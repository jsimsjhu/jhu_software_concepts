# pylint: disable=trailing-newlines,trailing-whitespace,line-too-long,consider-using-with
"""
Flask Web Application — Module 3 / Module 4, JHU Software Concepts
===================================================================
Connects to PostgreSQL, runs 10 analytical queries on the `applicants` table,
displays results in a styled web page, and provides:
  - "Pull Data" button triggers a background scrape of new GradCafe data
  - "Update Analysis" button refreshes the displayed query results

Thread-safe: uses a threading.Lock to prevent simultaneous scrape requests.
"""
# pylint: disable=no-member

import threading
import json
import os
import traceback
from datetime import datetime

import psycopg
from flask import Flask, render_template, jsonify

try:
    from .db_helpers import INSERT_APPLICANT_SQL, build_applicant_row
except ImportError:
    from db_helpers import INSERT_APPLICANT_SQL, build_applicant_row

try:
    from . import scrape as scrape_module
except ImportError:
    import scrape as scrape_module

SCRAPE_OUTPUT = "pulled_data.json"
LLM_EXTEND_FILE = "llm_extend_applicant_data.json"


def get_connection(app):
    """Return a new psycopg connection using the configured DATABASE_URL."""
    return psycopg.connect(app.config["DATABASE_URL"])


def run_query(app, query):
    """Execute query against applicants table and return all rows."""
    if app.config.get("DATABASE_URL") is None:
        raise RuntimeError("Database is not configured (TESTING mode).")
    with get_connection(app) as conn:
        with conn.cursor() as cur:
            cur.execute(query)
            rows = cur.fetchall()
    return rows


def get_existing_urls(app):
    """Return a set of all existing result URLs in the database."""
    conn = get_connection(app)
    cur = conn.cursor()
    try:
        cur.execute("SELECT url FROM applicants WHERE url IS NOT NULL;")
        return {row[0] for row in cur.fetchall()}
    finally:
        cur.close()
        conn.close()


def insert_new_rows(app, rows_to_insert):
    """Insert new applicant rows using executemany, then commit."""
    conn = get_connection(app)
    cur = conn.cursor()
    try:
        cur.executemany(INSERT_APPLICANT_SQL, rows_to_insert)
        conn.commit()
    except (psycopg.Error, psycopg.OperationalError) as e:
        conn.rollback()
        raise RuntimeError(f"DB insert error during scrape: {e}") from e
    finally:
        cur.close()
        conn.close()


def load_llm_lookup():
    """Load LLM-extended fields file into a result_id lookup dict."""
    llm_lookup = {}
    if os.path.exists(LLM_EXTEND_FILE):
        with open(LLM_EXTEND_FILE, "r", encoding="utf-8") as f:
            llm_data = json.load(f)
        for entry in llm_data.get("results", []):
            rid = entry.get("result_id")
            if rid:
                llm_lookup[rid] = entry
    return llm_lookup


def read_scraped_data():
    """Read the freshly scraped JSON output file."""
    with open(SCRAPE_OUTPUT, "r", encoding="utf-8") as f:
        return json.load(f)


def dedup_and_insert(app, new_records, llm_lookup):
    """Deduplicate new_records against existing URLs, then insert."""
    existing_urls = get_existing_urls(app)
    rows_to_insert = []
    for rec in new_records:
        result_url = rec.get("result_url")
        if result_url and result_url in existing_urls:
            continue
        if result_url:
            existing_urls.add(result_url)
        rows_to_insert.append(build_applicant_row(rec, llm_lookup))
    if rows_to_insert:
        insert_new_rows(app, rows_to_insert)
    return len(rows_to_insert)


# pylint: disable=duplicate-code
def get_all_results(app):
    """
    Run all 10 queries and return a dict of labelled results.
    Each value is either a scalar, a tuple, or a list of tuples.
    """
    results = {}
    q1 = "SELECT COUNT(*) FROM applicants WHERE term = 'Fall 2026';"
    results["q1_fall_2026_count"] = run_query(app, q1)[0][0]
    q2 = """
        SELECT ROUND(
            (100.0 * COUNT(CASE WHEN us_or_international = 'International' THEN 1 END)
             / COUNT(*))::numeric, 2
        ) FROM applicants;
    """
    results["q2_pct_international"] = run_query(app, q2)[0][0]
    q3 = """
        SELECT
            ROUND(AVG(gpa)::numeric, 2),
            ROUND(AVG(gre)::numeric, 2),
            ROUND(AVG(gre_v)::numeric, 2),
            ROUND(AVG(gre_aw)::numeric, 2)
        FROM applicants
        WHERE gpa IS NOT NULL OR gre IS NOT NULL
           OR gre_v IS NOT NULL OR gre_aw IS NOT NULL;
    """
    results["q3_avg_scores"] = run_query(app, q3)[0]
    q4 = """
        SELECT ROUND(AVG(gpa)::numeric, 2)
        FROM applicants
        WHERE us_or_international = 'American' AND term = 'Fall 2026';
    """
    results["q4_avg_gpa_american_fall2026"] = run_query(app, q4)[0][0]
    q5 = """
        SELECT ROUND(
            (100.0 * COUNT(CASE WHEN status = 'Accepted' THEN 1 END)
             / COUNT(*))::numeric, 2
        ) FROM applicants WHERE term = 'Fall 2026';
    """
    results["q5_pct_accepted_fall2026"] = run_query(app, q5)[0][0]
    q6 = """
        SELECT ROUND(AVG(gpa)::numeric, 2)
        FROM applicants
        WHERE term = 'Fall 2026' AND status = 'Accepted';
    """
    results["q6_avg_gpa_accepted_fall2026"] = run_query(app, q6)[0][0]
    q7 = """
        SELECT COUNT(*)
        FROM applicants
        WHERE llm_generated_university ILIKE '%Johns Hopkins%'
          AND degree = 'Masters'
          AND program ILIKE '%Computer Science%';
    """
    results["q7_jhu_masters_cs"] = run_query(app, q7)[0][0]
    q8 = """
        SELECT COUNT(*)
        FROM applicants
        WHERE term = 'Fall 2026'
          AND status = 'Accepted'
          AND degree = 'PhD'
          AND llm_generated_university IN (
              'Georgetown University', 'MIT',
              'Stanford University', 'Carnegie Mellon University'
          )
          AND program ILIKE '%Computer Science%';
    """
    results["q8_top_phd_accepts"] = run_query(app, q8)[0][0]
    q9 = """
        SELECT COUNT(*)
        FROM applicants
        WHERE us_or_international = 'International' AND degree = 'PhD';
    """
    results["q9_intl_phd"] = run_query(app, q9)[0][0]
    q10 = "SELECT term, COUNT(*) FROM applicants GROUP BY term ORDER BY term;"
    results["q10_entries_per_term"] = run_query(app, q10)
    return results
