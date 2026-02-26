import sys
sys.path.insert(0, r'C:\Users\chead\.openclaw\workspace\dashboard')

from auto_populate import run_all

print("Running auto_populate...")
results = run_all()

for source, result in results.items():
    print(f"\n{source}:")
    for key, val in result.items():
        print(f"  {key}: {val}")
