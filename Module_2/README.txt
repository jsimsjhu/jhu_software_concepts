Name: Justen Sims
Module: Module 2 - Web Scraping
Assignment: Web Scraping - Grad Cafe Data
Due Date: 5/31/2026

Approach:
This scraper uses Selenium with ChromeDriver to load Grad Cafe survey results for "computer science".
It navigates through paginated pages, extracts applicant data using BeautifulSoup and CSS selectors,
and saves the results to applicant_data.json with the following fields per record:
  - university, program, degree, added_on
  - acceptance_status, decision_date
  - result_url, result_id
  - term, applicant_type (International/American)
  - gpa, gre_quant, gre_verbal, gre_aw
  - comments (free-text applicant narratives)

The scraper implements:
- Headless browsing for efficiency
- Random delays between page requests (1-3 seconds) to be polite to the server
- Capable of scraping up to 1500 pages (~30,000 records)
- Handles missing fields by storing null/None
- GRE scores correctly parsed from badge formats: "GRE 168", "GRE V 160", "GRE AW 4.00"

robots.txt:
The GradCafe robots.txt was checked before development. Save your robots.txt screenshot as:
  Module_2/robots.txt.png

To run:
1. Install dependencies: pip install selenium beautifulsoup4
2. Run the scraper:   python scrape.py
3. Output: applicant_data.json

LLM Cleaning:
After scraping, clean the data using the provided LLM cleaner:
  python clean.py
This runs llm_hosting/app.py on applicant_data.json and produces:
  llm_extend_applicant_data.json

Known Issues:
- GRE scores are only available when the applicant includes them in their post badges.
- Some edge cases in date parsing may produce inconsistent formats.