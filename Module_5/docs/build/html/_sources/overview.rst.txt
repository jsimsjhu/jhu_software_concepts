========
Overview
========

The **GradCafe Applicant Analysis** application scrapes graduate-school
application data from The GradCafe, loads the results into a PostgreSQL
database, and presents 10 analytical queries via a Flask web interface.

--------------
Setup
--------------

Prerequisites
=============

* Python 3.13+
* PostgreSQL 16+
* ``pip`` (Python package installer)

Installation
============

1. Clone the repository and navigate to the Module_4 directory::

     git clone <repository-url>
     cd jhu_software_concepts/Module_4

2. Create and activate a virtual environment::

     python -m venv venv
     venv\Scripts\activate        # Windows
     source venv/bin/activate     # macOS / Linux

3. Install dependencies::

     pip install -r requirements.txt

4. Ensure PostgreSQL is running and the ``applicants`` table exists.
   You can create the table by running::

     python -c "from src.load_data import create_table; import psycopg; conn = psycopg.connect('postgresql://postgres:postgres@localhost/postgres'); create_table(conn); conn.close()"

-----------------------
Environment Variables
-----------------------

================================ ====================================================
Variable                         Description
================================ ====================================================
``DATABASE_URL``                 PostgreSQL connection string.
                                 Default: ``postgresql://postgres:postgres@localhost/postgres``
================================ ====================================================

.. tip::
   Set the environment variable before running the app to point at a
   different database::

     set DATABASE_URL=postgresql://user:password@host/dbname

-------------------------
Running the Application
-------------------------

Start the Flask development server::

    python src/app.py

The app will be available at http://127.0.0.1:5000/.

-------------------
Running the Tests
-------------------

All tests are written with **pytest** and use **monkeypatch** to mock
databases, network calls, and Selenium::

    python -m pytest tests/

To run tests with coverage::

    python -m pytest tests/ --cov=src --cov-report=term-missing

----------------
Project Layout
----------------

::

    Module_4/
    ├── src/
    │   ├── app.py                 # Flask application with create_app() factory
    │   ├── scrape.py              # GradCafe web scraper (Selenium + BeautifulSoup)
    │   ├── load_data.py           # DDL & data loading utilities
    │   ├── query_data.py          # 10 analytical SQL queries
    │   ├── templates/
    │   │   ├── index.html         # Main page template
    │   │   └── _results.html      # Results partial (dynamically loaded)
    │   └── static/
    ├── tests/
    │   ├── test_app.py            # Factory & basic route tests
    │   ├── test_app_comprehensive.py  # Comprehensive app coverage tests
    │   ├── test_buttons.py        # Button endpoint tests (BUSY flag)
    │   ├── test_db.py             # Database-layer tests (mocked psycopg)
    │   ├── test_flask_page.py     # Page rendering tests
    │   └── test_scrape.py         # Scraper tests (mocked Selenium)
    ├── docs/
    │   ├── source/                # Sphinx documentation source
    │   │   ├── conf.py
    │   │   ├── index.rst
    │   │   ├── overview.rst
    │   │   ├── architecture.rst
    │   │   ├── api.rst
    │   │   └── testing.rst
    │   └── Makefile               # Sphinx build commands
    └── requirements.txt