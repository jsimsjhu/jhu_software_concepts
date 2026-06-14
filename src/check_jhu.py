import psycopg

conn = psycopg.connect(
    dbname="postgres",
    user="postgres",
    password="postgres",
    host="localhost"
)
cur = conn.cursor()

cur.execute("""
    SELECT program, llm_generated_university
    FROM applicants
    WHERE program ILIKE '%Johns Hopkins%' OR llm_generated_university ILIKE '%Johns Hopkins%'
    LIMIT 5;
""")

rows = cur.fetchall()
print("Found", len(rows), "rows")
for row in rows:
    print(row)

cur.close()
conn.close()