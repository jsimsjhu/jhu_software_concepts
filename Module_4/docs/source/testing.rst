=============
Testing Guide
=============

The test suite uses **pytest** with extensive **monkeypatch**-based mocking
to run entirely without a real PostgreSQL database or Selenium browser.

--------------
Running Tests
--------------

Run the full suite::

    python -m pytest tests/

Run with coverage::

    python -m pytest tests/ --cov=src --cov-report=term-missing

Run a specific test file::

    python -m pytest tests/test_db.py -v

---------------------------
Test Markers (Tags)
---------------------------

Each test is tagged with one or more markers so you can run targeted
subsets::

    # Web page / route tests
    python -m pytest -m "web"

    # Button endpoint behavior
    python -m pytest -m "buttons"

    # Analysis / formatting tests
    python -m pytest -m "analysis"

    # Database-layer tests (schema, inserts, queries)
    python -m pytest -m "db"

    # End-to-end integration tests
    python -m pytest -m "integration"

    # Combined: all database-related tests
    python -m pytest -m "db or integration"

    # All tests except integration
    python -m pytest -m "not integration"

====================== ======================================================
Marker                 Description
====================== ======================================================
``web``                Flask route / page-rendering tests
``buttons``            ``pull_data()`` / ``update_analysis()`` behavior
``analysis``           Query results formatting and output
``db``                 Database schema, inserts, and select tests
``integration``        End-to-end load-then-query flows
====================== ======================================================

--------------
Test Selectors
--------------

Front-end tests use ``data-testid`` attributes for reliable element
selection instead of fragile CSS classes or XPath::

    <button data-testid="pull-data-btn">Pull Data</button>
    <button data-testid="update-analysis-btn">Update Analysis</button>

In your tests, select these elements with::

    driver.find_element(By.CSS_SELECTOR, "[data-testid='pull-data-btn']")
    driver.find_element(By.CSS_SELECTOR, "[data-testid='update-analysis-btn']")

Or in Playwright / Selenium::

    page.locator("[data-testid='pull-data-btn']").click()

--------------
Test Fixtures
--------------

``mock_conn``
=============

Returns a ``MagicMock`` that substitutes for a ``psycopg`` connection.
The mock's cursor supports the context-manager protocol so that
``with conn.cursor() as cur:`` works correctly.

``busy_client``
===============

Creates a Flask test client with ``BUSY=True`` in the app config,
simulating an in-progress data pull without actually running the
scraper.

``mock_json_files``
===================

Creates temporary ``applicant_data.json`` and
``llm_extend_applicant_data.json`` files with known test data and
returns their paths.

----------------------------
Mocking Strategy Summary
----------------------------

+---------------------------+----------------------------------------------+
| Dependency                | How It's Mocked                              |
+===========================+==============================================+
| PostgreSQL (``psycopg``)  | ``sys.modules["psycopg"] = MagicMock()`` at  |
|                           | import time.  ``connect()`` returns a mock   |
|                           | connection with a context-manager cursor.    |
+---------------------------+----------------------------------------------+
| Selenium WebDriver        | ``FakeDriver`` class with stubbed            |
|                           | ``page_source``, ``get``, ``quit``,          |
|                           | ``find_elements``, ``find_element``.         |
+---------------------------+----------------------------------------------+
| ``WebDriverWait``         | ``FakeWait`` class whose ``until()`` returns |
|                           | immediately (no real timeout).               |
+---------------------------+----------------------------------------------+
| ``time.sleep``            | Replaced with ``lambda s: None`` (no-op).    |
+---------------------------+----------------------------------------------+
| GradCafe HTML             | Static HTML strings served via               |
|                           | ``FakeDriver.page_source``.                  |
+---------------------------+----------------------------------------------+
| ``DATABASE_URL``          | Set to ``None`` or a mock URL via            |
|                           | ``test_config``.                             |
+---------------------------+----------------------------------------------+