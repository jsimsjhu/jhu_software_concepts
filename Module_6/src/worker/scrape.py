"""
GradCafe Applicant Data Scraper
Extracts program name, university, status, date added, result URL, comments,
semester, international status, GRE scores, GPA, and more from
The GradCafe survey/search results using Selenium and BeautifulSoup.
Handles pagination and saves results as JSON.
"""

import json
import time
import re
import traceback
from datetime import datetime
from urllib.parse import urljoin, quote

import random
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup

# ──────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────
BASE_URL = "https://www.thegradcafe.com"
SEARCH_URL = "https://www.thegradcafe.com/survey"

# Column indices (0-based)
COL_SCHOOL = 0
COL_PROGRAM = 1
COL_ADDED_ON = 2
COL_STATUS = 3
COL_ACTIONS = 4


def setup_driver(headless=True):
    """Configure and return a Chrome WebDriver."""
    options = Options()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    driver = webdriver.Chrome(options=options)
    driver.execute_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    )
    return driver


def parse_status_badge_desktop(cell):
    """Parse the desktop status column (column 3)."""
    text = cell.get_text(strip=True)
    match = re.search(r"(.+?)\s+on\s+(.+)$", text)
    if match:
        return {
            "acceptance_status": match.group(1).strip(),
            "decision_date": match.group(2).strip(),
            "decision_date_raw": text,
        }
    return {
        "acceptance_status": text if text else None,
        "decision_date": None,
        "decision_date_raw": text,
    }


def parse_detail_badges(detail_cell):
    """Parse the detail row badges."""
    result = {
        "term": None,
        "applicant_type": None,
        "gpa": None,
        "gre_quant": None,
        "gre_verbal": None,
        "gre_aw": None,
        "other_badges": [],
    }

    badge_divs = detail_cell.find_all(
        "div", class_=re.compile(r"inline-flex.*rounded-md")
    )
    for div in badge_divs:
        text = div.get_text(strip=True)
        if not text:
            continue

        # Term badge: "Fall 2026", "Spring 2027", "Summer 2026"
        if re.match(r"^(Fall|Spring|Summer)\s+\d{4}$", text, re.I):
            result["term"] = text
            continue

        # International/American badge
        if text in ("International", "American", "Domestic"):
            result["applicant_type"] = text
            continue

        # GPA badge: "GPA 3.50"
        gpa_match = re.match(r"^GPA\s+([\d.]+)$", text, re.I)
        if gpa_match:
            result["gpa"] = gpa_match.group(1)
            continue

        # GRE scores
        gre_q_match = re.match(r"^GRE\s+Q\s+([\d.]+)$", text, re.I)
        gre_nosuffix_match = re.match(r"^GRE\s+([\d.]+)$", text, re.I)
        gre_v_match = re.match(r"^GRE\s+V\s+([\d.]+)$", text, re.I)
        gre_aw_match = re.match(r"^GRE\s+AW\s+([\d.]+)$", text, re.I)
        if gre_q_match:
            result["gre_quant"] = gre_q_match.group(1)
            continue
        if gre_nosuffix_match:
            result["gre_quant"] = gre_nosuffix_match.group(1)
            continue
        if gre_v_match:
            result["gre_verbal"] = gre_v_match.group(1)
            continue
        if gre_aw_match:
            result["gre_aw"] = gre_aw_match.group(1)
            continue

        # Any other badge we didn't match
        result["other_badges"].append(text)

    return result


def parse_comments(comment_cell):
    """Parse the optional second detail row that contains applicant comments."""
    p_tag = comment_cell.find("p")
    if p_tag:
        text = p_tag.get_text(strip=True)
        return text if text else None
    return None


