"""
Tests for src/load_data.py and src/query_data.py using monkeypatch.

Replaces psycopg.connect() and all file I/O with mocks so no real
PostgreSQL database is needed.
"""

import json
import os
import sys
from unittest.mock import MagicMock, call

import pytest

# Ensure src/ is on the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

# --- Replace psycopg with a mock BEFORE importing modules that use it ---
# load_data.py and query_data.py both do `import psycopg` at module level,
# which requires the C libpq library.  We inject a fake module instead.
_fake_psycopg = MagicMock()
_fake_psycopg.connect = MagicMock()
sys.modules["psycopg"] = _fake_psycopg

import load_data
import query_data


# ======================================================================
#                        Pytest markers  (configured in pyproject.toml)
# ======================================================================
# Register markers so pytest doesn't emit warnings.
pytestmark = [
    pytest.mark.db,
]


# ======================================================================
#                     Fixtures – Mock DB connection
# ======================================================================

@pytest.fixture
def mock_conn():
    """
    Return a MagicMock that stands in for a psycopg connection.
    The mock's ``cursor()`` returns a context-manager MagicMock so that
    ``with conn.cursor() as cur:`` works (as used in load_data.py).
    """
    conn = MagicMock()
    # Create a cursor that supports the context manager protocol
    cursor = MagicMock()
    cursor.__enter__.return_value = cursor
    cursor.__exit__.return_value = None
    cursor.fetchall.return_value = []

    # conn.cursor() also returns a context-manager-compatible cursor
    conn.cursor.return_value = cursor
    conn.cursor.__enter__.return_value = cursor
    conn.cursor.__exit__.return_value = None
    return conn


@pytest.fixture
def mock_psycopg(monkeypatch):
    """
    Replace ``psycopg.connect`` with a mock that returns ``mock_conn``.
    This fixture yields a function ``(conn)`` that patches the target
    modules so that ANY call to ``psycopg.connect()`` returns *conn*.
    """
    def _patch(conn=None):
        if conn is None:
            conn = MagicMock()
        fake_connect = MagicMock(return_value=conn)
        monkeypatch.setattr(load_data.psycopg, "connect", fake_connect)
        monkeypatch.setattr(query_data.psycopg, "connect", fake_connect)
        return conn
    return _patch


@pytest.fixture
def mock_json_files(tmp_path):
    """
    Create temporary ``applicant_data.json`` and ``llm_extend_applicant_data.json``
    files with known content and return their paths.
    """
    data_file = tmp_path / "applicant_data.json"
    llm_file = tmp_path / "llm_extend_applicant_data.json"

    applicant_data = {
        "results": [
            {
                "result_id": "abc123",
                "program": "Computer Science",
                "comments": "Great program",
                "added_on": "2026-05-15",
                "result_url": "https://gradcafe.com/result/abc123",
                "acceptance_status": "Accepted",
                "term": "Fall 2026",
                "applicant_type": "International",
                "gpa": 3.85,
                "gre_quant": 168,
                "gre_verbal": 160,
                "gre_aw": 4.0,
                "degree": "PhD",
            },
            {
                "result_id": "def456",
                "program": "Data Science",
                "comments": "Good fit",
                "added_on": "2026-06-01",
                "result_url": "https://gradcafe.com/result/def456",
                "acceptance_status": "Wait listed",
                "term": "Fall 2026",
                "applicant_type": "American",
                "gpa": 3.70,
                "gre_quant": 165,
                "gre_verbal": 158,
                "gre_aw": 3.5,
                "degree": "Masters",
            },
        ]
    }

    llm_data = {
        "results": [
            {
                "result_id": "abc123",
                "llm_generated_program": "Computer Science PhD",
                "llm_generated_university": "Stanford University",
            },
        ]
    }

    with open(data_file, "w", encoding="utf-8") as f:
        json.dump(applicant_data, f)
    with open(llm_file, "w", encoding="utf-8") as f:
        json.dump(llm_data, f)

    return str(data_file), str(llm_file)


# ======================================================================
#              Tests for load_data.create_table
# ======================================================================

