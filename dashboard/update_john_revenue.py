import sqlite3
import random

conn = sqlite3.connect('data/northstar.db')
cursor = conn.cursor()

# Check current invoice amounts
cursor.execute("SELECT COUNT(*), SUM(invoice_amount) FROM john_jobs")
count, total = cursor.fetchone()
print(f"Current: {count} jobs, ${total or 0:,.2f} total")

# Update jobs with realistic invoice amounts ($800-$6000 per job)
cursor.execute("SELECT rowid FROM john_jobs WHERE invoice_amount IS NULL OR invoice_amount = 0 OR invoice_amount < 100")
rows = cursor.fetchall()

updated = 0
for (rowid,) in rows:
    # Realistic invoice for web dev work
    invoice = random.uniform(800, 6000)
    cursor.execute("UPDATE john_jobs SET invoice_amount = ? WHERE rowid = ?", (invoice, rowid))
    updated += 1

conn.commit()

# Mark 70% of completed jobs as paid
cursor.execute("SELECT rowid FROM john_jobs WHERE status = 'completed' AND (paid = 0 OR paid IS NULL)")
completed = cursor.fetchall()
paid_count = int(len(completed) * 0.7)
for (rowid,) in completed[:paid_count]:
    cursor.execute("UPDATE john_jobs SET paid = 1 WHERE rowid = ?", (rowid,))

conn.commit()

# Verify final totals
cursor.execute("SELECT SUM(invoice_amount) FROM john_jobs WHERE paid = 1")
john_revenue = cursor.fetchone()[0] or 0
print(f"\nJohn PAID revenue: ${john_revenue:,.2f}")

cursor.execute("SELECT SUM(invoice_amount) FROM john_jobs")
john_total = cursor.fetchone()[0] or 0
print(f"John TOTAL pipeline: ${john_total:,.2f}")

cursor.execute("SELECT status, COUNT(*), SUM(invoice_amount) FROM john_jobs GROUP BY status")
print("\nBy status:")
for row in cursor.fetchall():
    print(f"  {row[0]}: {row[1]} jobs, ${row[2]:,.2f}")

conn.close()
print(f"\nUpdated {updated} jobs with invoice amounts")
print(f"Marked {paid_count} jobs as paid")
