import json
from datetime import datetime

with open(r"C:\Users\chead\AppData\Roaming\Granola\cache-v3.json", "r", encoding="utf-8") as f:
    outer = json.load(f)

inner = json.loads(outer["cache"])
state = inner.get("state", {})
print("State type:", type(state).__name__, flush=True)
if isinstance(state, dict):
    print("State keys:", list(state.keys())[:20], flush=True)
    # Look for documents/notes/meetings
    for key in state.keys():
        val = state[key]
        if isinstance(val, list) and len(val) > 0:
            print(f"  {key}: list of {len(val)}, first item type: {type(val[0]).__name__}", flush=True)
            if isinstance(val[0], dict):
                print(f"    First item keys: {list(val[0].keys())[:10]}", flush=True)
        elif isinstance(val, dict):
            print(f"  {key}: dict with {len(val)} keys: {list(val.keys())[:5]}", flush=True)
        else:
            print(f"  {key}: {type(val).__name__} = {str(val)[:100]}", flush=True)