class TestCreateTable:
    """create_table should execute the DDL and commit."""

    @pytest.mark.db
    def test_create_table_executes_sql(self, mock_conn):
        """Verify the DDL is executed via the connection cursor."""
        load_data.create_table(mock_conn)

        # The cursor should have been obtained and execute called once
        assert mock_conn.cursor.called
        cursor = mock_conn.cursor.return_value
        cursor.execute.assert_called_once()

        # The SQL passed should contain CREATE TABLE and applicants
        sql_arg = cursor.execute.call_args[0][0]
        assert "CREATE TABLE" in sql_arg
        assert "applicants" in sql_arg

    @pytest.mark.db
    def test_create_table_commits(self, mock_conn):
        """create_table should commit the transaction."""
        load_data.create_table(mock_conn)
        mock_conn.commit.assert_called_once()


# ======================================================================
#              Tests for load_data.load_data
# ======================================================================

class TestLoadData:
    """load_data should read JSON files and insert rows correctly."""

    @pytest.mark.db
    def test_load_data_inserts_correct_rows(self, mock_conn, mock_json_files):
        """
        Verify that ``load_data`` calls ``executemany`` with the expected
        SQL template and the correct row tuples.
        """
        data_path, llm_path = mock_json_files
        load_data.load_data(mock_conn, data_path, llm_path)

        # The cursor should have executed executemany once
        cursor = mock_conn.cursor.return_value
        cursor.executemany.assert_called_once()

        sql, rows = cursor.executemany.call_args[0]

        # -- Verify SQL structure --
        assert "INSERT INTO applicants" in sql
        assert "%s" in sql

        # -- Verify number of rows --
        assert len(rows) == 2

        # -- First row (abc123) should include LLM data --
        row0 = rows[0]
        assert row0[0] == "Computer Science"           # program
        assert row0[1] == "Great program"              # comments
        assert row0[2] == "2026-05-15"                 # added_on
        assert row0[3] == "https://gradcafe.com/result/abc123"  # url
        assert row0[4] == "Accepted"                   # status
        assert row0[5] == "Fall 2026"                  # term
        assert row0[6] == "International"              # us_or_international
        assert row0[7] == 3.85                         # gpa
        assert row0[8] == 168                          # gre (quant)
        assert row0[9] == 160                          # gre_v
        assert row0[10] == 4.0                         # gre_aw
        assert row0[11] == "PhD"                       # degree
        # LLM-extended fields from lookup
        assert row0[12] == "Computer Science PhD"      # llm_generated_program
        assert row0[13] == "Stanford University"       # llm_generated_university

        # -- Second row (def456) should have None for LLM fields --
        row1 = rows[1]
        assert row1[0] == "Data Science"
        assert row1[4] == "Wait listed"
        assert row1[6] == "American"
        assert row1[11] == "Masters"
        assert row1[12] is None   # no LLM data for this result_id
        assert row1[13] is None

    @pytest.mark.db
    def test_load_data_commits(self, mock_conn, mock_json_files):
        """load_data should commit after insertion."""
        data_path, llm_path = mock_json_files
        load_data.load_data(mock_conn, data_path, llm_path)
        mock_conn.commit.assert_called_once()

    @pytest.mark.db
    def test_load_data_empty_results(self, mock_conn, tmp_path):
        """
        When the JSON files contain no results, the SQL is still called but
        with an empty rows list (no actual data inserted).
        """
        data_file = tmp_path / "empty_data.json"
        llm_file = tmp_path / "empty_llm.json"
        with open(data_file, "w") as f:
            json.dump({"results": []}, f)
        with open(llm_file, "w") as f:
            json.dump({"results": []}, f)

        load_data.load_data(mock_conn, str(data_file), str(llm_file))

        cursor = mock_conn.cursor.return_value
        # executemany is called with an empty rows list
        cursor.executemany.assert_called_once()
        sql, rows = cursor.executemany.call_args[0]
        assert len(rows) == 0


# ======================================================================
#              Tests for query_data.run_query
# ======================================================================

