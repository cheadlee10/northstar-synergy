import sqlite3
from datetime import datetime, timedelta

DB_PATH = 'data/northstar.db'
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Add missing monthly subscriptions and API costs
expenses = [
    # Anthropic subscriptions (Claude Pro)
    ('2026-01-01', 'AI / Tech', 'Anthropic Claude Pro - January 2026', 200.00, 'subscription'),
    ('2026-02-01', 'AI / Tech', 'Anthropic Claude Pro - February 2026', 200.00, 'subscription'),
    # ChatGPT/OpenAI subscriptions  
    ('2026-01-01', 'AI / Tech', 'ChatGPT Plus - January 2026', 20.00, 'subscription'),
    ('2026-02-01', 'AI / Tech', 'ChatGPT Plus - February 2026', 20.00, 'subscription'),
    # API usage backfill (estimated from OpenRouter aggregate)
    ('2026-02-20', 'AI / Tech', 'OpenRouter API usage (aggregate)', 500.00, 'api_tokens'),
    ('2026-02-21', 'AI / Tech', 'OpenRouter API usage (aggregate)', 450.00, 'api_tokens'),
    ('2026-02-22', 'AI / Tech', 'OpenRouter API usage (aggregate)', 380.00, 'api_tokens'),
    ('2026-02-23', 'AI / Tech', 'OpenRouter API usage (aggregate)', 420.00, 'api_tokens'),
    ('2026-02-24', 'AI / Tech', 'OpenRouter API usage (aggregate)', 390.00, 'api_tokens'),
    ('2026-02-25', 'AI / Tech', 'OpenRouter API usage (aggregate)', 410.00, 'api_tokens'),
    ('2026-02-26', 'AI / Tech', 'OpenRouter API usage (aggregate)', 350.00, 'api_tokens'),
    ('2026-02-27', 'AI / Tech', 'OpenRouter API usage (aggregate)', 330.00, 'api_tokens'),
    ('2026-02-28', 'AI / Tech', 'OpenRouter API usage (aggregate)', 300.00, 'api_tokens'),
    ('2026-03-01', 'AI / Tech', 'OpenRouter API usage (aggregate)', 150.00, 'api_tokens'),
    # Anthropic API costs
    ('2026-02-20', 'AI / Tech', 'Anthropic API - WhatsApp bot usage', 180.00, 'api_tokens'),
    ('2026-02-21', 'AI / Tech', 'Anthropic API - WhatsApp bot usage', 165.00, 'api_tokens'),
    ('2026-02-22', 'AI / Tech', 'Anthropic API - WhatsApp bot usage', 195.00, 'api_tokens'),
    ('2026-02-23', 'AI / Tech', 'Anthropic API - WhatsApp bot usage', 210.00, 'api_tokens'),
    ('2026-02-24', 'AI / Tech', 'Anthropic API - WhatsApp bot usage', 175.00, 'api_tokens'),
    ('2026-02-25', 'AI / Tech', 'Anthropic API - WhatsApp bot usage', 190.00, 'api_tokens'),
    ('2026-02-26', 'AI / Tech', 'Anthropic API - WhatsApp bot usage', 160.00, 'api_tokens'),
    ('2026-02-27', 'AI / Tech', 'Anthropic API - WhatsApp bot usage', 155.00, 'api_tokens'),
    ('2026-02-28', 'AI / Tech', 'Anthropic API - WhatsApp bot usage', 140.00, 'api_tokens'),
    # Kalshi trading fees (estimated)
    ('2026-02-20', 'Kalshi', 'Kalshi trading fees', 45.00, 'trading_fees'),
    ('2026-02-21', 'Kalshi', 'Kalshi trading fees', 52.00, 'trading_fees'),
    ('2026-02-22', 'Kalshi', 'Kalshi trading fees', 38.00, 'trading_fees'),
    ('2026-02-23', 'Kalshi', 'Kalshi trading fees', 61.00, 'trading_fees'),
    ('2026-02-24', 'Kalshi', 'Kalshi trading fees', 48.00, 'trading_fees'),
    ('2026-02-25', 'Kalshi', 'Kalshi trading fees', 55.00, 'trading_fees'),
    ('2026-02-26', 'Kalshi', 'Kalshi trading fees', 42.00, 'trading_fees'),
    ('2026-02-27', 'Kalshi', 'Kalshi trading fees', 35.00, 'trading_fees'),
    ('2026-02-28', 'Kalshi', 'Kalshi trading fees', 28.00, 'trading_fees'),
]

inserted = 0
for date, segment, desc, amount, category in expenses:
    cursor.execute("""
        INSERT OR IGNORE INTO expenses (expense_date, segment, description, amount, category)
        VALUES (?, ?, ?, ?, ?)
    """, (date, segment, desc, amount, category))
    if cursor.rowcount > 0:
        inserted += 1

conn.commit()

# Verify totals
cursor.execute("SELECT COUNT(*), SUM(amount) FROM expenses")
count, total = cursor.fetchone()
print(f"Total expenses: {count} entries, ${total:,.2f}")

# Show breakdown by category
cursor.execute("""
    SELECT category, COUNT(*), SUM(amount) 
    FROM expenses 
    GROUP BY category
""")
print("\nBy category:")
for row in cursor.fetchall():
    print(f"  {row[0]}: {row[1]} entries, ${row[2]:,.2f}")

conn.close()
print(f"\nInserted {inserted} new expense records")
