# -*- coding: utf-8 -*-
import tornado.ioloop
import tornado.web
import dbconn
import web
import os
dbconn.register_dsn("host=localhost dbname=examdb user=examdbo password=pass")

settings = {
    "static_path": os.path.join('.', 'pages'),
    "debug": True
}


class BaseReqHandler(tornado.web.RequestHandler):

    def db_cursor(self, autocommit=True):
        return dbconn.SimpleDataCursor(autocommit=autocommit)
    
class MainHandler(BaseReqHandler):
    def get(self):
        self.set_header("Content-Type", "text/html; charset=UTF-8")
        self.render(r"pages\base.html", title="首页")

class ScheduleHandler(BaseReqHandler):
    #显示排课信息
    def get(self):
        with self.db_cursor() as cur:
            sql = '''
                  select week,time,cno,cname,classroom,tname,tno,object
                  from tc_schedule
                  ORDER BY week,time
                  '''
            cur.execute(sql)
            cur.commit()
            items = cur.fetchall()
        self.set_header("Content-Type", "text/html; charset=UTF-8")
        self.render("pages\list.html", title="排课信息", items=items)


class CourseAddHandler(BaseReqHandler):
    #添加排课信息
    def post(self):
        week = int(self.get_argument("week"))
        time= int(self.get_argument("time"))
        cno = self.get_argument("cno")
        cname = self.get_argument("cname")
        classroom = self.get_argument("classroom")
        tname = self.get_argument("tname")
        tno = self.get_argument("tno")
        _cls = self.get_argument("class")
        
        with self.db_cursor() as cur:
            sql_1 = '''select cname,cno
                        from course
            '''
            cur.execute(sql_1)
            cur.commit()
            course=[]
            for item in cur.fetchall():
                course.append(item)
            for item in course:
                if item[0]==cname and item[1]==cno:
                    sql_2 = '''insert into tc_schedule
                             (week,time,cno,cname,classroom,tname,tno,object)
                             values
                               (%s,%s,%s,%s,%s,%s,%s,%s)'''
                    try:
                        cur.execute(sql_2, (week,time,cno,cname,classroom,tname,tno,_cls))
                        cur.commit()
                        break
                    except :
                        cur.rollback()
                    finally:
                        self.set_header("Content-Type", "text/html; charset=UTF-8") 
                        self.redirect("/schedule")



class CourseDelHandler(BaseReqHandler):
    #删除排课信息
    def get(self, week,time,tno):
        week = int(week)
        time = int(time)
        
        with self.db_cursor() as cur:
            sql_1 = '''delete from tc_schedule
                       where week=%s and time=%s and tno=%s 
            '''
            cur.execute(sql_1, (week,time,tno))
            cur.commit()
            sql_2='''update t_chart set 
                     cname=null,classroom=null
                     where  week=%s and time=%s
            '''
            cur.execute(sql_2, (week,time))
            cur.commit()
        self.set_header("Content-Type", "text/html; charset=UTF-8")
        self.redirect("/schedule")

class CourseEditHandler(BaseReqHandler):
   #修改排课信息
    def get(self,week,time,tno):
        week = int(week)
        time = int(time)

        self.set_header("Content-Type", "text/html; charset=UTF-8")
        with self.db_cursor() as cur:
            sql = '''
                select week,time,cno,cname,classroom,tname,tno,object
                from tc_schedule
                WHERE week=%s and time=%s and tno=%s;
            '''
            cur.execute(sql,(week,time,tno))
            cur.commit()
            row = cur.fetchone()
            if row:
                self.render("pages\edit.html", week=week,time=time,
                 cno=row[2],cname=row[3],classroom=row[4],tname=row[5],
                    tno=row[6],object=row[7])
            else:
                self.write('Not FOUND!')
    
    def post(self,week,time,tno):
        week = int(week)
        time = int(time)
        cno = self.get_argument("cno")
        cname = self.get_argument("cname")
        classroom = self.get_argument("classroom")
        tname = self.get_argument("tname")
        _cls = self.get_argument("class")
        self.set_header("Content-Type", "text/html; charset=UTF-8")
        with self.db_cursor() as cur:
            
            sql_2 = '''update tc_schedule set 
                      cno=%s,cname=%s,
                      classroom=%s,tname=%s,object=%s
                      where week=%s and time=%s and tno=%s
                      
                '''
            cur.execute(sql_2, (cno,cname,classroom,tname,_cls,week,time,tno))
            cur.commit()
        self.redirect("/schedule")
        
class StudentCourseHandler(BaseReqHandler):
    #学生课程表
    def post(self):
        _cls = self.get_argument("_cls")
        with self.db_cursor() as cur:
            cur.execute('''update s_chart  as a set
                           cname= b.cname,classroom=b.classroom
                           from tc_schedule as b
                           where a.week= b.week and a.time= b.time and b.object=%s
            ''',(_cls,))
            cur.commit()
        self.redirect("/student_course")
                
        
    def get(self):
        course=[]
        with self.db_cursor() as cur:
             for i in range(1,5):
                 cur.execute('''SELECT cname,classroom
                               from s_chart
                               WHERE time=%s 
                               ORDER BY week''',(i,))
                 cur.commit()
                 course.append(list(cur.fetchall()))
        self.render("pages\s_chart.html", first=course[0],second=course[1],
                    third=course[2],fourth=course[3])


class TeacherCourseHandler(BaseReqHandler):
   #教师课程表
    def post(self):
        teacher = self.get_argument("teacher")
        with self.db_cursor() as cur:
            cur.execute('''update t_chart  as a set
                           cname= b.cname,classroom= b.classroom
                           from tc_schedule as b
                           where a.week= b.week and a.time=b.time and b.tname=%s
            ''',(teacher,))
            cur.commit()
        self.redirect("/teacher_course")
    def get(self):
        course=[]
        with self.db_cursor() as cur:
            
            for i in range(1,5):
                cur.execute('''SELECT cname,classroom
                               from t_chart
                               WHERE time=%s 
                               ORDER BY week''',(i,))
                cur.commit()
                course.append(list(cur.fetchall()))
        self.render(r"pages\t_chart.html", first=course[0],second=course[1],
                    third=course[2],fourth=course[3])

class TCourseClearHandler(BaseReqHandler):
    #清空教师课程表
    def get(self):
        with self.db_cursor() as cur:
            cur.execute("""update  t_chart set
                           cname=null,classroom=null
            """)
            cur.commit()
        self.redirect("/teacher_course")

class SCourseClearHandler(BaseReqHandler):
    #清空学生课程表
    def get(self):
        with self.db_cursor() as cur:
            cur.execute("""update  s_chart set
                           cname=null,classroom=null
            """)
            cur.commit()
        self.redirect("/student_course")


application= tornado.web.Application([
    (r"/", MainHandler),
    (r"/schedule", ScheduleHandler),
    (r"/course.add",CourseAddHandler),
    (r"/course.del/([0-9]+)/([0-9]+)/([0-9]+)",CourseDelHandler),
    (r"/course.edit/([0-9]+)/([0-9]+)/([0-9]+)",CourseEditHandler),
    (r"/student_course", StudentCourseHandler),
    (r"/teacher_course", TeacherCourseHandler),
    (r"/tcourse.clear", TCourseClearHandler),
    (r"/scourse.clear", SCourseClearHandler),
    (r'/(.*)', web.HtplHandler)
], **settings)


if __name__ == "__main__":
    application.listen(8888)
    server = tornado.ioloop.IOLoop.instance()
    tornado.ioloop.PeriodicCallback(lambda: None, 500, server).start()
    server.start()
