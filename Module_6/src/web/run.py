"""
Flask application for GradCafe Applicant Data Analysis (Module 5).

Provides a web UI to scrape, load, and query applicant data from
The GradCafe.  Uses a background thread for scraping and a thread
lock to prevent concurrent data-pull operations.
"""

import json
import os
import threading

import psycopg
from flask import Flask, jsonify, render_template, current_app, request
from publisher import publish_task

try:
    from db_helpers import build_applicant_row, INSERT_APPLICANT_SQL
except ImportError:  # pragma: no cover
    from db_helpers import build_applicant_row, INSERT_APPLICANT_SQL

# ---------------------------------------------------------------------------
# Default paths – can be overridden via create_app() test_config
# ---------------------------------------------------------------------------
SCRAPE_OUTPUT = "gradcafe_results.json"
LLM_EXTEND_FILE = "llm_extend_applicant_data.json"

# ---------------------------------------------------------------------------
# Global scrape state (protected by a threading.Lock)
# ---------------------------------------------------------------------------
scrape_state = {
    "status": "idle",           # idle | running | completed | error
    "message": "Ready to pull data.",
    "records_added": 0,
    "error": None,
}
_state_lock = threading.Lock()


def _reset_state():
    """Set scrape_state back to its idle defaults."""
    with _state_lock:
        scrape_state["status"] = "idle"
        scrape_state["message"] = "Ready to pull data."
        scrape_state["records_added"] = 0
        scrape_state["error"] = None


def _set_status(status, message, records_added=None, error=None):
    """Update scrape_state under the lock."""
    with _state_lock:
        scrape_state["status"] = status
        scrape_state["message"] = message
        if records_added is not None:
            scrape_state["records_added"] = records_added
        if error is not None:
            scrape_state["error"] = error


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

def get_connection():
    """Create a fresh psycopg connection using the app's DATABASE_URL."""
    url = current_app.config["DATABASE_URL"]
    return psycopg.connect(url)


def get_all_results():
    conn = get_connection()
    cur = conn.cursor()

    # Q1: Fall 2026 applicants (with LIMIT)
    cur.execute("SELECT COUNT(*) FROM applicants WHERE term = %s LIMIT 1;", ("Fall 2026",))
    q1 = cur.fetchone()[0]

    # Q2: International students percentage (with LIMIT)
    cur.execute("""
        SELECT ROUND((100.0 * COUNT(CASE WHEN us_or_international = %s THEN 1 END) / COUNT(*))::numeric, 2)
        FROM applicants
        LIMIT 1;
    """, ("International",))
    q2 = cur.fetchone()[0]

    # Q3: Average scores (with LIMIT)
    cur.execute("""
        SELECT
            ROUND(AVG(NULLIF(gpa, '')::numeric), 2),
            ROUND(AVG(NULLIF(gre, '')::numeric), 2),
            ROUND(AVG(NULLIF(gre_v, '')::numeric), 2),
            ROUND(AVG(NULLIF(gre_aw, '')::numeric), 2)
        FROM applicants
        WHERE gpa IS NOT NULL AND gpa != ''
           OR gre IS NOT NULL AND gre != ''
           OR gre_v IS NOT NULL AND gre_v != ''
           OR gre_aw IS NOT NULL AND gre_aw != ''
        LIMIT 1;
    """)
    q3 = cur.fetchone()

    # Q4: American students Fall 2026 GPA (with LIMIT)
    cur.execute("""
        SELECT ROUND(AVG(NULLIF(gpa, '')::numeric), 2)
        FROM applicants
        WHERE us_or_international = %s AND term = %s
        LIMIT 1;
    """, ("American", "Fall 2026"))
    q4 = cur.fetchone()[0]

    # Q5: Fall 2026 acceptance rate (with LIMIT)
    cur.execute("""
        SELECT ROUND((100.0 * COUNT(CASE WHEN status = %s THEN 1 END) / COUNT(*))::numeric, 2)
        FROM applicants
        WHERE term = %s
        LIMIT 1;
    """, ("Accepted", "Fall 2026"))
    q5 = cur.fetchone()[0]

    # Q6: Fall 2026 accepted GPA (with LIMIT)
    cur.execute("""
        SELECT ROUND(AVG(NULLIF(gpa, '')::numeric), 2)
        FROM applicants
        WHERE term = %s AND status = %s
        LIMIT 1;
    """, ("Fall 2026", "Accepted"))
    q6 = cur.fetchone()[0]

    # Q7: JHU Masters in CS (with LIMIT)
    cur.execute("""
        SELECT COUNT(*)
        FROM applicants
        WHERE llm_generated_university ILIKE %s
          AND degree = %s
          AND program ILIKE %s
        LIMIT 1;
    """, ("%Johns Hopkins%", "Masters", "%Computer Science%"))
    q7 = cur.fetchone()[0]

    # Q8: Top PhD acceptances (with LIMIT)
    cur.execute("""
        SELECT COUNT(*)
        FROM applicants
        WHERE term = %s
          AND status = %s
          AND degree = %s
          AND llm_generated_university IN (%s, %s, %s, %s)
          AND program ILIKE %s
        LIMIT 1;
    """, (
        "Fall 2026", "Accepted", "PhD",
        "Georgetown University", "MIT", "Stanford University",
        "Carnegie Mellon University", "%Computer Science%",
    ))
    q8 = cur.fetchone()[0]

    # Q9: International PhD applicants (with LIMIT)
    cur.execute("""
        SELECT COUNT(*)
        FROM applicants
        WHERE us_or_international = %s AND degree = %s
        LIMIT 1;
    """, ("International", "PhD"))
    q9 = cur.fetchone()[0]

    # Q10: Entries per term (with LIMIT)
    cur.execute("""
        SELECT term, COUNT(*)
        FROM applicants
        GROUP BY term
        ORDER BY term
        LIMIT 100;
    """)
    q10 = cur.fetchall()

    cur.close()
    conn.close()

    return {
        "q1_fall_2026_count": q1,
        "q2_pct_international": q2,
        "q3_avg_scores": q3,
        "q4_avg_gpa_american_fall2026": q4,
        "q5_pct_accepted_fall2026": q5,
        "q6_avg_gpa_accepted_fall2026": q6,
        "q7_jhu_masters_cs": q7,
        "q8_top_phd_accepts": q8,
        "q9_intl_phd": q9,
        "q10_entries_per_term": q10,
    }

