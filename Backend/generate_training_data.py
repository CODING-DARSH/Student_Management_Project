# insert_attendance_sample.py
import random
from datetime import datetime, timedelta
from db import execute_query

student_ids = [1,2,3,4,5]  # real ones
course_ids = [1,2,3,4,5,6]
today = datetime.now().date()
DAYS = 90

for sid in student_ids:
    for d in range(DAYS):
        date_val = today - timedelta(days=d)
        for cid in course_ids:
            # tune presence: make student 1 low attendance, 2 high, etc
            if sid == 1:
                present = 1 if random.random() < 0.3 else 0
            elif sid == 2:
                present = 1 if random.random() < 0.95 else 0
            elif sid == 3:
                present = 1 if random.random() < 0.7 else 0
            elif sid == 4:
                present = 1 if random.random() < 0.2 else 0
            else:
                present = 1 if random.random() < 0.85 else 0
            execute_query(
                "INSERT INTO Attendance (student_id, course_id, date_marked, present, created_at) VALUES (%s,%s,%s,%s,NOW())",
                (sid, cid, date_val, present)
            )
print("Inserted attendance for students", student_ids)
