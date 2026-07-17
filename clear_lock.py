import os
import glob

app_dir = os.path.dirname(os.path.abspath(__file__))

# Common lock file locations
patterns = [
    os.path.join(app_dir, "*.lock"),
    os.path.join(app_dir, "tmp", "*.lock"),
    os.path.join(app_dir, "tmp", "restart.txt"),
]

for pattern in patterns:
    for f in glob.glob(pattern):
        try:
            os.remove(f)
            print(f"Removed: {f}")
        except Exception as e:
            print(f"Could not remove {f}: {e}")

print("Done.")
