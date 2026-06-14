============
Architecture
============

The application is structured in three layers: **Web**, **ETL**, and
**Database**.  The ``create_app()`` factory function assembles them into
a single Flask instance.

.. figure:: _static/diagram.png
   :align: center
   :width: 80%

   *High-level architecture diagram (placeholder)*

---------
Web Layer
---------

``src/app.py`` — Flask application with the ``create_app()`` factory.

* **Factory pattern**: ``create_app(test_config=None)`` returns a
  configured ``Flask`` instance.  The optional ``test_config`` dict
  overrides settings such as ``TESTING`` and ``DATABASE_URL``.
* **Routes**:

  ======================= ====== ==========================================
  Route                   Method Description
  ======================= ====== ==========================================
  ``/``, ``/analysis``    GET    Main page — runs all 10 queries and
                                 renders results
  ``/pull_data``,         POST   Starts a background thread to scrape new
  ``/pull-data``                 data from The GradCafe
  ``/update_analysis``,   POST   Re-runs all 10 queries and returns fresh
  ``/update-analysis``           rendered HTML
  ``/scrape_status``      GET    Returns the current scrape state as JSON
  ======================= ====== ==========================================

* **Thread safety**: A ``threading.Lock`` prevents concurrent scrape
  operations.  The ``BUSY`` config flag can simulate an in-progress
  scrape for testing.

---------
ETL Layer
---------

Two modules handle the extract-transform-load pipeline:

``src/scrape.py``
=================

A Selenium-based scraper that:

1. Opens a headless Chrome browser (via ``webdriver.Chrome``).
2. Navigates the GradCafe search results, paginating through pages.
3. Parses each result row using BeautifulSoup, extracting university,
   program, degree, status, date, GPA, GRE scores, and comments.
4. Writes the results as a JSON file.

Key functions:

* ``setup_driver(headless=True)`` — configure and return a Chrome driver.
* ``extract_page_results(driver)`` — parse the current page's table into
  a list of record dicts.
* ``get_next_page_url(driver)`` — find the "Next" pagination link.
* ``scrape_gradcafe(search_query, max_pages, output_file, headless)`` —
  main entry point.

``src/load_data.py``
====================

Loads scraped JSON data into PostgreSQL:

* ``create_table(conn)`` — drops and recreates the ``applicants`` table.
* ``load_data(conn, data_file, llm_file)`` — reads JSON files, merges
  LLM-extended fields, and inserts rows via ``executemany``.

``src/query_data.py``
=====================

Contains the ``run_query(query)`` helper and the 10 analytical SQL
queries used by the web interface.

-----------
DB Layer
-----------

The database schema (``applicants`` table) stores fields such as:

* ``program``, ``comments``, ``date_added``, ``url``
* ``status``, ``term``, ``us_or_international``
* ``gpa``, ``gre``, ``gre_v``, ``gre_aw``
* ``degree``, ``llm_generated_program``, ``llm_generated_university``

The ``DATABASE_URL`` environment variable controls the connection.  When
set to ``None`` (testing mode), the application gracefully degrades
without attempting real database queries.