# pylint: enable=duplicate-code


def run_scraper(state):
    """Run the Selenium scraper and update state."""
    state["status"] = "running"
    state["message"] = "Pulling data from GradCafe..."
    state["started_at"] = datetime.now().isoformat()
    scrape_module.scrape_gradcafe(
        search_query="computer science",
        max_pages=5,
        output_file=SCRAPE_OUTPUT,
        headless=True,
    )


# pylint: disable=too-many-locals, too-many-statements
def create_app(test_config=None):
    """Flask application factory with routes for analysis and data pulling."""
    app = Flask(__name__)
    app.secret_key = os.urandom(24).hex()
    app.config["DATABASE_URL"] = os.environ.get(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost/postgres",
    )
    app.config["TESTING"] = False
    if test_config is not None:
        app.config.update(test_config)
    db_enabled = app.config.get("DATABASE_URL") is not None
    scrape_lock = threading.Lock()
    scrape_state = {
        "status": "idle", "message": "",
        "records_added": 0, "total_scraped": 0,
        "started_at": None, "finished_at": None,
    }

    def handle_scrape_complete():
        """Process scraped data and insert new records into the database."""
        payload = read_scraped_data()
        new_records = payload.get("results", [])
        total = len(new_records)
        scrape_state["total_scraped"] = total
        llm_lookup = load_llm_lookup()
        inserted = dedup_and_insert(app, new_records, llm_lookup)
        scrape_state["records_added"] = inserted
        scrape_state["status"] = "completed"
        scrape_state["message"] = (
            f"Scraped {total} record(s); "
            f"appended {inserted} new record(s) to database."
        )

    @app.route("/")
    @app.route("/analysis")
    def index():
        """Main page: render template with query results and scrape state."""
        try:
            results = get_all_results(app)
            db_ok, db_error = True, None
        except RuntimeError as e:
            results, db_ok, db_error = {}, False, str(e)
        return render_template(
            "index.html", results=results, db_ok=db_ok,
            db_error=db_error, scrape_state=scrape_state,
        )

    @app.route("/pull_data", methods=["POST"])
    @app.route("/pull-data", methods=["POST"])
    def pull_data():
        """Start a background scrape if one is not already running."""
        if app.config.get("BUSY"):
            return jsonify({"success": False,
                            "message": "A data pull is already in progress."}), 409
        if not db_enabled:
            return jsonify({"success": False,
                            "message": "Database is not available."})
        if not scrape_lock.acquire(blocking=False):
            return jsonify({"success": False,
                            "message": "A data pull is already in progress."}), 409
        scrape_state.update(
            status="starting", message="Starting data pull...",
            records_added=0, total_scraped=0,
            started_at=None, finished_at=None,
        )

        def bg_work():
            try:
                run_scraper(scrape_state)
                handle_scrape_complete()
            except (json.JSONDecodeError, KeyError, OSError) as e:
                scrape_state["status"] = "error"
                scrape_state["message"] = f"Scrape failed: {e}"
                traceback.print_exc()
            finally:
                scrape_state["finished_at"] = datetime.now().isoformat()
                scrape_lock.release()

        threading.Thread(target=bg_work, daemon=True).start()
        return jsonify({"success": True,
                        "message": "Data pull started. This may take a few minutes."})

    @app.route("/update_analysis", methods=["POST"])
    @app.route("/update-analysis", methods=["POST"])
    def update_analysis():
        """Re-run all queries and return fresh results."""
        if app.config.get("BUSY") or scrape_state["status"] == "running":
            return jsonify({"success": False,
                            "message": "A data pull is in progress.",
                            "scraping": True}), 409
        try:
            results = get_all_results(app)
            html = render_template("_results.html", results=results)
            return jsonify({"success": True, "html": html,
                            "message": "Analysis updated successfully."})
        except RuntimeError as e:
            return jsonify({"success": False,
                            "message": f"Failed to update analysis: {e}"})

    @app.route("/scrape_status", methods=["GET"])
    def scrape_status():
        """Return the current scrape state as JSON (for polling)."""
        return jsonify(scrape_state)

    return app


if __name__ == "__main__":  # pragma: no cover
    application = create_app()
    print("Starting Flask app on http://127.0.0.1:5000")
    application.run(debug=True, threaded=True)
    
