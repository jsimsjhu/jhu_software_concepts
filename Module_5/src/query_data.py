# pylint: disable=missing-final-newline, trailing-newlines
"""Run analytical queries on GradCafe data."""
# pylint: disable=no-member

import psycopg

# pylint: disable=duplicate-code
from db_helpers import DB_NAME, DB_USER, DB_PASSWORD, DB_HOST


def run_query(query):
    """Execute a SQL query and return results."""
    conn = psycopg.connect(
        dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST
    )
    cur = conn.cursor()
    cur.execute(query)
    result = cur.fetchall()
    cur.close()
    conn.close()
    return result


# 1. How many entries applied for Fall 2026?
Q1 = "SELECT COUNT(*) FROM applicants WHERE term = 'Fall 2026';"
print("1. Fall 2026 entries:", run_query(Q1)[0][0])

# 2. Percentage of international students (to 2 decimal places)
Q2 = """
SELECT ROUND((100.0 * COUNT(CASE WHEN us_or_international = 'International' THEN 1 END) / COUNT(*))::numeric, 2)
FROM applicants;
"""
print("2. % International:", run_query(Q2)[0][0])

# 3. Average GPA, GRE, GRE V, GRE AW (where provided)
Q3 = """
SELECT
    ROUND(AVG(gpa)::numeric, 2),
    ROUND(AVG(gre)::numeric, 2),
    ROUND(AVG(gre_v)::numeric, 2),
    ROUND(AVG(gre_aw)::numeric, 2)
FROM applicants
WHERE gpa IS NOT NULL OR gre IS NOT NULL OR gre_v IS NOT NULL OR gre_aw IS NOT NULL;
"""
result3 = run_query(Q3)[0]
print("3. Avg GPA, GRE, GRE V, GRE AW:", result3)

# 4. Average GPA of American students in Fall 2026
Q4 = """
SELECT ROUND(AVG(gpa)::numeric, 2)
FROM applicants
WHERE us_or_international = 'American' AND term = 'Fall 2026';
"""
print("4. Avg GPA (American, Fall 2026):", run_query(Q4)[0][0])

# 5. Percentage of acceptances for Fall 2026
Q5 = """
SELECT ROUND((100.0 * COUNT(CASE WHEN status = 'Accepted' THEN 1 END) / COUNT(*))::numeric, 2)
FROM applicants
WHERE term = 'Fall 2026';
"""
print("5. % Acceptances (Fall 2026):", run_query(Q5)[0][0])

# 6. Average GPA of Fall 2026 acceptances
Q6 = """
SELECT ROUND(AVG(gpa)::numeric, 2)
FROM applicants
WHERE term = 'Fall 2026' AND status = 'Accepted';
"""
print("6. Avg GPA (Accepted, Fall 2026):", run_query(Q6)[0][0])

# 7. JHU masters in CS
Q7 = """
SELECT COUNT(*)
FROM applicants
WHERE llm_generated_university ILIKE '%Johns Hopkins%'
  AND degree = 'Masters'
  AND program ILIKE '%Computer Science%';
"""
print("7. JHU Masters in CS:", run_query(Q7)[0][0])

# 8. 2026 acceptances to Georgetown, MIT, Stanford, CMU for PhD in CS
Q8 = """
SELECT COUNT(*)
FROM applicants
WHERE term = 'Fall 2026'
  AND status = 'Accepted'
  AND degree = 'PhD'
  AND llm_generated_university IN ('Georgetown University', 'MIT', 'Stanford University', 'Carnegie Mellon University')
  AND program ILIKE '%Computer Science%';
"""
print(
    "8. Acceptances (Georgetown, MIT, Stanford, CMU) for PhD in CS:",
    run_query(Q8)[0][0],
)

# 9. Two of your own questions (example)
Q9 = """
SELECT COUNT(*)
FROM applicants
WHERE us_or_international = 'International' AND degree = 'PhD';
"""
print("9. International PhD applicants:", run_query(Q9)[0][0])

Q10 = """
SELECT term, COUNT(*) FROM applicants GROUP BY term ORDER BY term;
"""
print("10. Entries per term:")
for row in run_query(Q10):
    print(f"    {row[0]}: {row[1]}")  # pragma: no cover
