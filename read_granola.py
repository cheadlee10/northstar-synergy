import json
import sys
from datetime import datetime

with open(r"C:\Users\chead\AppData\Roaming\Granola\cache-v3.json", "r", encoding="utf-8") as f:
    outer = json.load(f)

# Cache is a stringified JSON
inner = json.loads(outer["cache"])
print("Inner type:", type(inner).__name__, flush=True)
if isinstance(inner, dict):
    print("Inner keys:", list(inner.keys())[:15], flush=True)
elif isinstance(inner, list):
    print("Inner list length:", len(inner), flush=True)
    if inner:
        print("First item keys:", list(inner[0].keys()), flush=True)
