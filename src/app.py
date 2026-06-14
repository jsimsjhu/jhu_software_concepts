"""
Flask Web Application — Module 3 / Module 4, JHU Software Concepts
===================================================================
Connects to PostgreSQL, runs 10 analytical queries on the `applicants` table,
displays results in a styled web page, and provides:
  - "Pull Data" button triggers a background scrape of new GradCafe data
  - "Update Analysis" button refreshes the displayed query results

Thread-safe: uses a threading.Lock to prevent simultaneous scrape requests.
"""

import threading
import json
import os
import sys
from datetime import datetime

from flask import Flask, render_template, jsonify

# NOTE: psycopg is imported lazily within create_app() so that the module
# can be imported without requiring libpq (useful for tests that mock the DB).

# ---------------------------------------------------------------------------
# Constants  (not overridable per-instance)
# ---------------------------------------------------------------------------
SCRAPE_OUTPUT = "pulled_data.json"
LLM_EXTEND_FILE = "llm_extend_applicant_data.json"


# ===================================================================
#                       APPLICATION FACTORY
# ===================================================================

def create_app(test_config=None):
    """
    Flask application factory.

    Usage (production)::

        app = create_app()

    Usage (testing)::

        app = create_app({"TESTING": True, "DATABASE_URL": None})

    Parameters
    ----------
    test_config : dict or None
        If provided, these values override the default configuration.
        Common keys:
            - ``TESTING`` (bool)          — enable Flask testing mode
            - ``DATABASE_URL`` (str|None) — PostgreSQL connection string.
              ``None`` means "skip the database" (used when tests mock it).
    """
    app = Flask(__name__)
    app.secret_key = os.urandom(24).hex()

    # ---- Default configuration ----
    app.config["DATABASE_URL"] = os.environ.get(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost/postgres",
    )
    app.config["TESTING"] = False

    # ---- Override with test config if provided ----
    if test_config is not None:
        app.config.update(test_config)

    # ------------------------------------------------------------------
    #                       DATABASE HELPERS
    # ------------------------------------------------------------------

    db_enabled = app.config.get("DATABASE_URL") is not None

    def get_connection():
        """
        Return a new psycopg connection using the configured DATABASE_URL.
        Each call creates a fresh connection (required for thread safety).
        """
        import psycopg
        url = app.config["DATABASE_URL"]
        return psycopg.connect(url)

    def run_query(query):
        """
        Execute *query* against the applicants table and return all rows.
        Opens and closes a connection each time (safe for multi-thread use).
        Raises RuntimeError if database is disabled in config.
        """
        if not db_enabled:
            raise RuntimeError(
                "Database is not configured (TESTING mode). "
                "Mock get_all_results() or provide DATABASE_URL."
            )
        conn = None
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute(query)
            rows = cur.fetchall()
            cur.close()
            return rows
        except Exception as e:
            raise RuntimeError(f"Database error: {e}") from e
        finally:
            if conn:
                conn.close()

    # ------------------------------------------------------------------
    #                   THE 10 ANALYTICAL QUERIES
    # ------------------------------------------------------------------

    def get_all_results():
        """
        Run all 10 queries and return a dict of labelled results.
        Each value is either a scalar, a tuple, or a list of tuples.
        """
        results = {}

        # -- Q1: How many entries applied for Fall 2026? --
        q1 = "SELECT COUNT(*) FROM applicants WHERE term = 'Fall 2026';"
        results["q1_fall_2026_count"] = run_query(q1)[0][0]

        # -- Q2: Percentage of international students (to 2 decimals) --
        q2 = """
            SELECT ROUND(
                (100.0 * COUNT(CASE WHEN us_or_international = 'International' THEN 1 END)
                 / COUNT(*))::numeric, 2
            ) FROM applicants;
        """
        results["q2_pct_international"] = run_query(q2)[0][0]

        # -- Q3: Average GPA, GRE, GRE V, GRE AW (where provided) --
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
        results["q3_avg_scores"] = run_query(q3)[0]

        # -- Q4: Average GPA of American students in Fall 2026 --
        q4 = """
            SELECT ROUND(AVG(gpa)::numeric, 2)
            FROM applicants
            WHERE us_or_international = 'American' AND term = 'Fall 2026';
        """
        results["q4_avg_gpa_american_fall2026"] = run_query(q4)[0][0]

        # -- Q5: Percentage of acceptances for Fall 2026 --
        q5 = """
            SELECT ROUND(
                (100.0 * COUNT(CASE WHEN status = 'Accepted' THEN 1 END)
                 / COUNT(*))::numeric, 2
            ) FROM applicants WHERE term = 'Fall 2026';
        """
        results["q5_pct_accepted_fall2026"] = run_query(q5)[0][0]

        # -- Q6: Average GPA of Fall 2026 acceptances --
        q6 = """
            SELECT ROUND(AVG(gpa)::numeric, 2)
            FROM applicants
            WHERE term = 'Fall 2026' AND status = 'Accepted';
        """
        results["q6_avg_gpa_accepted_fall2026"] = run_query(q6)[0][0]

        # -- Q7: Count of JHU Masters in CS (using llm_generated_university) --
        q7 = """
            SELECT COUNT(*)
            FROM applicants
            WHERE llm_generated_university ILIKE '%Johns Hopkins%'
              AND degree = 'Masters'
              AND program ILIKE '%Computer Science%';
        """
        results["q7_jhu_masters_cs"] = run_query(q7)[0][0]

        # -- Q8: Count of 2026 acceptances to Georgetown, MIT, Stanford, CMU for PhD CS --
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
        results["q8_top_phd_accepts"] = run_query(q8)[0][0]

        # -- Q9 (My original): Count of International PhD applicants --
        q9 = """
            SELECT COUNT(*)
            FROM applicants
            WHERE us_or_international = 'International' AND degree = 'PhD';
        """
        results["q9_intl_phd"] = run_query(q9)[0][0]

        # -- Q10 (My original): Entries per term --
        q10 = "SELECT term, COUNT(*) FROM applicants GROUP BY term ORDER BY term;"
        results["q10_entries_per_term"] = run_query(q10)

        return results

    # ------------------------------------------------------------------
    #              SCRAPE STATE  (thread-safe via lock)
    # ------------------------------------------------------------------

    scrape_lock = threading.Lock()
    scrape_state = {
        "status": "idle",          # idle | running | completed | error
        "message": "",
        "records_added": 0,
        "total_scraped": 0,
        "started_at": None,
        "finished_at": None,
    }

    def background_scrape():
        """
        Runs in a background thread.
        IMPORTANT: The caller (pull_data route) already holds scrape_lock.
        This function:
          1. Calls scrape_gradcafe() to pull new data from GradCafe.
          2. Reads the resulting JSON file.
          3. Inserts only records whose 'result_url' is NOT already in the DB
             (i.e. appends without overwriting).
          4. Updates scrape_state so the UI can report progress.
        Always releases scrape_lock in its finally block.
        """
        nonlocal scrape_state

        try:
            # -- Import scrape module (must be in same directory) --
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            import scrape

            scrape_state["status"] = "running"
            scrape_state["message"] = "Pulling data from GradCafe..."
            scrape_state["started_at"] = datetime.now().isoformat()

            # Run the scraper
            scrape.scrape_gradcafe(
                search_query="computer science",
                max_pages=5,
                output_file=SCRAPE_OUTPUT,
                headless=True,
            )

            # -- Read the freshly scraped data --
            with open(SCRAPE_OUTPUT, "r", encoding="utf-8") as f:
                payload = json.load(f)

            new_records = payload.get("results", [])
            total = len(new_records)
            scrape_state["total_scraped"] = total

            # -- Optionally load LLM-extended fields for dedup lookup --
            llm_lookup = {}
            if os.path.exists(LLM_EXTEND_FILE):
                with open(LLM_EXTEND_FILE, "r", encoding="utf-8") as f:
                    llm_data = json.load(f)
                for entry in llm_data.get("results", []):
                    rid = entry.get("result_id")
                    if rid:
                        llm_lookup[rid] = entry

            # -- Insert only NEW records (by result_url) --
            conn = get_connection()
            try:
                cur = conn.cursor()

                # Build a set of existing URLs for fast dedup
                cur.execute("SELECT url FROM applicants WHERE url IS NOT NULL;")
                existing_urls = {row[0] for row in cur.fetchall()}

                rows_to_insert = []
                for rec in new_records:
                    result_url = rec.get("result_url")
                    if result_url and result_url in existing_urls:
                        continue          # skip duplicate
                    if result_url:
                        existing_urls.add(result_url)

                    rid = rec.get("result_id")
                    llm = llm_lookup.get(rid, {})

                    rows_to_insert.append((
                        rec.get("program"),
                        rec.get("comments"),
                        rec.get("added_on"),
                        result_url,
                        rec.get("acceptance_status"),
                        rec.get("term"),
                        rec.get("applicant_type"),
                        rec.get("gpa"),
                        rec.get("gre_quant"),
                        rec.get("gre_verbal"),
                        rec.get("gre_aw"),
                        rec.get("degree"),
                        llm.get("llm_generated_program"),
                        llm.get("llm_generated_university"),
                    ))

                if rows_to_insert:
                    insert_sql = """
                        INSERT INTO applicants (
                            program, comments, date_added, url, status, term,
                            us_or_international, gpa, gre, gre_v, gre_aw, degree,
                            llm_generated_program, llm_generated_university
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    cur.executemany(insert_sql, rows_to_insert)
                    conn.commit()

                inserted = len(rows_to_insert)
                scrape_state["records_added"] = inserted
                scrape_state["status"] = "completed"
                scrape_state["message"] = (
                    f"Scraped {total} record(s); "
                    f"appended {inserted} new record(s) to database."
                )

            except Exception as e:
                conn.rollback()
                raise RuntimeError(f"DB insert error during scrape: {e}") from e
            finally:
                cur.close()
                conn.close()

        except Exception as e:
            scrape_state["status"] = "error"
            scrape_state["message"] = f"Scrape failed: {e}"
            import traceback
            traceback.print_exc()
        finally:
            scrape_state["finished_at"] = datetime.now().isoformat()
            # Release the lock so future pulls are allowed
            scrape_lock.release()

    # ------------------------------------------------------------------
    #                         FLASK ROUTES
    # ------------------------------------------------------------------

    @app.route("/")
    @app.route("/analysis")
    def index():
        """
        Main page: run all queries and render the template with results.
        Also passes scrape_state so the UI can show current status.
        """
        try:
            results = get_all_results()
            db_ok = True
            db_error = None
        except RuntimeError as e:
            results = {}
            db_ok = False
            db_error = str(e)

        return render_template(
            "index.html",
            results=results,
            db_ok=db_ok,
            db_error=db_error,
            scrape_state=scrape_state,
        )

    @app.route("/pull_data", methods=["POST"])
    @app.route("/pull-data", methods=["POST"])
    def pull_data():
        """
        Start a background scrape if one is not already running.
        Returns JSON so the front end can update the page dynamically.
        """
        # For testing: allow BUSY config flag to simulate in-progress state
        if app.config.get("BUSY"):
            return jsonify({
                "success": False,
                "message": "A data pull is already in progress. Please wait.",
            }), 409

        if not db_enabled:
            return jsonify({
                "success": False,
                "message": "Database is not available. Cannot pull data.",
            })

        if not scrape_lock.acquire(blocking=False):
            return jsonify({
                "success": False,
                "message": "A data pull is already in progress. Please wait.",
            }), 409

        # Reset state for new run
        scrape_state["status"] = "starting"
        scrape_state["message"] = "Starting data pull..."
        scrape_state["records_added"] = 0
        scrape_state["total_scraped"] = 0
        scrape_state["started_at"] = None
        scrape_state["finished_at"] = None

        thread = threading.Thread(target=background_scrape, daemon=True)
        thread.start()

        return jsonify({
            "success": True,
            "message": "Data pull started. This may take a few minutes.",
        })

    @app.route("/update_analysis", methods=["POST"])
    @app.route("/update-analysis", methods=["POST"])
    def update_analysis():
        """
        Re-run all queries and return fresh results.
        If a scrape is in progress, inform the user instead.
        """
        # For testing: allow BUSY config flag to simulate in-progress state
        if app.config.get("BUSY"):
            return jsonify({
                "success": False,
                "message": "A data pull is currently in progress. "
                           "Please wait for it to complete before refreshing.",
                "scraping": True,
            }), 409

        if scrape_state["status"] == "running":
            return jsonify({
                "success": False,
                "message": "A data pull is currently in progress. "
                           "Please wait for it to complete before refreshing.",
                "scraping": True,
            }), 409

        try:
            results = get_all_results()
            html = render_template(
                "_results.html",
                results=results,
            )
            return jsonify({
                "success": True,
                "html": html,
                "message": "Analysis updated successfully.",
            })
        except RuntimeError as e:
            return jsonify({
                "success": False,
                "message": f"Failed to update analysis: {e}",
            })

    @app.route("/scrape_status", methods=["GET"])
    def scrape_status():
        """Return the current scrape state as JSON (for polling)."""
        return jsonify(scrape_state)

    return app


# ===================================================================
#                           ENTRY POINT
# ===================================================================

if __name__ == "__main__":  # pragma: no cover
    application = create_app()
    print("Starting Flask app on http://127.0.0.1:5000")
    application.run(debug=True, threaded=True)