# pylint: disable=missing-final-newline, trailing-newlines
"""Load GradCafe data into PostgreSQL."""
# pylint: disable=no-member

import json
import psycopg

from db_helpers import (
    INSERT_APPLICANT_SQL,
    build_applicant_row,
    DB_NAME,
    DB_USER,
    DB_PASSWORD,
    DB_HOST,
)


def create_table(db_conn):
    """Create the applicants table if it does not exist."""
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
    with db_conn.cursor() as cur:
        cur.execute(sql)
    db_conn.commit()


def load_data(db_conn, data_file, llm_file):
    """Load data from JSON files into the database."""
    # Load both JSON files
    with open(data_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    with open(llm_file, "r", encoding="utf-8") as f:
        llm_data = json.load(f)

    # Build a lookup from result_id to llm fields
    llm_lookup = {}
    for entry in llm_data.get("results", []):
        rid = entry.get("result_id")
        if rid:
            llm_lookup[rid] = entry

    # Prepare rows for insertion using shared helper
    rows = [build_applicant_row(entry, llm_lookup) for entry in data.get("results", [])]

    # Insert using executemany for efficiency
    with db_conn.cursor() as cur:
        cur.executemany(INSERT_APPLICANT_SQL, rows)
    db_conn.commit()
    print(f"Inserted {len(rows)} rows.")


if __name__ == "__main__":  # pragma: no cover
    conn = psycopg.connect(
        dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST
    )
    create_table(conn)
    load_data(conn, "applicant_data.json", "llm_extend_applicant_data.json")
    conn.close()