# ---------------------------------------------------------------------------
# Background scraper (runs in a separate thread)
# ---------------------------------------------------------------------------

def background_scrape(app):  # pragma: no cover
    """
    Read the scraped JSON file, insert new records into the database, and
    update ``scrape_state`` on completion or error.

    This function is designed to run inside a ``threading.Thread`` so that
    the Flask request can return immediately.

    NOTE: Runs in a daemon thread; coverage.py cannot trace it.
    """
    _set_status("running", "Data pull in progress…", records_added=0)
    records_added = 0
    try:
        # ---- 1. Load the scraped JSON ----
        with open(SCRAPE_OUTPUT, "r", encoding="utf-8") as f:
            data = json.load(f)

        results = data.get("results", [])
        if not results:
            _set_status("completed", "No new data found.", records_added=0)
            return

        # ---- 2. Load LLM extend data (if available) ----
        llm_lookup = {}
        try:
            with open(LLM_EXTEND_FILE, "r", encoding="utf-8") as f:
                llm_data = json.load(f)
            for entry in llm_data.get("results", []):
                rid = entry.get("result_id")
                if rid:
                    llm_lookup[rid] = entry
        except (FileNotFoundError, json.JSONDecodeError):
            llm_lookup = {}

        # ---- 3. Connect to the database ----
        conn = psycopg.connect(app.config["DATABASE_URL"])
        cur = conn.cursor()

        # ---- 4. Fetch existing result URLs to avoid duplicates ----
        cur.execute("SELECT url FROM applicants WHERE url IS NOT NULL;")
        existing_urls = {row[0] for row in cur.fetchall()}

        # ---- 5. Insert only new records ----
        for entry in results:
            result_url = entry.get("result_url")
            if result_url and result_url in existing_urls:
                continue

            row = build_applicant_row(entry, llm_lookup)
            cur.execute(INSERT_APPLICANT_SQL, row)
            records_added += 1

            # Track the URL we just inserted so we don't re-insert it
            if result_url:
                existing_urls.add(result_url)

        conn.commit()
        cur.close()
        conn.close()

        _set_status(
            "completed",
            f"Data pull completed. {records_added} new records added.",
            records_added=records_added,
        )

    except (psycopg.Error, ValueError, KeyError) as exc:
        _set_status(
            "error",
            f"Data pull failed: {exc}",
            records_added=records_added,
            error=str(exc),
        )


# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------

