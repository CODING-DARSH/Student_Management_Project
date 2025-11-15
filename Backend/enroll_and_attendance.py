import random
from datetime import datetime, timedelta
from db import execute_query

NUM_SUBJECTS = 6

def enroll_all_students():
    students = execute_query("SELECT id FROM Students", fetch=True)
    courses = execute_query("SELECT id FROM Courses ORDER BY id", fetch=True)

    if len(courses) < NUM_SUBJECTS:
        print("❌ ERROR: Need 6 subjects in Courses table.")
        return

    course_ids = [c[0] for c in courses]

    for (sid,) in students:
        for cid in course_ids:
            marks = random.uniform(20, 95)
            execute_query(
                "INSERT INTO StudentCourses (student_id, course_id, marks) VALUES (%s,%s,%s)",
                (sid, cid, marks)
            )
    print("✔ Students enrolled in all 6 subjects with marks.")


def generate_attendance():
    students = execute_query("SELECT id FROM Students", fetch=True)
    courses = execute_query("SELECT id FROM Courses ORDER BY id", fetch=True)
    course_ids = [c[0] for c in courses]

    today = datetime.now().date()

    for (sid,) in students:
        for day_offset in range(90):  # last 90 days
            date_val = today - timedelta(days=day_offset)
            for cid in course_ids:
                present = 1 if random.random() < 0.85 else 0

                execute_query(
                    "INSERT INTO Attendance (student_id, course_id, date_marked, present, created_at) "
                    "VALUES (%s,%s,%s,%s,NOW())",
                    (sid, cid, date_val, present)
                )
    print("✔ Attendance inserted for last 90 days.")


if __name__ == "__main__":
    enroll_all_students()
    generate_attendance()
