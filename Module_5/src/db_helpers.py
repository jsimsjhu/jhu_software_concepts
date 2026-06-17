# pylint: disable=missing-final-newline
"""
Shared database helpers for GradCafe applicant data.
Eliminates duplicated SQL blocks across the codebase.
"""

import psycopg

INSERT_APPLICANT_SQL = """
    INSERT INTO applicants (
        program, comments, date_added, url, status, term,
        us_or_international, gpa, gre, gre_v, gre_aw, degree,
        llm_generated_program, llm_generated_university
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
"""

DB_NAME = "postgres"
DB_USER = "postgres"
DB_PASSWORD = "postgres"
DB_HOST = "localhost"


def get_connection():
    """Create a PostgreSQL connection using the configured defaults."""
    return psycopg.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
    )


def build_applicant_row(entry, llm_lookup):
    """
    Build a tuple for insertion from a data entry and LLM lookup dict.

    Parameters
    ----------
    entry : dict
        A single applicant record from scraped data.
    llm_lookup : dict
        Mapping of result_id to LLM-extended fields.

    Returns
    -------
    tuple
        A 14-element tuple matching INSERT_APPLICANT_SQL columns.
    """
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