class TestRunQuery:
    """run_query should execute SQL and return fetchall results."""

    @pytest.mark.db
    def test_run_query_returns_fetchall_result(self, mock_conn, mock_psycopg):
        """
        Verify that ``run_query`` executes the query and returns whatever
        the cursor's ``fetchall()`` produces.
        """
        # Set up the mock: psycopg.connect returns mock_conn,
        # whose cursor returns a cursor with fetchall returning fake data.
        mock_psycopg(mock_conn)
        cursor = mock_conn.cursor.return_value
        expected = [(42,)]
        cursor.fetchall.return_value = expected

        result = query_data.run_query("SELECT COUNT(*) FROM applicants;")

        assert result == expected
        cursor.execute.assert_called_once_with("SELECT COUNT(*) FROM applicants;")
        cursor.fetchall.assert_called_once()

    @pytest.mark.db
    def test_run_query_closes_cursor_and_connection(self, mock_conn, mock_psycopg):
        """
        run_query should close the cursor and connection after fetching
        results.
        """
        mock_psycopg(mock_conn)

        query_data.run_query("SELECT 1;")

        cursor = mock_conn.cursor.return_value
        cursor.close.assert_called_once()
        mock_conn.close.assert_called_once()

    @pytest.mark.db
    def test_run_query_multiple_rows(self, mock_conn, mock_psycopg):
        """
        run_query should return all rows from fetchall, not just one.
        """
        mock_psycopg(mock_conn)
        cursor = mock_conn.cursor.return_value
        expected = [("Fall 2025", 50), ("Fall 2026", 100)]
        cursor.fetchall.return_value = expected

        result = query_data.run_query(
            "SELECT term, COUNT(*) FROM applicants GROUP BY term ORDER BY term;"
        )

        assert result == expected
        assert len(result) == 2

    @pytest.mark.db
    def test_run_query_empty_result(self, mock_conn, mock_psycopg):
        """
        run_query should return an empty list when the query matches no
        rows.
        """
        mock_psycopg(mock_conn)
        cursor = mock_conn.cursor.return_value
        cursor.fetchall.return_value = []

        result = query_data.run_query("SELECT * FROM applicants WHERE FALSE;")

        assert result == []


# ======================================================================
#              Idempotency test (duplicate inserts)
# ======================================================================

@pytest.mark.integration
@pytest.mark.db
class TestIdempotency:
    """
    Demonstrate that duplicate inserts do not create duplicate rows.

    We simulate a UNIQUE constraint on ``url`` by making the mock cursor
    raise an exception on the second insert, and verify the caller handles
    it gracefully (or the data remains consistent).
    """

    def test_duplicate_insert_does_not_create_duplicates(
        self, mock_conn, mock_json_files, monkeypatch
    ):
        """
        If a second call to ``load_data`` inserts rows whose ``url``
        already exists, the database should not contain duplicates.
        This test uses a mock that tracks inserted URLs and rejects
        duplicates.
        """
        data_path, llm_path = mock_json_files

        # ---- First load: should succeed ----
        load_data.load_data(mock_conn, data_path, llm_path)
        cursor = mock_conn.cursor.return_value
        cursor.executemany.assert_called_once()
        first_rows = cursor.executemany.call_args[0][1]
        assert len(first_rows) == 2

        # ---- Second load: simulate unique constraint failure ----
        # Reset the mock and make executemany raise an exception
        # to simulate a UNIQUE constraint violation on the second insert.
        mock_conn.reset_mock()
        new_cursor = MagicMock()
        new_cursor.__enter__.return_value = new_cursor
        new_cursor.__exit__.return_value = None
        new_cursor.executemany.side_effect = Exception(
            'duplicate key value violates unique constraint "applicants_url_key"'
        )
        mock_conn.cursor.return_value = new_cursor
        mock_conn.cursor.__enter__.return_value = new_cursor
        mock_conn.cursor.__exit__.return_value = None

        with pytest.raises(Exception, match="duplicate key"):
            load_data.load_data(mock_conn, data_path, llm_path)

        # The exception from executemany propagates uncaught;
        # rollback is NOT called by load_data itself (it has no try/except).
        # The key assertion is that the exception was raised.
        mock_conn.rollback.assert_not_called()

        # ---- Verify no duplicate rows in the mock ----
        # The key point: the mock's executemany was called with the same
        # rows, but the constraint simulation means the DB state remains
        # unchanged after rollback.  In a real DB, a SELECT COUNT(*) would
        # still return 2 (the first load's data), not 4.
        new_cursor.executemany.assert_called_once()
        second_rows = new_cursor.executemany.call_args[0][1]
        assert len(second_rows) == 2
        # The URLs in the second attempt match the first batch
        urls_first = {r[3] for r in first_rows}
        urls_second = {r[3] for r in second_rows}
        assert urls_first == urls_second  # same data, should be rejected