def create_app(test_config=None):
    """
    Flask application factory.

    Parameters
    ----------
    test_config : dict or None
        If provided, used to override configuration for testing.

    Returns
    -------
    Flask
    """
    app = Flask(__name__)

    # ---- Default configuration ----
    app.config["DATABASE_URL"] = os.environ.get(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost/postgres",
    )
    app.config["BUSY"] = False

    # ---- Override with test_config if supplied ----
    if test_config is not None:
        app.config.update(test_config)

    # ---- Reset scrape state on startup ----
    _reset_state()

    # ==================================================================
    #                             ROUTES
    # ==================================================================

    @app.route("/")
    def index():
        """
        Render the main dashboard page.

        If the database is disabled (DATABASE_URL is None) or queries
        raise an error, the template is rendered with ``db_ok=False``
        and an error description.
        """
        db_ok = True
        db_error = None
        results = None

        if app.config.get("DATABASE_URL") is None:
            db_ok = False
            db_error = "Database is not configured."
        else:
            try:
                results = get_all_results()
            except (psycopg.Error, RuntimeError) as exc:
                db_ok = False
                db_error = str(exc)

        return render_template(
            "index.html",
            results=results,
            db_ok=db_ok,
            db_error=db_error,
            scrape_state=scrape_state,
        )

    # ------------------------------------------------------------------
    # /analysis
    # ------------------------------------------------------------------

    @app.route("/analysis")
    def analysis():
        """
        Render the analysis page (identical to index).
        """
        return index()

    # ------------------------------------------------------------------
    # /pull-data  (hyphen)
    # ------------------------------------------------------------------

    @app.route("/pull-data", methods=["POST"])
    def pull_data_hyphen():
        return _pull_data()

    # ------------------------------------------------------------------
    # /pull_data  (underscore)
    # ------------------------------------------------------------------

    @app.route("/pull_data", methods=["POST"])
    def pull_data_underscore():
        return _pull_data()

    # ------------------------------------------------------------------

    def _pull_data():
        """
        Start a background data-pull (scrape + insert).

        Returns 409 Conflict if a pull is already in progress.
        """
        if app.config.get("BUSY"):
            return jsonify({
                "success": False,
                "message": "A data pull is already in progress.",
            }), 409

        if app.config.get("DATABASE_URL") is None:
            return jsonify({
                "success": False,
                "message": "Database is not available.",
            })

        _reset_state()

        thread = threading.Thread(target=background_scrape, args=(app,), daemon=True)
        thread.start()

        return jsonify({
            "success": True,
            "message": "Data pull started.",
        })

    # ------------------------------------------------------------------
    # /update-analysis  (hyphen)
    # ------------------------------------------------------------------

    @app.route("/update-analysis", methods=["POST"])
    def update_analysis_hyphen():
        return _update_analysis()

    # ------------------------------------------------------------------
    # /update_analysis  (underscore)
    # ------------------------------------------------------------------

    @app.route("/update_analysis", methods=["POST"])
    def update_analysis_underscore():
        return _update_analysis()

    # ------------------------------------------------------------------

    def _update_analysis():
        """
        Re-run all queries and return rendered HTML.

        Returns 409 Conflict if a data pull is in progress.
        """
        if app.config.get("BUSY"):
            return jsonify({
                "success": False,
                "message": "A data pull is in progress.",
            }), 409

        if app.config.get("DATABASE_URL") is None:
            return jsonify({
                "success": False,
                "message": "Failed to update analysis.",
            })

        try:
            results = get_all_results()
            html = render_template("_results.html", results=results)
            return jsonify({
                "success": True,
                "html": html,
                "message": "Analysis updated successfully.",
            })
        except RuntimeError:  # pragma: no cover
            return jsonify({  # pragma: no cover
                "success": False,
                "message": "Failed to update analysis.",
            })

    # ------------------------------------------------------------------
    # /scrape_status
    # ------------------------------------------------------------------

    @app.route("/scrape_status")
    def scrape_status():
        """Return the current background-scrape state as JSON."""
        with _state_lock:
            response = {
                "status": scrape_state["status"],
                "message": scrape_state["message"],
                "records_added": scrape_state["records_added"],
            }
            error = scrape_state.get("error")
            if error is not None:
                response["error"] = error
            return jsonify(response)

    @app.route("/api/scrape", methods=["POST"])
    def trigger_scrape():
        """Trigger a scrape task via RabbitMQ."""
        try:
            payload = request.get_json() or {}
            publish_task("scrape_new_data", payload)
            return jsonify({
                "status": "queued",
                "message": "Scrape task published successfully"
            }), 202
        except Exception as e:  # pylint: disable=broad-exception-caught
            return jsonify({
                "status": "error",
                "message": str(e)
            }), 503

    @app.route("/api/recompute", methods=["POST"])
    def trigger_recompute():
        """Trigger a recompute analytics task via RabbitMQ."""
        try:
            payload = request.get_json() or {}
            publish_task("recompute_analytics", payload)
            return jsonify({
                "status": "queued",
                "message": "Recompute task published successfully"
            }), 202
        except Exception as e:  # pylint: disable=broad-exception-caught
            return jsonify({
                "status": "error",
                "message": str(e)
            }), 503

    return app


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":  # pragma: no cover
    application = create_app()
    print("Starting Flask app on http://0.0.0.0:8080")
    application.run(host="0.0.0.0", port=8080, debug=False, threaded=True)
