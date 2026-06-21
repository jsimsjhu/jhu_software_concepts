import json
import psycopg
from psycopg.extras import execute_values

DB_NAME = "postgres"
DB_USER = "postgres"
DB_PASSWORD = "postgres"
DB_HOST = "localhost"

def create_table(conn):
    sql = """
    DROP TABLE IF EXISTS applicants;
    CREATE TABLE applicants (
        p_id SERIAL PRIMARY KEY,
        program TEXT,
        comments TEXT,
        date_added DATE,
        url TEXT,
        status TEXT,
        term TEXT,
        us_or_international TEXT,
        GPA FLOAT,
        gre FLOAT,
        gre_v FLOAT,
        gre_aw FLOAT,
        degree TEXT,
        llm_generated_program TEXT,
        llm_generated_university TEXT
    );
    """
    with conn.cursor() as cur:
        cur.execute(sql)
    conn.commit()

with open(data_file, 'r', encoding='utf-8-sig') as f:
    data = json.load(f)
with open(llm_file, 'r', encoding='utf-8-sig') as f:
    llm_data = json.load(f)
    
    # Build a lookup from result_id to llm fields
    llm_lookup = {}
    for entry in llm_data.get('results', []):
        rid = entry.get('result_id')
        if rid:
            llm_lookup[rid] = entry
    
    # Prepare rows for insertion
    rows = []
    for entry in data.get('results', []):
        rid = entry.get('result_id')
        llm = llm_lookup.get(rid, {})
        rows.append((
            entry.get('program'),
            entry.get('comments'),
            entry.get('added_on'),
            entry.get('result_url'),
            entry.get('acceptance_status'),
            entry.get('term'),
            entry.get('applicant_type'),
            entry.get('gpa'),
            entry.get('gre_quant'),
            entry.get('gre_verbal'),
            entry.get('gre_aw'),
            entry.get('degree'),
            llm.get('llm_generated_program'),
            llm.get('llm_generated_university')
        ))
    
    # Insert using execute_values for efficiency
    insert_sql = """
    INSERT INTO applicants (
        program, comments, date_added, url, status, term,
        us_or_international, gpa, gre, gre_v, gre_aw, degree,
        llm_generated_program, llm_generated_university
    ) VALUES %s
    """
    with conn.cursor() as cur:
        execute_values(cur, insert_sql, rows)
    conn.commit()
    print(f"Inserted {len(rows)} rows.")

if __name__ == "__main__":
    conn = psycopg.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST
    )
    create_table(conn)
    load_data(conn, "applicant_data.json", "llm_extend_applicant_data.json")
    conn.close()