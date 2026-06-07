Module 3 – Database Queries and Flask Webpage

Name: Justen Sims
Course: EN.605.256 Modern Software Concepts in Python
Module: 3

Setup Instructions:
1. Install PostgreSQL and create a database named 'postgres'
2. Update database credentials in load_data.py, query_data.py, and app.py if different from default (default: user=postgres, password=postgres, host=localhost)
3. Install dependencies: pip install -r requirements.txt
4. Load data: python load_data.py
5. Run queries: python query_data.py
6. Start Flask app: python app.py
7. Open browser to http://127.0.0.1:5000

Notes:
- Queries 7 and 8 return 0 due to absence of matching data in the dataset
- See limitations.pdf for discussion of bias and missing data

Files included:
- load_data.py : loads JSON data into PostgreSQL
- query_data.py : runs all 10 SQL queries and prints results
- app.py : Flask web application displaying results
- templates/index.html : main webpage template
- templates/_results.html : partial for dynamic updates
- static/styles.css : styling
- requirements.txt : Python dependencies
- limitations.pdf : reflection on data limitations
- console_output.png : screenshot of query_data.py output
- webpage.png : screenshot of running Flask webpage