# JHU Software Concepts — Modern Software Concepts in Python

**Student:** Justen Sims  
**Course:** EN.605.256 — Modern Software Concepts in Python  
**Term:** Summer 2026  

## Repository Overview

This repository contains all coursework, projects, and assignments completed during the Summer 2026 semester of Modern Software Concepts in Python at Johns Hopkins University. The work spans web scraping, data cleaning, SQL, Flask web development, cloud computing, data visualization, machine learning, MLOps, and neural network deployment.

## Projects Portfolio

The complete portfolio of semester projects is displayed on the personal website hosted at [your-website-url] (or localhost for development). The Projects page organizes each module with:
- Project title and overview
- Link to the GitHub folder
- Personal learning statement

Visit the portfolio at: `http://127.0.0.1:5000/projects` (when running locally)

## Corrections Log
Module 1 — Personal Website
Feedback:

No comments present in code (-1)

Screenshots PDF outside zipped folder

Correction: Added comments to pages.py; verified all deliverables (screenshots PDF) are inside the module folder.
-------------
Module 2 — JSON Output & Data Structure
Feedback:

Missing comments omitted rather than consistently set to null (-2)

No full raw listing text per record (-2)

Cleaner is deterministic parsing/normalization, not a local LLM standardizer; does not add standardized program/university fields; overwrites existing fields (-10)

No canonical list changes or LLM edge cases documented (-2)

Code uses functions but not requested scrape_data(), clean_data(), save_data(), load_data() pattern (-2)

Helper functions not private/underscore-named (-2)

robots.txt screenshot missing (-5)

Correction: Use null placeholders for missing comments; preserve raw text fields; implement requested function pattern; add _ prefix to helper functions; include robots.txt screenshot.
-------------
Module 3 — SQL Query Analysis
Feedback:

Missing explanation on query results including what each query is doing and why in submitted PDF (-3)

Would like to see committed/pushed updates frequently to GitHub (not just final upload) (-3)

Correction: Added detailed explanations for each SQL query in the write-up; committed code incrementally.
-------------
Module 4 — Test Markers and Organization
Feedback:

Only test_db.py has markers; all other test files have zero markers. Major policy violation (-3)

Missing required test files: test_analysis_format.py, test_db_insert.py, test_integration_end_to_end.py (-1)

Uses arbitrary time.sleep() for busy-state checks (prohibited) (-1)

pytest.ini defines markers but running -m only collects from test_db.py (-2)

No test validates rendered HTML formatting (e.g., two-decimal regex) (-3)

No marked test validates row insertion via HTTP POST end-to-end (-2)

No test performs GET /analysis after full pull/update cycle with HTML validation (-2)

pytest.ini markers defined but unmarked tests skip most functionality (-2)

test_app_comprehensive.py uses time.sleep() for background threads (prohibited) (-1)

CI does not include --cov-fail-under=100, so coverage drops pass (-1)

Correction: Added pytest markers to all test files; replaced time.sleep() with proper wait conditions; created missing test files; added HTML validation tests; added --cov-fail-under=100 to CI.
-------------
Module 5 — Pylint, SQL, and README
Feedback:

Pylint 10/10 earned with suppressions rather than clean code (15+ suppressions) (-5)

Raw SQL strings with embedded values: 'Fall 2026', 'International', 'American', 'Accepted', 'Masters', 'PhD' (-1)

psycopg.sql.SQL / sql.Identifier not used (-1)

src/query_data.py exposes run_query(query) accepting arbitrary SQL (-1)

Query logic duplicated between src/app.py and src/query_data.py (-1)

No LIMIT on queries (-1)

No standalone least-privilege SQL script (CREATE ROLE, GRANT) (-1)

src/db_helpers.py hardcodes DB_USER = "postgres" and DB_PASSWORD = "postgres" (-1)

src/app.py falls back to postgresql://postgres:postgres@localhost/postgres (-1)

src/load_data.py drops and recreates table from application code (-1)

src/app.py runs Flask with debug=True (-1)

CI does not provision PostgreSQL; CI does not test with restricted role (-1)

README identifies project as "Module 4 — Pytest and Sphinx" (-1)

requirements.txt uses broad lower bounds (flask>=3.0) (-1)

Folder ~90 MB due to generated artifacts (.pytest_cache, __pycache__, *.egg-info, docs/build) (-1)

coverage_summary.txt not a successful coverage report (-1)