def parse_data_row(row):
    """Parse a data <tr> that has 5 <td> cells."""
    cells = row.find_all("td")
    if len(cells) < 5:
        return None

    record = {}

    # ── Column 0: School / University ──
    col0 = cells[COL_SCHOOL]
    school_div = col0.find("div", class_=re.compile(r"font-medium"))
    record["university"] = (
        school_div.get_text(strip=True) if school_div else col0.get_text(strip=True)
    )

    # ── Column 1: Program name + Degree ──
    col1 = cells[COL_PROGRAM]
    spans = col1.find_all("span")
    record["program"] = spans[0].get_text(strip=True) if spans else col1.get_text(strip=True)
    record["degree"] = spans[-1].get_text(strip=True) if len(spans) > 1 else ""

    # ── Column 2: Added On date ──
    record["added_on"] = cells[COL_ADDED_ON].get_text(strip=True)

    # ── Column 3: Desktop status badge ──
    status_info = parse_status_badge_desktop(cells[COL_STATUS])
    record.update(status_info)

    # ── Column 4: Actions column — extract result URL ──
    col4 = cells[COL_ACTIONS]
    result_link = col4.find("a", href=re.compile(r"/result/"))
    if result_link:
        record["result_url"] = urljoin(BASE_URL, result_link.get("href", ""))
        record["result_id"] = result_link.get("href", "").replace("/result/", "")
    else:
        record["result_url"] = None
        record["result_id"] = None

    return record


def attach_detail_to_record(records, cells):
    """Parse badge info and comments from a detail row."""
    if not records:  # pragma: no cover
        return

    badge_info = parse_detail_badges(cells[0])
    comments = parse_comments(cells[0])

    has_badges = any(
        v is not None for v in badge_info.values()
        if not isinstance(v, list)
    ) or len(badge_info.get("other_badges", [])) > 0

    if has_badges:
        for k, v in badge_info.items():
            if v and k not in records[-1] or not records[-1].get(k):
                if k == "other_badges":
                    continue
                records[-1][k] = v
    if comments:
        records[-1]["comments"] = comments


def extract_page_results(driver):
    """Extract all result entries from the current page using BeautifulSoup."""
    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")

    table = soup.find("table", class_=re.compile(r"tw-min-w-full|tw-divide-y"))
    if not table:
        print("WARNING: Could not find results table on page.")
        return []

    rows = table.find_all("tr")
    records = []

    i = 0
    while i < len(rows):
        row = rows[i]
        cells = row.find_all("td")

        if not cells:
            i += 1
            continue

        is_detail = any(cell.get("colspan") == "100%" for cell in cells)

        if is_detail:
            attach_detail_to_record(records, cells)
            i += 1
            continue

        record = parse_data_row(row)
        if record:
            records.append(record)
        i += 1

    return records


def polite_delay(page_count):
    """Sleep for a random polite delay between page requests."""
    if page_count > 1:
        delay = random.uniform(1.0, 3.0)
        print(f"  Polite delay: {delay:.1f}s...")
        time.sleep(delay)


def wait_for_table(driver):
    """Wait for the results table to be present on the page."""
    try:
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "table.tw-min-w-full")
            )
        )
    except TimeoutException:
        print("  Timed out waiting for table. Waiting extra...")
        time.sleep(8)
        if not driver.find_elements(By.TAG_NAME, "table"):
            print("  No table found. Site may have changed.")
            return False
    return True


def print_page_header(page_count, current_url):
    """Print a formatted page header."""
    print(f"\n{'='*60}")
    print(f"  Page {page_count}")
    print(f"{'='*60}")
    print(f"  Loading: {current_url}")


def process_single_page(driver, page_count, current_url, all_records, max_pages):
    """Fetch and process a single page."""
    polite_delay(page_count)
    print_page_header(page_count, current_url)

    try:
        driver.get(current_url)
    except Exception:  # pylint: disable=broad-exception-caught
        return None

    if not wait_for_table(driver):
        return None

    time.sleep(2)

    print(f"  Title: {driver.title[:80]}")
    print(f"  URL: {driver.current_url[:100]}")

    page_records = extract_page_results(driver)
    print(f"  Records found: {len(page_records)}")

    all_records.extend(page_records)

    if max_pages and page_count >= max_pages:
        print(f"\n  Reached max pages ({max_pages}). Stopping.")
        return None

    next_url = get_next_page_url(driver)
    if next_url and next_url != current_url and next_url != driver.current_url:
        return next_url

    print("\n  No next page found. Scraping complete.")
    return None


def _find_next_by_text(driver):
    """Find next page via text/aria-label links."""
    next_links = driver.find_elements(
        By.XPATH,
        "//a[contains(translate(text(), 'NEXT', 'next'), 'next') "
        "or contains(@aria-label, 'Next') "
        "or contains(@aria-label, 'next')]"
    )
    for link in next_links:
        href = link.get_attribute("href")
        if href:
            return href
    return None


