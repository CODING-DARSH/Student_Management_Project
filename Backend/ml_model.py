# ml_model.py
import os
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
import joblib
import numpy as np
from db import execute_query

MODEL_PATH = os.path.join(os.getcwd(), 'models', 'risk_model.pkl')
os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)

PASS_THRESHOLD = 40.0  # percent / change as per your rules

def fetch_training_data():
    """
    Expect historical rows with final label (pass/fail).
    We'll compute: avg_marks (from StudentCourses.marks), avg_attendance (from Attendance).
    Label: pass if marks >= PASS_THRESHOLD else fail
    """
    students = execute_query("""
        SELECT s.id
        FROM Students s
    """, fetch=True)

    X = []
    y = []
    for (sid,) in students:
        # avg marks across courses (if stored in StudentCourses marks column)
        rows = execute_query("SELECT NVL(marks,0) FROM StudentCourses WHERE student_id=:1", (sid,), fetch=True)
        if not rows:
            continue
        marks = [float(r[0]) for r in rows]
        avg_marks = float(sum(marks))/len(marks) if marks else 0.0

        # attendance average across his courses (last 180 days)
        att = execute_query("""
            SELECT AVG(present)*100
            FROM Attendance a
            JOIN StudentCourses sc ON a.student_id=sc.student_id AND a.course_id=sc.course_id
            WHERE a.student_id=:1 AND a.date_marked >= (SYSDATE - 180)
        """, (sid,), fetch=True)
        avg_attendance = float(att[0][0] or 0.0)

        # label: pass if avg_marks >= PASS_THRESHOLD (change logic as required)
        label = 1 if avg_marks >= PASS_THRESHOLD else 0  # 1 = pass
        X.append([avg_marks, avg_attendance])
        y.append(label)
    return np.array(X), np.array(y)

def train_and_save_model():
    X, y = fetch_training_data()
    if X.shape[0] < 10:
        print("Not enough training rows (need >=10). Model not trained.")
        return None
    pipeline = Pipeline([
        ('scaler', StandardScaler()),
        ('clf', LogisticRegression(max_iter=1000))
    ])
    pipeline.fit(X, y)
    joblib.dump(pipeline, MODEL_PATH)
    print("✅ Model trained & saved to", MODEL_PATH)
    return pipeline

def load_model():
    if os.path.exists(MODEL_PATH):
        return joblib.load(MODEL_PATH)
    return None

def predict_student_risk(student_id, model=None):
    """
    Returns probability of FAIL (risk). We'll use model to get pass probability; risk = 1 - pass_prob.
    """
    if model is None:
        model = load_model()
    if model is None:
        return None

    # compute features
    rows = execute_query("SELECT NVL(marks,0) FROM StudentCourses WHERE student_id=:1", (student_id,), fetch=True)
    if not rows:
        avg_marks = 0.0
    else:
        marks = [float(r[0]) for r in rows]
        avg_marks = float(sum(marks))/len(marks) if marks else 0.0

    att = execute_query("""
        SELECT AVG(present)*100
        FROM Attendance a
        WHERE a.student_id=:1 AND a.date_marked >= (SYSDATE - 180)
    """, (student_id,), fetch=True)
    avg_attendance = float(att[0][0] or 0.0)

    X = [[avg_marks, avg_attendance]]
    pass_prob = model.predict_proba(X)[0][1]  # index 1 is probability of pass (label=1)
    risk_score = 1 - pass_prob
    label = 'low'
    if risk_score >= 0.75:
        label = 'high'
    elif risk_score >= 0.5:
        label = 'medium'
    return {'student_id': student_id, 'risk_score': risk_score, 'risk_label': label, 'avg_marks': avg_marks, 'avg_attendance': avg_attendance}

def predict_all_students(threshold=0.6):
    model = load_model()
    if model is None:
        m = train_and_save_model()
        if m is None:
            return []
        model = m

    students = execute_query("SELECT id FROM Students", fetch=True)
    results = []
    for (sid,) in students:
        r = predict_student_risk(sid, model)
        if r is None:
            continue
        # store into StudentRisk table
        next_id = execute_query("SELECT NVL(MAX(id),0)+1 FROM StudentRisk", fetch=True)[0][0]
        execute_query("""
            INSERT INTO StudentRisk (id, student_id, risk_score, risk_label, evaluated_at)
            VALUES (:1, :2, :3, :4, SYSTIMESTAMP)
        """, (next_id, sid, float(r['risk_score']), r['risk_label']))
        results.append(r)
        # optionally send notifications if above threshold
        if r['risk_score'] >= threshold:
            Notification.create(sid, f"⚠️ Risk warning: Your projected risk score is {r['risk_score']:.2f} ({r['risk_label']}). Please contact your teacher.")
    return results