Correction: Removed all pylint suppressions; replaced raw SQL with parameterized queries; used psycopg.sql for identifiers; added LIMIT to all queries; created least-privilege SQL script; moved credentials to environment variables; set debug=False; fixed CI to provision PostgreSQL; updated README to Module 5; pinned dependencies to exact versions; cleaned cache artifacts; verified coverage report success.
-------------
Module 6 — Docker and RabbitMQ
Feedback:

Legacy Module 3/5 structure remains; tests reference old module paths (-1)

Worker Dockerfile not portable (forced google-chrome-stable:amd64) (-2)

Required UI button paths (/pull_data, /update_analysis) bypass RabbitMQ (-5)

Submitted Compose startup did not auto-populate Postgres with applicant_data.json (-2)

README/docs do not include pullable web/worker image tags or registry links (-1)

.pylintrc ignores venv, .venv, tests, disables important checks (-1)

Submission includes generated/cached files (venv/, __pycache__, coverage artifacts) (-1)

Pytest fails with 8 import errors (missing app, src.app, load_data, scrape) (-2)

Correction: Made Dockerfile multi-architecture compatible; updated UI buttons to use /api/scrape and /api/recompute; added data population script; added Docker Hub registry links to README; updated .pylintrc; removed cache artifacts before zipping; fixed import paths in tests.
-------------
Module 7 — SageMaker and README
Feedback:

Used Studio instead of Notebook Instance (-3)

s3_fetch.py exists but notebook inlines boto3 instead of importing (-1)

Pylint .py 7.27, notebook 4.17/7.5, reusable module unused (-3)

README + Setup for EC2 very thin (-5)

Correction: Switched to Notebook Instance; moved boto3 logic to s3_fetch.py and imported it; improved README with detailed EC2 setup steps.
-------------
Module 8 — Missing Files and Invalid Values
Feedback:

Missing files: cleaned_gradcafe.json, missingness_summary.csv, summary_statistics.csv, GRE-vs-GRE-V.png, GPA-vs-GRE.png, Degree-vs-International.png, Acceptances-over-Time.png, GPA-by-Outcome.png, Numeric-Correlation-Heatmap.png (-5)

Nonstandard schema names (program, university, gpa) instead of required (Program, University, GPA) (-5)

Degree filtering used "Master's" but source uses Masters → all Master's dropped (-5)

Outcome parsing failed to preserve Waitlisted and Interviewed (-5)

Decision-date parsing unsuccessful (-5)

has_valid_gpa allowed GPA 0; has_valid_gre only required >0; invalid values (GPA 9.99, GRE 650, 670, 99.99) not filtered (-5)

application_season assigned missing months to Early Cycle (-5)

df2 used separately → inconsistent analysis (-5)

Acceptances-over-Time.png placeholder (0 accepted applicants with valid decision dates) (-5)

Summary statistics invalid due to malformed values (-5)

Reported GRE 177.95 (not valid GRE), Master's GPA 4.09 (above 4.0) (-3)

Correction: Added systematic file verification; standardized column names; standardized Masters → "Master's"; preserved all outcome categories; added stricter numeric validation (GPA 0-4.0, GRE 130-170); used one consistent dataframe; documented limitations.
-------------
Module 9 — Clustering Justification and README
Feedback:

Selected 85 clusters without clearly justifying why from elbow curve (-1)

No dataset included; non-standard naming not matching Module 8 (-2)

requirements.txt saved as UTF-16 with many unnecessary pinned packages (-1)

clustered_dataFrame.png title overlapping table rows; GRE plots missing GRE V; units/scale not explained (-5)

Correction: Added clear justification for 85 clusters; included dataset in folder; fixed requirements.txt encoding (UTF-8); improved visualization formatting and added missing GRE V with units.
-------------
Module 10 — README, Debug Mode, and Workflow
Feedback:

data/ folder empty; PNGs duplicated across assets/ and plots/; generation/serving workflow incoherent (-2)

README says Kaggle but code uses sns.load_dataset("diamonds"); no local CSV; offline loading impossible (-2)

EDA not deeply documented; no saved EDA summary; no written interpretation in README (-4)

Scatterplot extremely tall; 3D plot less clear than 2D; tight layout warning (-2)

debug=True caused sandbox/reloader failure (-2)

