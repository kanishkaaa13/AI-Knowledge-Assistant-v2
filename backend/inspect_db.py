import sqlite3

conn = sqlite3.connect("ai_knowledge_assistant.db")
cur = conn.cursor()

# List all tables
cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = [r[0] for r in cur.fetchall()]
print("TABLES:", tables)

# Show users
cur.execute("SELECT id, name, email, hashed_password, created_at FROM users LIMIT 5")
rows = cur.fetchall()
print(f"\nUSER COUNT (up to 5): {len(rows)}")
for r in rows:
    print("  id          :", r[0])
    print("  name        :", r[1])
    print("  email       :", r[2])
    print("  hash_prefix :", r[3][:30] if r[3] else None)
    print("  created_at  :", r[4])
    print()

conn.close()