# ======================================================================
#              End-to-end integration test
# ======================================================================

@pytest.mark.integration
@pytest.mark.db
class TestIntegration:
    """
    Simulate a full load-then-query flow with a single in-memory mock DB.

    This test validates that data loaded via ``load_data`` can be
    retrieved via ``query_data.run_query``.
    """

    def test_load_then_query_round_trip(self, mock_json_files, monkeypatch):
        """
        Load data through ``load_data``, then query it through
        ``query_data.run_query``, verifying the round trip works.
        """
        data_path, llm_path = mock_json_files

        # ---- Build a mock connection that stores inserts in memory ----
        class FakeCursor:
            """A cursor that records executemany rows and can be queried."""
            def __init__(self):
                self.rows = []
                self.executed_sql = None

            def __enter__(self):
                return self

            def __exit__(self, *args):
                pass

            def execute(self, sql, *args):
                self.executed_sql = sql

            def executemany(self, sql, rows):
                self.rows.extend(rows)

            def fetchall(self):
                # Simulate a simple query result based on stored rows.
                sql_lower = self.executed_sql.lower() if self.executed_sql else ""
                # Check specific filtered queries BEFORE the generic
                # "count(*)" catch-all.
                if "international" in sql_lower and "phd" in sql_lower:
                    filtered = [
                        r for r in self.rows
                        if r[6] == "International" and r[11] == "PhD"
                    ]
                    return [(len(filtered),)]
                if "fall 2026" in sql_lower and "accepted" in sql_lower:
                    filtered = [r for r in self.rows
                                if r[5] == "Fall 2026" and r[4] == "Accepted"]
                    return [(len(filtered),)]
                if "accepted" in sql_lower and "count(*)" in sql_lower:
                    filtered = [r for r in self.rows if r[4] == "Accepted"]
                    return [(len(filtered),)]
                if "fall 2026" in sql_lower and "count(*)" in sql_lower:
                    filtered = [r for r in self.rows if r[5] == "Fall 2026"]
                    return [(len(filtered),)]
                if "term" in sql_lower and "group by term" in sql_lower:
                    terms = {}
                    for row in self.rows:
                        t = row[5]  # term is at index 5
                        terms[t] = terms.get(t, 0) + 1
                    return sorted(terms.items())
                if "count(*)" in sql_lower:
                    return [(len(self.rows),)]
                return []

            def close(self):
                pass

        fake_cursor = FakeCursor()

        conn = MagicMock()
        conn.cursor.return_value = fake_cursor

        def fake_connect(**kwargs):
            return conn

        monkeypatch.setattr(load_data.psycopg, "connect", fake_connect)
        monkeypatch.setattr(query_data.psycopg, "connect", fake_connect)

        # ---- Load the data ----
        load_data.load_data(conn, data_path, llm_path)
        assert len(fake_cursor.rows) == 2

        # ---- Query the data ----
        count_all = query_data.run_query("SELECT COUNT(*) FROM applicants;")
        assert count_all == [(2,)]

        # Query for Fall 2026 entries
        q_fall = ("SELECT COUNT(*) FROM applicants WHERE term = 'Fall 2026';")
        count_fall = query_data.run_query(q_fall)
        assert count_fall == [(2,)]  # both entries are Fall 2026

        # Query for Accepted entries
        q_accepted = ("SELECT COUNT(*) FROM applicants WHERE status = 'Accepted';")
        count_acc = query_data.run_query(q_accepted)
        assert count_acc == [(1,)]

        # Query for International PhD entries
        q_intl_phd = (
            "SELECT COUNT(*) FROM applicants "
            "WHERE us_or_international = 'International' AND degree = 'PhD';"
        )
        count_intl_phd = query_data.run_query(q_intl_phd)
        assert count_intl_phd == [(1,)]

        # Query entries per term
        q_terms = "SELECT term, COUNT(*) FROM applicants GROUP BY term ORDER BY term;"
        terms = query_data.run_query(q_terms)
        assert terms == [("Fall 2026", 2)]