Dashboard depends on assets/*.png while visualization.py regenerates into plots/ (-2)

README incomplete (19 lines, stops mid-code block) (-5)

requirements.txt missing pylint and selenium (-4)

Dashboard Pylint issues: trailing whitespace, missing newline, lowercase fig3d/figbox, unused os import (-2)

Correction: Completed README with setup, embedded PNGs, EDA findings, conclusion, and limitations; set debug=False; added pylint and selenium to requirements.txt; consolidated output locations to plots/; fixed Pylint issues.
-------------
Module 11 — Perfect Score
Feedback: None — 103/100.
Correction: No changes needed. Maintained clean submission workflow.
-------------
Module 12 — Constants and Pylint
Feedback:

Used json.load instead of JSON Lines format for data loader (-1)

Required constants (HIDDEN_UNITS, LEARNING_RATE, MAX_EPOCHS, PATIENCE) used only as function defaults/arguments rather than module-level constants (-2)

Pylint 6.73/10 due to naming/style issues, trailing whitespace, missing final newline (-2)

Correction: Updated data loader to handle JSON Lines; defined required constants at module level; fixed Pylint issues.
-------------
Module 13 — Model Weights and Write-Up
Feedback:

Local model weights file only a Git LFS pointer, not actual trained weights (-1)

Tokenizer-choice explanation minimal (-1)

Submitted write-up/screenshot evidence abbreviated; interpretation surface-level (-1)

Local submitted model weights not present → reload inference cannot work from zip alone (-2)

Model load failure at app startup not handled gracefully (-1)

Write-up less complete/polished than rubric expects (-2)

Correction: Used Git LFS for model weights; expanded tokenizer explanation; improved write-up with deeper interpretation; added graceful error handling for model loading; made write-up more polished.

## Repository Structure
jhu_software_concepts/
├── Module_1/ # Personal website (updated for portfolio)
├── Module_2/ # Python foundations
├── Module_3/ # SQL and database queries
├── Module_4/ # Pytest and Sphinx documentation
├── Module_5/ # Flask web application
├── Module_6/ # Docker + RabbitMQ + PostgreSQL microservices
├── Module_7/ # AWS S3 + SageMaker + EC2 deployment
├── Module_8/ # Data cleaning and EDA
├── Module_9/ # K-Means clustering
├── Module_10/ # Data dashboard with Dash + Plotly
├── Module_11/ # MLOps tracking with MLflow + wandb
├── Module_12/ # Two-layer neural network from scratch
├── Module_13/ # Multimodal admissions prediction with PyTorch
└── README.md # This file

## Reflection

**Most Challenging Module:** Module 13 — Fine-tuning a transformer model and deploying it in a Flask app required integrating many concepts from throughout the semester.

**Strongest Work:** Module 12 — Implementing a neural network from scratch in NumPy demonstrated deep understanding of gradient descent and backpropagation.

**Most Improved Skills:** Python packaging, code quality (Pylint), and submission workflow.

**Understanding of Python:** Over the semester, I progressed from writing scripts to building complete, deployable systems with proper documentation, testing, and version control.
**Updates**

| Module 1 | No comments in code; screenshots PDF outside zip | Added comments to app.py and pages.py; ensured all deliverables are in the module folder |


### Module 9 — Clustering and README
**Feedback:** Elbow justification missing; dataset not included; requirements.txt UTF-16; visualization issues.
**Correction:** Added clear justification for cluster selection; included dataset in folder; fixed requirements.txt encoding; improved visualization formatting.
**Why it improves:** Makes the clustering analysis more transparent and reproducible.

### Module 10 — README and Debug Mode
**Feedback:** README incomplete; debug=True left on; output locations inconsistent.
**Correction:** Completed README with setup, visualizations, and conclusion; set debug=False; consolidated output locations to a single folder.
**Why it improves:** The project is now production-ready and self-contained.

### Module 11 — Pylint and Submission Hygiene
**Feedback:** Pylint issues; venv in submission; requirements.txt missing packages.
**Correction:** Fixed all Pylint issues; removed venv before zipping; added all required packages to requirements.txt.
**Why it improves:** The submission is clean, professional, and reproducible.

### Module 12 — Column Names
**Feedback:** Column name mismatches with dataset schema.
**Correction:** Updated code to use correct column names (gre_quant, gre_verbal, acceptance_status, degree, applicant_type).
**Why it improves:** The code now correctly reads and processes the actual dataset.

### Module 13 — Model File Size
**Feedback:** Large model file exceeded GitHub limit.
**Correction:** Used Git LFS to store model.safetensors.
**Why it improves:** The repository is now fully pushable and the model is properly versioned.