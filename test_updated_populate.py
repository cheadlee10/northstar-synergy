import sys
sys.path.insert(0, r'C:\Users\chead\.openclaw\workspace\dashboard')

from auto_populate import run_all

print("Testing updated auto_populate with LIVE Kalshi API...\n")
results = run_all()

for source, result in results.items():
    print(f"{source}:")
    for key, val in result.items():
        print(f"  {key}: {val}")
    print()