def _find_next_by_pagination(driver):
    """Find next page via pagination nav."""
    pagination = driver.find_elements(
        By.CSS_SELECTOR, "nav[aria-label='Pagination']"
    )
    if not pagination:
        return None
    page_links = pagination[0].find_elements(By.TAG_NAME, "a")
    for j, link in enumerate(page_links):
        parent_class = (
            link.find_element(By.XPATH, "..").get_attribute("class") or ""
        )
        if ("current" in parent_class or "active" in parent_class):
            if j + 1 < len(page_links):
                next_href = page_links[j + 1].get_attribute("href")
                if next_href:
                    return next_href
    return None  # pragma: no cover


def _find_next_by_rel(driver):
    """Find next page via rel='next' links."""
    rel_next = driver.find_elements(
        By.CSS_SELECTOR, "a[rel='next'], link[rel='next']"
    )
    for link in rel_next:
        href = link.get_attribute("href")
        if href:
            return href
    return None


def get_next_page_url(driver):
    """Find the 'Next' page link on the current page."""
    try:
        return (
            _find_next_by_text(driver)
            or _find_next_by_pagination(driver)
            or _find_next_by_rel(driver)
        )
    except (TimeoutException, ValueError, AttributeError, Exception):  # pylint: disable=broad-exception-caught
        return None


def save_results(output_file, output):
    """Save scraped results to a JSON file."""
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)


def print_summary(page_count, all_records, output_file):
    """Print a summary of the scraping run."""
    print(f"\n{'='*60}")
    print("  SCRAPING COMPLETE")
    print(f"{'='*60}")
    print(f"  Pages scraped:  {page_count}")
    print(f"  Total records:  {len(all_records)}")
    print(f"  Output file:    {output_file}")
    print(f"{'='*60}")


def scrape_gradcafe(
    search_query="computer science",
    max_pages=1500,
    output_file="applicant_data.json",
    headless=True,
):
    """Main scraping function for The GradCafe."""
    driver = setup_driver(headless=headless)
    all_records = []
    page_count = 0

    encoded_query = quote(search_query)
    current_url = f"{SEARCH_URL}?q={encoded_query}&sort=newest"

    try:
        while current_url:
            page_count += 1
            next_url = process_single_page(driver, page_count, current_url,
                                           all_records, max_pages)
            if next_url is None:
                break
            current_url = next_url

    except KeyboardInterrupt:
        print("\n\nInterrupted. Saving current results...")
    except (TimeoutException, ConnectionError, OSError) as e:  # pragma: no cover
        print(f"\nError: {e}")  # pragma: no cover
        traceback.print_exc()  # pragma: no cover

    finally:
        driver.quit()

    output = {
        "meta": {
            "search_query": search_query,
            "pages_scraped": page_count,
            "total_records": len(all_records),
            "scraped_at": datetime.now().isoformat(),
            "source_url": SEARCH_URL,
        },
        "results": all_records,
    }

    save_results(output_file, output)
    print_summary(page_count, all_records, output_file)

    return all_records


# ──────────────────────────────────────────────
# CLI Entry Point
# ──────────────────────────────────────────────
if __name__ == "__main__":  # pragma: no cover
    import argparse

    parser = argparse.ArgumentParser(
        description="Scrape applicant/grad school data from The GradCafe",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-q", "--query",
        default="computer science",
        help="Search query (default: 'computer science')",
    )
    parser.add_argument(
        "-p", "--pages",
        type=int,
        default=1500,
        help="Maximum pages to scrape (default: 1500, 0 = unlimited)",
    )
    parser.add_argument(
        "-o", "--output",
        default="gradcafe_results.json",
        help="Output JSON file path (default: gradcafe_results.json)",
    )
    parser.add_argument(
        "--no-headless",
        action="store_true",
        help="Run browser in visible mode (not headless)",
    )

    args = parser.parse_args()

    print("╔══════════════════════════════════════════╗")
    print("║     GradCafe Applicant Data Scraper      ║")
    print("╚══════════════════════════════════════════╝")
    print(f"  Query:      {args.query}")
    print(f"  Max pages:  {args.pages if args.pages else 'unlimited'}")
    print(f"  Output:     {args.output}")
    print(f"  Headless:   {not args.no_headless}")
    print()

    scrape_gradcafe(
        search_query=args.query,
        max_pages=args.pages,
        output_file=args.output,
        headless=not args.no_headless,
    )
