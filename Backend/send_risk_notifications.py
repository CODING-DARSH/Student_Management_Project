from ml_model import predict_all_students

print("🚀 Sending risk notifications...")

results = predict_all_students(threshold=0.6, notify=True)

print("✅ Done.")
