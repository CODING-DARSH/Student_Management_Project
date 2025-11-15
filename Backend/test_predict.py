from ml_model import predict_all_students

res = predict_all_students(threshold=0.6, notify=False)
for r in res:
    print(r)
