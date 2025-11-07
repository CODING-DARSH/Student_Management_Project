from datetime import datetime, timedelta
import random
import smtplib
from email.mime.text import MIMEText
import os
from dotenv import load_dotenv
from twilio.rest import Client
from db import execute_query

# Load environment variables
load_dotenv()

# ---------------- OTP / EMAIL / SMS UTILITIES ----------------
def send_email_otp(email, otp):
    """Send OTP via Gmail (uses env vars EMAIL_ADDR and EMAIL_APP_PASSWORD)."""
    sender = os.getenv("EMAIL_ADDR") or "yourapp@gmail.com"
    app_password = os.getenv("EMAIL_APP_PASSWORD")

    msg = MIMEText(f"Your Student Portal OTP is: {otp}")
    msg["Subject"] = "Student Portal Login OTP"
    msg["From"] = sender
    msg["To"] = email

    if not app_password:
        print(f"📧 [DEV MODE] OTP for {email}: {otp}")
        return

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender, app_password)
            server.send_message(msg)
        print(f"✅ OTP sent to email: {email}")
    except Exception as e:
        print(f"❌ Email send error: {e}")


def send_sms_otp(phone, otp):
    """Send OTP via Twilio (prints in dev mode if Twilio not configured)."""
    sid = os.getenv("TWILIO_SID")
    token = os.getenv("TWILIO_AUTH_TOKEN")
    from_number = os.getenv("TWILIO_PHONE_NUMBER")

    if not (sid and token and from_number):
        print(f"📱 [DEV MODE] OTP to {phone}: {otp}")
        return

    try:
        client = Client(sid, token)
        client.messages.create(
            body=f"Your Student Portal OTP is {otp}",
            from_=from_number,
            to=f"+91{phone}" if not phone.startswith("+") else phone,
        )
        print(f"✅ OTP sent to phone: {phone}")
    except Exception as e:
        print(f"❌ SMS send error: {e}")


# ---------------- STUDENT MODEL ----------------
class Student:
    @staticmethod
    def register(name, email, phone, password):
        next_id = execute_query("SELECT NVL(MAX(id), 0)+1 FROM Students", fetch=True)[0][0]
        execute_query(
            "INSERT INTO Students (id, name, email, phone, password) VALUES (:1,:2,:3,:4,:5)",
            (next_id, name, email, phone, password),
        )
        print(f"✅ Student registered with ID: {next_id}")
        return next_id

    @staticmethod
    def login(student_id, password):
        q = "SELECT id, name FROM Students WHERE id=:1 AND password=:2"
        data = execute_query(q, (student_id, password), fetch=True)
        return data[0] if data else None

    @staticmethod
    def change_password(student_id, old_password, new_password):
        q = "SELECT password FROM Students WHERE id=:1"
        data = execute_query(q, (student_id,), fetch=True)
        if data and data[0][0] == old_password:
            execute_query("UPDATE Students SET password=:1 WHERE id=:2", (new_password, student_id))
            return True
        return False

    @staticmethod
    def get_details(student_id):
        q = "SELECT id, name, grades FROM Students WHERE id=:1"
        data = execute_query(q, (student_id,), fetch=True)
        return data[0] if data else None

    @staticmethod
    def enroll(student_id, course_id):
        execute_query("INSERT INTO StudentCourses (student_id, course_id) VALUES (:1,:2)", (student_id, course_id))

    @staticmethod
    def show_courses(student_id):
        q = """
        SELECT c.course_name
        FROM Courses c
        JOIN StudentCourses sc ON c.id = sc.course_id
        WHERE sc.student_id = :1
        """
        data = execute_query(q, (student_id,), fetch=True)
        return [row[0] for row in data]

    @staticmethod
    def get_course_grades(student_id):
        q = """
        SELECT c.course_name, sc.marks
        FROM Courses c
        JOIN StudentCourses sc ON c.id = sc.course_id
        WHERE sc.student_id = :1
        """
        data = execute_query(q, (student_id,), fetch=True)
        return [(row[0], row[1] or 0) for row in data]

    @staticmethod
    def export_csv(student_id):
        data = Student.get_course_grades(student_id)
        filename = f"student_{student_id}_report.csv"
        with open(filename, "w", encoding="utf-8") as f:
            f.write("Course,Marks\n")
            for d in data:
                f.write(f"{d[0]},{d[1]}\n")
        print(f"📁 Exported report: {filename}")

    @staticmethod
    def get_notifications(student_id):
        q = """
        SELECT message, TO_CHAR(created_at,'YYYY-MM-DD HH24:MI')
        FROM Notifications
        WHERE student_id=:1
        ORDER BY created_at DESC
        """
        return execute_query(q, (student_id,), fetch=True)

class TeacherNotification:
    @staticmethod
    def create(teacher_id, message):
        q = "INSERT INTO TeacherNotifications (id, teacher_id, message) VALUES (teacher_notif_seq.NEXTVAL, :1, :2)"
        execute_query(q, (teacher_id, message))

# ---------------- NOTIFICATION MODEL ----------------
class Notification:
    @staticmethod
    def create(student_id, message):
        """Create a new notification for a student."""
        q = """
        INSERT INTO Notifications (id, student_id, message, created_at)
        VALUES (notif_seq.NEXTVAL, :1, :2, SYSTIMESTAMP)
        """
        execute_query(q, (student_id, message))
        print(f"🔔 Notification sent to Student {student_id}: {message}")

    @staticmethod
    def get_for_student(student_id):
        q = """
        SELECT message, TO_CHAR(created_at,'YYYY-MM-DD HH24:MI')
        FROM Notifications
        WHERE student_id=:1
        ORDER BY created_at DESC
        """
        return execute_query(q, (student_id,), fetch=True)


