import time
from ml_model import train_and_save_model

print("⏱ Starting training...\n")

start = time.time()
train_and_save_model()
end = time.time()

print(f"\n⏳ Training completed in {end - start:.4f} seconds\n")
