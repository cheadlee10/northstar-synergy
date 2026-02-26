import json
from datetime import datetime

with open(r"C:\Users\chead\AppData\Roaming\Granola\cache-v3.json", "r", encoding="utf-8") as f:
    outer = json.load(f)

inner = json.loads(outer["cache"])
docs = inner["state"]["documents"]

# Sort by updated_at, find most recent and any RBS-related
results = []
for doc_id, doc in docs.items():
    title = doc.get("title", "") or ""
    created = doc.get("created_at", "") or ""
    updated = doc.get("updated_at", "") or ""
    notes_md = doc.get("notes_markdown", "") or ""
    notes_plain = doc.get("notes_plain", "") or ""
    results.append({
        "id": doc_id,
        "title": title,
        "created": created,
        "updated": updated,
        "notes_md": notes_md,
        "notes_plain": notes_plain
    })

# Sort by updated desc
results.sort(key=lambda x: x["updated"], reverse=True)

# Print top 10 most recent
print("=== TOP 10 MOST RECENT DOCS ===", flush=True)
for r in results[:10]:
    print(f"Title: {r['title']} | Updated: {r['updated']}", flush=True)

# Print any with RBS in title or notes
print("\n=== RBS DOCS ===", flush=True)
rbs_docs = [r for r in results if "rbs" in r["title"].lower() or "rbs" in r["notes_md"].lower() or "rbs" in r["notes_plain"].lower()]
for r in rbs_docs[:5]:
    print(f"\n--- {r['title']} (Updated: {r['updated']}) ---", flush=True)
    notes = r["notes_md"] if r["notes_md"] else r["notes_plain"]
    print(notes[:3000], flush=True)
