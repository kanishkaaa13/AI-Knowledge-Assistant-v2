import sqlite3, json
conn = sqlite3.connect('ai_knowledge_assistant.db')
cur = conn.cursor()

cur.execute('SELECT id, title, file_name, status, extracted_text IS NOT NULL as has_text, LENGTH(COALESCE(extracted_text, "")) as text_len FROM uploaded_documents LIMIT 10')
cols = [d[0] for d in cur.description]
rows = cur.fetchall()
print('Documents:')
for row in rows:
    print(dict(zip(cols, row)))

cur.execute('SELECT COUNT(*) FROM document_chunks')
print('\nTotal chunks in DB:', cur.fetchone()[0])
conn.close()
