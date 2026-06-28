"""
Shared database helpers for GradCafe applicant data.
Uses environment variables for database configuration.
"""

import os
import psycopg

# Use environment variables - no hardcoded credentials!
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://app_user:app_password@db:5432/postgres")

INSERT_APPLICANT_SQL = """
    INSERT INTO applicants (
        program, comments, date_added, url, status, term,
        us_or_international, gpa, gre, gre_v, gre_aw, degree,
        llm_generated_program, llm_generated_university
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
"""

def get_connection():  # pragma: no cover
    """Create a PostgreSQL connection using DATABASE_URL from environment."""
    return psycopg.connect(DATABASE_URL)

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
