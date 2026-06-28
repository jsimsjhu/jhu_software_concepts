"""Load GradCafe data into PostgreSQL using environment variables."""

import json
import os
import psycopg

# Use environment variables
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://app_user:app_password@db:5432/postgres")

INSERT_APPLICANT_SQL = """
    INSERT INTO applicants (
        program, comments, date_added, url, status, term,
        us_or_international, gpa, gre, gre_v, gre_aw, degree,
        llm_generated_program, llm_generated_university
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
"""

def build_applicant_row(entry, llm_lookup):
    """Build a tuple for insertion from a data entry and LLM lookup dict."""
    rid = entry.get("result_id")
    llm = llm_lookup.get(rid, {})
    return (
        entry.get("program"),
        entry.get("comments"),
        entry.get("added_on"),
        entry.get("result_url"),
        entry.get("acceptance_status"),
        entry.get("term"),
        entry.get("applicant_type"),
        entry.get("gpa"),
        entry.get("gre_quant"),
        entry.get("gre_verbal"),
        entry.get("gre_aw"),
        entry.get("degree"),
        llm.get("llm_generated_program"),
        llm.get("llm_generated_university"),
    )

def load_data(data_file, llm_file):
    """Load data from JSON files into the database."""
    with open(data_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    with open(llm_file, "r", encoding="utf-8") as f:
        llm_data = json.load(f)

    llm_lookup = {}
    for entry in llm_data.get("results", []):
        rid = entry.get("result_id")
        if rid:
            llm_lookup[rid] = entry

    rows = [build_applicant_row(entry, llm_lookup) for entry in data.get("results", [])]

    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            # Use ON CONFLICT to handle duplicates
            for row in rows:
                cur.execute("""
                    INSERT INTO applicants (
                        program, comments, date_added, url, status, term,
                        us_or_international, gpa, gre, gre_v, gre_aw, degree,
                        llm_generated_program, llm_generated_university
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (url) DO NOTHING
                """, row)
        conn.commit()
    print(f"Inserted {len(rows)} rows.")

if __name__ == "__main__":  # pragma: no cover
    load_data("src/data/applicant_data.json", "src/data/llm_extend_applicant_data.json")