# ---------------- TEACHER MODEL ----------------
class Teacher:
    @staticmethod
    def register(name, password):
        next_id = execute_query("SELECT NVL(MAX(id), 0)+1 FROM Teachers", fetch=True)[0][0]
        execute_query("INSERT INTO Teachers (id, name, password) VALUES (:1,:2,:3)", (next_id, name, password))
        print(f"✅ Teacher registered with ID: {next_id}")
        return next_id
    @staticmethod
    def get_courses(teacher_id):
        """
        Return list of (course_id, course_name) for courses this teacher is assigned to.
        """
        q = """SELECT c.id, c.course_name
               FROM Courses c
               JOIN TeacherCourses tc ON c.id = tc.course_id
               WHERE tc.teacher_id = :1"""
        return execute_query(q, (teacher_id,), fetch=True)

    @staticmethod
    def login(teacher_id, password):
        q = "SELECT id, name FROM Teachers WHERE id=:1 AND password=:2"
        data = execute_query(q, (teacher_id, password), fetch=True)
        return data[0] if data else None

    @staticmethod
    def grade_submission(submission_id, marks):
        """Grade a submission, update averages, and notify student."""
        execute_query("UPDATE Submissions SET marks=:1 WHERE id=:2", (marks, submission_id))
        data = execute_query("""
            SELECT s.student_id, a.course_id
            FROM Submissions s
            JOIN Assignments a ON s.assignment_id=a.id
            WHERE s.id=:1
        """, (submission_id,), fetch=True)
        if not data:
            print("❌ No related student/course found.")
            return

        student_id, course_id = data[0]

        # Update average marks in StudentCourses
        execute_query("""
            UPDATE StudentCourses
            SET marks = (
                SELECT ROUND(AVG(s.marks), 2)
                FROM Submissions s
                JOIN Assignments a ON s.assignment_id=a.id
                WHERE s.student_id=:1 AND a.course_id=:2 AND s.marks IS NOT NULL
            )
            WHERE student_id=:1 AND course_id=:2
        """, (student_id, course_id))

        Notification.create(student_id, f"✅ Your submission for Course {course_id} has been graded. Marks: {marks}")

    @staticmethod
    def assign_to_course(teacher_id, course_id):
        next_id = execute_query("SELECT NVL(MAX(id),0)+1 FROM TeacherCourses", fetch=True)[0][0]
        execute_query("INSERT INTO TeacherCourses (id, teacher_id, course_id) VALUES (:1,:2,:3)",
                      (next_id, teacher_id, course_id))


# ---------------- ADMIN MODEL ----------------
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


# ---------------- OTP MODEL ----------------
class OTP:
    @staticmethod
    def generate_otp(student_id):
        otp = str(random.randint(100000, 999999))
        expires_at = datetime.now() + timedelta(minutes=5)
        next_id = execute_query("SELECT NVL(MAX(id), 0)+1 FROM OTP_CODES", fetch=True)[0][0]
        execute_query(
            "INSERT INTO OTP_CODES (id, student_id, otp_code, expires_at) VALUES (:1,:2,:3,:4)",
            (next_id, student_id, otp, expires_at),
        )
        print(f"✅ OTP {otp} created for Student {student_id}")
        return otp

    @staticmethod
    def verify_otp(student_id, otp_code):
        q = "SELECT otp_code, expires_at FROM OTP_CODES WHERE student_id=:1 ORDER BY expires_at DESC"
        data = execute_query(q, (student_id,), fetch=True)
        if not data:
            return False
        otp, expiry = data[0]
        return otp == otp_code and datetime.now() < expiry


# ---------------- ASSIGNMENTS MODEL ----------------
class Assignment:
    @staticmethod
    def create(course_id, teacher_id, title, description, due_date):
        next_id = execute_query("SELECT NVL(MAX(id), 0)+1 FROM Assignments", fetch=True)[0][0]
        execute_query("""
            INSERT INTO Assignments (id, course_id, teacher_id, title, description, due_date)
            VALUES (:1,:2,:3,:4,:5,:6)
        """, (next_id, course_id, teacher_id, title, description, due_date))

        # Notify all students in this course
        students = execute_query("SELECT student_id FROM StudentCourses WHERE course_id=:1", (course_id,), fetch=True)
        for sid, in students:
            Notification.create(sid, f"🆕 New assignment posted: {title} (Due: {due_date})")

        print(f"✅ Assignment {next_id} created for Course {course_id}")
        return next_id

    @staticmethod
    def get_for_teacher(teacher_id):
        q = "SELECT id, title, description, due_date FROM Assignments WHERE teacher_id=:1"
        return execute_query(q, (teacher_id,), fetch=True)


# ---------------- SUBMISSIONS MODEL ----------------
class Submission:
    @staticmethod
    def submit(assignment_id, student_id, file_path):
        next_id = execute_query("SELECT NVL(MAX(id), 0)+1 FROM Submissions", fetch=True)[0][0]
        execute_query("""
            INSERT INTO Submissions (id, assignment_id, student_id, file_path)
            VALUES (:1,:2,:3,:4)
        """, (next_id, assignment_id, student_id, file_path))
        Notification.create(student_id, f"📤 Assignment {assignment_id} submitted successfully.")
        print(f"✅ Submission {next_id} saved for Student {student_id}")
        return next_id

    @staticmethod
    def get_for_student(student_id):
        q = """
        SELECT s.id, a.id, a.title, s.file_path, s.submitted_at, s.marks
        FROM Submissions s
        JOIN Assignments a ON s.assignment_id = a.id
        WHERE s.student_id = :1
        """
        return execute_query(q, (student_id,), fetch=True)
