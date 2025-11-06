from db import execute_query

class Student:
    @staticmethod
    def register(name, password):
        q = "INSERT INTO Students (name, password) VALUES (:1, :2)"
        execute_query(q, (name, password))

    @staticmethod
    def login(student_id, password):
        q = "SELECT id, name FROM Students WHERE id=:1 AND password=:2"
        data = execute_query(q, (student_id, password), fetch=True)
        return data[0] if data else None

    @staticmethod
    def enroll(student_id, course_id):
        q = "INSERT INTO StudentCourses (student_id, course_id) VALUES (:1, :2)"
        execute_query(q, (student_id, course_id))

    @staticmethod
    def show_courses(student_id):
        q = """SELECT c.course_name
               FROM Courses c JOIN StudentCourses sc
               ON c.id = sc.course_id
               WHERE sc.student_id=:1"""
        return [row[0] for row in execute_query(q, (student_id,), fetch=True)]

class Teacher:
    @staticmethod
    def register(name, password):
        execute_query("INSERT INTO Teachers (name, password) VALUES (:1, :2)", (name, password))

    @staticmethod
    def assign_grade(student_id, grade):
        execute_query("UPDATE Students SET grades=:1 WHERE id=:2", (grade, student_id))

class Admin:
    @staticmethod
    def login(username, password):
        q = "SELECT username FROM Admins WHERE username=:1 AND password=:2"
        data = execute_query(q, (username, password), fetch=True)
        return bool(data)

    @staticmethod
    def show_all_students():
        q = "SELECT id, name, grades FROM Students"
        return execute_query(q, fetch=True)
