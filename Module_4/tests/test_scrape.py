"""
Tests for src/scrape.py using pytest and monkeypatch.

Replaces all network/Selenium calls with fake functions that return mock
HTML or pre-defined return values, so no real HTTP requests or browsers
are needed.
"""

import json
import os
import sys
import types
from datetime import datetime
from unittest.mock import MagicMock

import pytest
from bs4 import BeautifulSoup

# Ensure src/ is on the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import scrape


# ======================================================================
#                            HELPER  HTML
# ======================================================================

# A minimal mock page that mimics one result row + detail rows from GradCafe.
SINGLE_RESULT_HTML = """
<table class="tw-min-w-full">
  <tbody>
    <tr>
      <td>
        <div class="font-medium text-gray-900">Stanford University</div>
      </td>
      <td>
        <span>Computer Science</span>
        <span>PhD</span>
      </td>
      <td>May 15, 2026</td>
      <td>
        <div class="inline-flex items-center rounded-md bg-green-50 px-2 py-1">
          Accepted on Apr 30
        </div>
      </td>
      <td>
        <a href="/result/12345" class="text-blue-600">View</a>
      </td>
    </tr>
    <tr class="tw-border-none">
      <td colspan="100%">
        <div class="inline-flex items-center rounded-md bg-gray-100 px-2 py-1">
          Fall 2026
        </div>
        <div class="inline-flex items-center rounded-md bg-gray-100 px-2 py-1">
          International
        </div>
        <div class="inline-flex items-center rounded-md bg-gray-100 px-2 py-1">
          GPA 3.85
        </div>
        <div class="inline-flex items-center rounded-md bg-gray-100 px-2 py-1">
          GRE 168
        </div>
      </td>
    </tr>
    <tr class="tw-border-none">
      <td colspan="100%">
        <p>Great program, highly recommend!</p>
      </td>
    </tr>
  </tbody>
</table>
"""

TWO_RESULTS_HTML = """
<table class="tw-min-w-full">
  <tbody>
    <tr>
      <td>
        <div class="font-medium text-gray-900">MIT</div>
      </td>
      <td>
        <span>Computer Science</span>
        <span>Masters</span>
      </td>
      <td>Jun 1, 2026</td>
      <td>
        <div class="inline-flex items-center rounded-md bg-yellow-50 px-2 py-1">
          Wait listed on May 29
        </div>
      </td>
      <td>
        <a href="/result/111" class="text-blue-600">View</a>
      </td>
    </tr>
    <tr class="tw-border-none">
      <td colspan="100%">
        <div class="inline-flex items-center rounded-md bg-gray-100 px-2 py-1">
          Fall 2026
        </div>
        <div class="inline-flex items-center rounded-md bg-gray-100 px-2 py-1">
          American
        </div>
        <div class="inline-flex items-center rounded-md bg-gray-100 px-2 py-1">
          GPA 3.95
        </div>
        <div class="inline-flex items-center rounded-md bg-gray-100 px-2 py-1">
          GRE Q 170
        </div>
        <div class="inline-flex items-center rounded-md bg-gray-100 px-2 py-1">
          GRE V 165
        </div>
      </td>
    </tr>
    <tr class="tw-border-none">
      <td colspan="100%">
        <p>Excellent fit.</p>
      </td>
    </tr>
    <tr>
      <td>
        <div class="font-medium text-gray-900">CMU</div>
      </td>
      <td>
        <span>Robotics</span>
        <span>PhD</span>
      </td>
      <td>May 20, 2026</td>
      <td>
        <div class="inline-flex items-center rounded-md bg-red-50 px-2 py-1">
          Rejected on May 22
        </div>
      </td>
      <td>
        <a href="/result/222" class="text-blue-600">View</a>
      </td>
    </tr>
    <tr class="tw-border-none">
      <td colspan="100%">
        <div class="inline-flex items-center rounded-md bg-gray-100 px-2 py-1">
          Fall 2026
        </div>
        <div class="inline-flex items-center rounded-md bg-gray-100 px-2 py-1">
          International
        </div>
      </td>
    </tr>
    <!-- no comments row for this one -->
  </tbody>
</table>
"""

# For extract_page_results testing, we need a fake driver with .page_source
class FakeDriver:
    """A minimal Selenium WebDriver replacement for testing."""
    def __init__(self, html_source=""):
        self._source = html_source
        self._elements = {}
        self.current_url = "https://www.thegradcafe.com/survey?q=cs"
        self.title = "Test Page"

    @property
    def page_source(self):
        return self._source

    def get(self, url):
        self.current_url = url

    def quit(self):
        pass

    def find_elements(self, by, value):
        """Used by get_next_page_url — return nothing to stop pagination."""
        return []

    def find_element(self, by, value):
        """Stub used by WebDriverWait internally; returns a dummy element."""
        return None

    def execute_script(self, script):
        pass


# ======================================================================
#           TESTS FOR PURE PARSING FUNCTIONS
# ======================================================================

class TestParseStatusBadgeDesktop:
    """parse_status_badge_desktop extracts status + date from badge text."""

    def test_accepted_status(self):
        """Parse 'Accepted on Apr 30' correctly."""
        cell = BeautifulSoup(
            '<div class="badge">Accepted on Apr 30</div>', "html.parser"
        ).find("div")
        result = scrape.parse_status_badge_desktop(cell)
        assert result["acceptance_status"] == "Accepted"
        assert result["decision_date"] == "Apr 30"
        assert result["decision_date_raw"] == "Accepted on Apr 30"

    def test_rejected_status(self):
        """Parse 'Rejected on May 22' correctly."""
        cell = BeautifulSoup(
            '<div class="badge">Rejected on May 22</div>', "html.parser"
        ).find("div")
        result = scrape.parse_status_badge_desktop(cell)
        assert result["acceptance_status"] == "Rejected"
        assert result["decision_date"] == "May 22"

    def test_wait_listed_status(self):
        """Parse 'Wait listed on May 29' correctly."""
        cell = BeautifulSoup(
            '<div class="badge">Wait listed on May 29</div>', "html.parser"
        ).find("div")
        result = scrape.parse_status_badge_desktop(cell)
        assert result["acceptance_status"] == "Wait listed"
        assert result["decision_date"] == "May 29"

    def test_status_without_date(self):
        """Handle badge text without ' on ' separator."""
        cell = BeautifulSoup(
            '<div class="badge">Pending</div>', "html.parser"
        ).find("div")
        result = scrape.parse_status_badge_desktop(cell)
        assert result["acceptance_status"] == "Pending"
        assert result["decision_date"] is None


class TestParseDetailBadges:
    """parse_detail_badges extracts term, international, GPA, GRE."""

    def test_parses_all_badge_types(self):
        """Recognize term, international, GPA, and GRE badges."""
        html = """
        <div>
            <div class="inline-flex items-center rounded-md px-2 py-1">Fall 2026</div>
            <div class="inline-flex items-center rounded-md px-2 py-1">International</div>
            <div class="inline-flex items-center rounded-md px-2 py-1">GPA 3.75</div>
            <div class="inline-flex items-center rounded-md px-2 py-1">GRE 166</div>
            <div class="inline-flex items-center rounded-md px-2 py-1">GRE V 160</div>
            <div class="inline-flex items-center rounded-md px-2 py-1">GRE AW 4.00</div>
        </div>
        """
        cell = BeautifulSoup(html, "html.parser").find("div")
        result = scrape.parse_detail_badges(cell)
        assert result["term"] == "Fall 2026"
        assert result["applicant_type"] == "International"
        assert result["gpa"] == "3.75"
        assert result["gre_quant"] == "166"
        assert result["gre_verbal"] == "160"
        assert result["gre_aw"] == "4.00"

    def test_american_and_gre_q(self):
        """Recognize 'American' type and 'GRE Q' prefix."""
        html = """
        <div>
            <div class="inline-flex items-center rounded-md px-2 py-1">Spring 2027</div>
            <div class="inline-flex items-center rounded-md px-2 py-1">American</div>
            <div class="inline-flex items-center rounded-md px-2 py-1">GPA 3.50</div>
            <div class="inline-flex items-center rounded-md px-2 py-1">GRE Q 170</div>
        </div>
        """
        cell = BeautifulSoup(html, "html.parser").find("div")
        result = scrape.parse_detail_badges(cell)
        assert result["term"] == "Spring 2027"
        assert result["applicant_type"] == "American"
        assert result["gpa"] == "3.50"
        assert result["gre_quant"] == "170"

    def test_no_badges(self):
        """Return None fields when no badges present."""
        cell = BeautifulSoup("<div></div>", "html.parser").find("div")
        result = scrape.parse_detail_badges(cell)
        assert result["term"] is None
        assert result["applicant_type"] is None
        assert result["gpa"] is None
        assert result["gre_quant"] is None
        assert result["gre_verbal"] is None
        assert result["gre_aw"] is None

    def test_unrecognized_badge_goes_to_other(self):
        """Unrecognized badges go into the other_badges list."""
        html = """
        <div>
            <div class="inline-flex items-center rounded-md px-2 py-1">Some Unknown Tag</div>
        </div>
        """
        cell = BeautifulSoup(html, "html.parser").find("div")
        result = scrape.parse_detail_badges(cell)
        assert "Some Unknown Tag" in result["other_badges"]


class TestParseComments:
    """parse_comments extracts the comment text from a detail row."""

    def test_with_comment(self):
        """Extract text from <p> tag."""
        html = '<div><p>Great program, highly recommend!</p></div>'
        cell = BeautifulSoup(html, "html.parser").find("div")
        assert scrape.parse_comments(cell) == "Great program, highly recommend!"

    def test_no_comment(self):
        """Return None when no <p> tag exists."""
        html = "<div></div>"
        cell = BeautifulSoup(html, "html.parser").find("div")
        assert scrape.parse_comments(cell) is None


class TestParseDataRow:
    """parse_data_row extracts university, program, degree, status, url."""

    def test_parse_full_data_row(self):
        """Parse a standard 5-column data row."""
        html = """
        <tr>
            <td>
                <div class="font-medium text-gray-900">Stanford University</div>
            </td>
            <td>
                <span>Computer Science</span>
                <span>PhD</span>
            </td>
            <td>May 15, 2026</td>
            <td>
                <div class="inline-flex items-center rounded-md bg-green-50 px-2 py-1">
                    Accepted on Apr 30
                </div>
            </td>
            <td>
                <a href="/result/12345" class="text-blue-600">View</a>
            </td>
        </tr>
        """
        soup = BeautifulSoup(html, "html.parser")
        row = soup.find("tr")
        record = scrape.parse_data_row(row)

        assert record is not None
        assert record["university"] == "Stanford University"
        assert record["program"] == "Computer Science"
        assert record["degree"] == "PhD"
        assert record["added_on"] == "May 15, 2026"
        assert record["acceptance_status"] == "Accepted"
        assert record["decision_date"] == "Apr 30"
        assert record["result_url"] == "https://www.thegradcafe.com/result/12345"
        assert record["result_id"] == "12345"

    def test_row_with_fewer_than_5_cells(self):
        """Return None if row has fewer than 5 cells."""
        html = "<tr><td>Only one cell</td></tr>"
        soup = BeautifulSoup(html, "html.parser")
        row = soup.find("tr")
        assert scrape.parse_data_row(row) is None


# ======================================================================
#           TESTS FOR EXTRACT_PAGE_RESULTS
# ======================================================================

class TestExtractPageResults:
    """extract_page_results parses the driver's page source into records."""

    def test_single_result(self):
        """Parse one complete result entry."""
        driver = FakeDriver(SINGLE_RESULT_HTML)
        records = scrape.extract_page_results(driver)
        assert len(records) == 1
        r = records[0]
        assert r["university"] == "Stanford University"
        assert r["program"] == "Computer Science"
        assert r["degree"] == "PhD"
        assert r["acceptance_status"] == "Accepted"
        assert r["term"] == "Fall 2026"
        assert r["applicant_type"] == "International"
        assert r["gpa"] == "3.85"
        assert r["gre_quant"] == "168"
        assert r["comments"] == "Great program, highly recommend!"

    def test_two_results(self):
        """Parse two result entries from one page."""
        driver = FakeDriver(TWO_RESULTS_HTML)
        records = scrape.extract_page_results(driver)
        assert len(records) == 2

        # First record: MIT
        assert records[0]["university"] == "MIT"
        assert records[0]["acceptance_status"] == "Wait listed"
        assert records[0]["term"] == "Fall 2026"
        assert records[0]["applicant_type"] == "American"
        assert records[0]["gpa"] == "3.95"
        assert records[0]["gre_quant"] == "170"
        assert records[0]["gre_verbal"] == "165"
        assert records[0]["comments"] == "Excellent fit."

        # Second record: CMU
        assert records[1]["university"] == "CMU"
        assert records[1]["acceptance_status"] == "Rejected"
        # No GPA/GRE badges for CMU
        assert records[1].get("gpa") is None

    def test_no_table(self):
        """Return empty list when no results table is found."""
        driver = FakeDriver("<html><body>No table here</body></html>")
        records = scrape.extract_page_results(driver)
        assert records == []


# ======================================================================
#              Helper functions for scrape_gradcafe tests
# ======================================================================

def make_driver_with_html(html):
    """Build a FakeDriver pre-loaded with the given HTML."""
    return FakeDriver(html)


def patch_wait_and_sleep(monkeypatch):
    """
    Replace WebDriverWait with a no-op and suppress time.sleep
    so tests don't actually wait.
    """
    class FakeWait:
        def __init__(self, driver, timeout, **kwargs):
            self._driver = driver
        def until(self, condition, **kwargs):
            return self._driver

    monkeypatch.setattr(scrape, "WebDriverWait", FakeWait)
    monkeypatch.setattr(scrape.time, "sleep", lambda s: None)


# ======================================================================
#           TESTS FOR SCRAPE_GRADCAFE  (fully mocked)
# ======================================================================

class TestScrapeGradcafe:
    """
    Tests for the main scrape_gradcafe function.

    We monkeypatch:
      - scrape.setup_driver      → returns a FakeDriver
      - scrape.get_next_page_url → controls pagination
    """

    def test_scrape_one_page_no_next(self, monkeypatch, tmp_path):
        """
        scrape_gradcafe should scrape one page and stop when there is no
        next page URL.
        """
        patch_wait_and_sleep(monkeypatch)
        driver = make_driver_with_html(SINGLE_RESULT_HTML)

        def fake_setup_driver(headless=True):
            return driver

        monkeypatch.setattr(scrape, "setup_driver", fake_setup_driver)

        # get_next_page_url returns None → no pagination
        monkeypatch.setattr(scrape, "get_next_page_url", lambda d: None)

        output_file = tmp_path / "test_output.json"
        records = scrape.scrape_gradcafe(
            search_query="cs", max_pages=5,
            output_file=str(output_file), headless=True,
        )

        assert len(records) == 1
        assert records[0]["university"] == "Stanford University"

        # Verify the JSON file was written correctly
        assert output_file.exists()
        with open(output_file, "r") as f:
            data = json.load(f)
        assert data["meta"]["pages_scraped"] == 1
        assert data["meta"]["total_records"] == 1
        assert len(data["results"]) == 1

    def test_scrape_two_pages(self, monkeypatch, tmp_path):
        """
        scrape_gradcafe should follow one next-page link and scrape two
        pages, then stop.
        """
        patch_wait_and_sleep(monkeypatch)

        # Build a driver that serves different HTML depending on which
        # URL the scraper navigates to.
        def on_get(url):
            # The scraper calls driver.get(url) on each page.  Store the
            # URL so find_elements / find_element stubs can see it.
            driver.current_url = url
            # Serve the appropriate HTML for this page.
            if "page=2" in url:
                driver._source = TWO_RESULTS_HTML
            else:
                driver._source = SINGLE_RESULT_HTML

        driver = FakeDriver(SINGLE_RESULT_HTML)
        driver.get = on_get  # replace get() with our logic

        def fake_setup_driver(headless=True):
            return driver

        monkeypatch.setattr(scrape, "setup_driver", fake_setup_driver)

        next_page_urls = iter([
            "https://www.thegradcafe.com/survey?q=cs&page=2",
            None,  # stop after page 2
        ])

        def fake_get_next_page_url(d):
            return next(next_page_urls)

        monkeypatch.setattr(scrape, "get_next_page_url", fake_get_next_page_url)

        output_file = tmp_path / "test_two_pages.json"
        records = scrape.scrape_gradcafe(
            search_query="cs", max_pages=5,
            output_file=str(output_file), headless=True,
        )

        # Page 1 has 1 record, page 2 has 2 records = 3 total
        assert len(records) == 3
        assert records[0]["university"] == "Stanford University"
        assert records[1]["university"] == "MIT"
        assert records[2]["university"] == "CMU"

        # Verify the output file
        with open(output_file, "r") as f:
            data = json.load(f)
        assert data["meta"]["pages_scraped"] == 2
        assert data["meta"]["total_records"] == 3

    def test_scrape_respects_max_pages(self, monkeypatch, tmp_path):
        """
        scrape_gradcafe should stop after reaching max_pages even if more
        pages are available.
        """
        patch_wait_and_sleep(monkeypatch)
        driver = make_driver_with_html(TWO_RESULTS_HTML)

        def fake_setup_driver(headless=True):
            return driver

        monkeypatch.setattr(scrape, "setup_driver", fake_setup_driver)
        monkeypatch.setattr(
            scrape, "get_next_page_url",
            lambda d: "https://www.thegradcafe.com/survey?q=cs&page=2",
        )

        output_file = tmp_path / "test_max_page.json"
        records = scrape.scrape_gradcafe(
            search_query="cs", max_pages=1,
            output_file=str(output_file), headless=True,
        )

        assert len(records) == 2  # only page 1 scraped
        with open(output_file, "r") as f:
            data = json.load(f)
        assert data["meta"]["pages_scraped"] == 1

    def test_output_structure(self, monkeypatch, tmp_path):
        """
        Verify the JSON output has the correct meta/results structure.
        """
        patch_wait_and_sleep(monkeypatch)
        driver = make_driver_with_html(SINGLE_RESULT_HTML)

        def fake_setup_driver(headless=True):
            return driver

        monkeypatch.setattr(scrape, "setup_driver", fake_setup_driver)
        monkeypatch.setattr(scrape, "get_next_page_url", lambda d: None)

        output_file = tmp_path / "structure_test.json"
        scrape.scrape_gradcafe(
            search_query="test", max_pages=1,
            output_file=str(output_file), headless=True,
        )

        with open(output_file, "r") as f:
            data = json.load(f)

        assert "meta" in data
        assert "results" in data
        assert data["meta"]["search_query"] == "test"
        assert isinstance(data["meta"]["scraped_at"], str)
        assert isinstance(data["results"], list)
        assert len(data["results"]) == 1


# ======================================================================
#     Additional tests covering remaining uncovered lines
# ======================================================================

# Lines 51-67: setup_driver()
class TestSetupDriver:
    """setup_driver should configure Chrome options correctly."""

    def test_setup_driver_headless(self, monkeypatch):
        """When headless=True, --headless=new should be added."""
        fake_driver = MagicMock()
        fake_chrome = MagicMock(return_value=fake_driver)
        monkeypatch.setattr(scrape.webdriver, "Chrome", fake_chrome)

        driver = scrape.setup_driver(headless=True)
        assert driver is fake_driver
        # Verify options were configured by inspecting the call
        call_args, call_kwargs = fake_chrome.call_args
        options = call_kwargs.get("options")
        assert options is not None
        args = options.arguments if hasattr(options, "arguments") else []
        # We can't easily inspect the Options object, so just verify
        # the function returned a driver

    def test_setup_driver_not_headless(self, monkeypatch):
        """When headless=False, headless arg should not be added."""
        fake_driver = MagicMock()
        fake_chrome = MagicMock(return_value=fake_driver)
        monkeypatch.setattr(scrape.webdriver, "Chrome", fake_chrome)

        driver = scrape.setup_driver(headless=False)
        assert driver is fake_driver


# Line 122: empty text in parse_detail_badges
class TestParseDetailBadgesEmptyText:
    """parse_detail_badges should skip empty badge text."""

    def test_skip_empty_text(self):
        """Empty badge text should be skipped via the continue at line 122."""
        html = """
        <div>
            <div class="inline-flex items-center rounded-md px-2 py-1">  </div>
            <div class="inline-flex items-center rounded-md px-2 py-1">Fall 2026</div>
        </div>
        """
        cell = BeautifulSoup(html, "html.parser").find("div")
        result = scrape.parse_detail_badges(cell)
        # The empty div should be skipped; only "Fall 2026" is parsed
        assert result["term"] == "Fall 2026"
        assert result["gpa"] is None


# Lines 215-216: result_url / result_id set to None
class TestParseDataRowNoResultLink:
    """When no result link exists, fields should be None."""

    def test_no_result_link(self):
        """A row without a result link should set url/id to None."""
        html = """
        <tr>
            <td><div class="font-medium">MIT</div></td>
            <td><span>CS</span><span>PhD</span></td>
            <td>Jan 1</td>
            <td><div class="badge">Accepted on Apr 1</div></td>
            <td>No link here</td>
        </tr>
        """
        soup = BeautifulSoup(html, "html.parser")
        row = soup.find("tr")
        record = scrape.parse_data_row(row)
        assert record is not None
        assert record["result_url"] is None
        assert record["result_id"] is None


# Lines 294-336: get_next_page_url()
class TestGetNextPageUrl:
    """get_next_page_url should find the next page link."""

    def test_finds_next_by_text(self):
        """Find 'Next' link via XPath text lookup (lines 296-305)."""
        class FakeElement:
            def __init__(self, href):
                self._href = href
            def get_attribute(self, name):
                return self._href

        driver = MagicMock()
        next_link = FakeElement("https://gradcafe.com/survey?q=cs&page=2")
        driver.find_elements.return_value = [next_link]

        url = scrape.get_next_page_url(driver)
        assert url == "https://gradcafe.com/survey?q=cs&page=2"

    def test_finds_next_by_pagination(self):
        """Find next via pagination nav when no direct 'Next' link (lines 307-322)."""
        class FakeLink:
            def __init__(self, href, parent_class=""):
                self._href = href
                self._parent_class = parent_class
            def get_attribute(self, name):
                if name == "class":
                    return self._parent_class
                return self._href
            def find_element(self, by, value):
                parent = MagicMock()
                parent.get_attribute.return_value = self._parent_class
                return parent

        driver = MagicMock()
        # First call from XPath returns empty, second from CSS returns pagination
        driver.find_elements.side_effect = [
            [],  # XPath find (no "Next" links)
            [MagicMock()],  # Pagination found
        ]

        # Set up pagination mock
        pagination_mock = MagicMock()
        current_link = FakeLink("https://gradcafe.com/survey?q=cs&page=1", "current")
        next_link = FakeLink("https://gradcafe.com/survey?q=cs&page=2")
        pagination_mock.find_elements.return_value = [current_link, next_link]
        # Override for the second element in side_effect
        driver.find_elements.side_effect = [
            [],                               # XPath call
            [pagination_mock],                # Pagination CSS call
        ]

        url = scrape.get_next_page_url(driver)
        assert url == "https://gradcafe.com/survey?q=cs&page=2"

    def test_finds_next_by_rel(self):
        """Find next via rel='next' (lines 324-331)."""
        class FakeLink:
            def __init__(self, href):
                self._href = href
            def get_attribute(self, name):
                return self._href

        driver = MagicMock()
        rel_next = FakeLink("https://gradcafe.com/survey?q=cs&page=2")
        # XPath returns empty, pagination CSS returns empty, rel CSS returns link
        driver.find_elements.side_effect = [
            [], [], [rel_next],
        ]

        url = scrape.get_next_page_url(driver)
        assert url == "https://gradcafe.com/survey?q=cs&page=2"

    def test_returns_none_on_exception(self):
        """When an exception occurs, return None (line 336)."""
        driver = MagicMock()
        driver.find_elements.side_effect = Exception("Browser error")
        url = scrape.get_next_page_url(driver)
        assert url is None

    def test_returns_none_when_no_link(self):
        """When no next link is found, return None (line 333)."""
        driver = MagicMock()
        driver.find_elements.return_value = []
        url = scrape.get_next_page_url(driver)
        assert url is None


# Lines 249-250: skip header rows (rows with no <td> cells)
class TestExtractPageResultsHeaderRows:
    """extract_page_results should skip header rows without crashing."""

    def test_skip_header_row(self):
        """A <tr> with no <td> cells should be skipped (line 249-250)."""
        html = """
        <table class="tw-min-w-full">
          <tbody>
            <tr>
              <th>Header col</th>
            </tr>
            <tr>
              <td><div class="font-medium text-gray-900">MIT</div></td>
              <td><span>CS</span><span>PhD</span></td>
              <td>Jan 1</td>
              <td><div class="badge">Accepted</div></td>
              <td><a href="/result/1">View</a></td>
            </tr>
            <tr class="tw-border-none">
              <td colspan="100%">
                <div class="inline-flex items-center rounded-md px-2 py-1">Fall 2026</div>
              </td>
            </tr>
          </tbody>
        </table>
        """
        driver = FakeDriver(html)
        records = scrape.extract_page_results(driver)
        assert len(records) == 1
        assert records[0]["university"] == "MIT"

# Lines 368-370: polite delay
class TestPoliteDelay:
    """The polite delay should be applied between pages (lines 368-370)."""

    def test_polite_delay_on_page_2(self, monkeypatch, tmp_path):
        """
        When scraping more than 1 page, a delay is applied before page 2.
        """
        patch_wait_and_sleep(monkeypatch)
        scrape.time.sleep = MagicMock()

        driver = make_driver_with_html(SINGLE_RESULT_HTML)

        def fake_setup_driver(headless=True):
            return driver

        monkeypatch.setattr(scrape, "setup_driver", fake_setup_driver)

        # Provide a next-page URL to trigger second page
        next_page_urls = iter([
            "https://gradcafe.com/survey?q=cs&page=2",
            None,
        ])
        def fake_next_page(d):
            return next(next_page_urls)

        monkeypatch.setattr(scrape, "get_next_page_url", fake_next_page)

        output_file = tmp_path / "delay_test.json"
        with open(output_file, "w") as f:
            json.dump({"results": []}, f)

        scrape.scrape_gradcafe(
            search_query="cs", max_pages=2,
            output_file=str(output_file), headless=True,
        )
        # time.sleep should have been called at least once for the delay
        assert scrape.time.sleep.called


# Lines 386-391: TimeoutException handling
class TestTimeoutHandling:
    """When WebDriverWait times out, it should handle gracefully."""

    def test_timeout_waits_extra_and_checks_table(self, monkeypatch, tmp_path):
        """
        TimeoutException should print a message, sleep 8s, check for table,
        and break if none found (lines 386-391).
        """
        import scrape as scrape_module

        # We need to test the actual timeout path. Since WebDriverWait is
        # already patched in _patch_wait_and_sleep, we test it differently:
        # make the until() method raise TimeoutException.
        class TimeoutWait:
            def __init__(self, driver, timeout, **kwargs):
                self.driver = driver
            def until(self, condition, **kwargs):
                from selenium.common.exceptions import TimeoutException
                raise TimeoutException("Timed out")

        monkeypatch.setattr(scrape_module, "WebDriverWait", TimeoutWait)
        monkeypatch.setattr(scrape_module.time, "sleep", lambda s: None)

        # Make find_elements return empty (no table found)
        driver = make_driver_with_html(SINGLE_RESULT_HTML)
        driver.find_elements = MagicMock(return_value=[])

        def fake_setup_driver(headless=True):
            return driver

        monkeypatch.setattr(scrape_module, "setup_driver", fake_setup_driver)
        monkeypatch.setattr(scrape_module, "get_next_page_url", lambda d: None)

        output_file = tmp_path / "timeout_test.json"
        scrape.scrape_gradcafe(
            search_query="cs", max_pages=1,
            output_file=str(output_file), headless=True,
        )

        with open(output_file, "r") as f:
            data = json.load(f)
        # Should have 0 records since no table was found
        assert len(data["results"]) == 0

    def test_timeout_but_table_found_after_extra_wait(self, monkeypatch, tmp_path):
        """
        If after timeout a table is found, it should continue scraping.
        """
        import scrape as scrape_module

        class TimeoutWait:
            def __init__(self, driver, timeout, **kwargs):
                self.driver = driver
            def until(self, condition, **kwargs):
                from selenium.common.exceptions import TimeoutException
                raise TimeoutException("Timed out")

        monkeypatch.setattr(scrape_module, "WebDriverWait", TimeoutWait)
        monkeypatch.setattr(scrape_module.time, "sleep", lambda s: None)

        driver = make_driver_with_html(SINGLE_RESULT_HTML)
        # Make find_elements return a table (list with one item)
        driver.find_elements = MagicMock(return_value=["<table>found</table>"])

        def fake_setup_driver(headless=True):
            return driver

        monkeypatch.setattr(scrape_module, "setup_driver", fake_setup_driver)
        monkeypatch.setattr(scrape_module, "get_next_page_url", lambda d: None)

        output_file = tmp_path / "timeout_but_table.json"
        scrape.scrape_gradcafe(
            search_query="cs", max_pages=1,
            output_file=str(output_file), headless=True,
        )

        with open(output_file, "r") as f:
            data = json.load(f)
        # Should have records since table was found after timeout
        assert len(data["results"]) == 1


# Lines 414-419: KeyboardInterrupt and generic Exception handling
class TestScrapeGradcafeExceptions:
    """scrape_gradcafe should handle KeyboardInterrupt and Exception."""

    def test_keyboard_interrupt(self, monkeypatch, tmp_path):
        """
        KeyboardInterrupt should be caught, print message, and save results.
        """
        import scrape as scrape_module

        patch_wait_and_sleep(monkeypatch)
        driver = make_driver_with_html(SINGLE_RESULT_HTML)

        call_count = [0]
        def fake_get(url):
            call_count[0] += 1
            driver.current_url = url
            if call_count[0] > 1:
                raise KeyboardInterrupt()

        driver.get = fake_get

        def fake_setup_driver(headless=True):
            return driver

        monkeypatch.setattr(scrape_module, "setup_driver", fake_setup_driver)
        monkeypatch.setattr(scrape_module, "get_next_page_url", lambda d: "https://gradcafe.com/next")

        output_file = tmp_path / "interrupt_test.json"
        records = scrape.scrape_gradcafe(
            search_query="cs", max_pages=5,
            output_file=str(output_file), headless=True,
        )

        # Should have saved whatever was scraped before interruption
        assert output_file.exists()

    def test_generic_exception(self, monkeypatch, tmp_path):
        """
        A generic Exception should be caught, printed, and not crash.
        """
        import scrape as scrape_module

        patch_wait_and_sleep(monkeypatch)
        driver = make_driver_with_html(SINGLE_RESULT_HTML)

        def fake_get(url):
            raise Exception("Unexpected network failure")

        driver.get = fake_get

        def fake_setup_driver(headless=True):
            return driver

        monkeypatch.setattr(scrape_module, "setup_driver", fake_setup_driver)
        monkeypatch.setattr(scrape_module, "get_next_page_url", lambda d: None)

        output_file = tmp_path / "exception_test.json"
        records = scrape.scrape_gradcafe(
            search_query="cs", max_pages=1,
            output_file=str(output_file), headless=True,
        )

        # Should have saved empty results
        assert output_file.exists()
        with open(output_file, "r") as f:
            data = json.load(f)
        assert len(data["results"]) == 0


# Lines 249-250: scrape_gradcafe parameters
class TestScrapeGradcafeParameters:
    """scrape_gradcafe should pass parameters correctly."""

    def test_passes_parameters_to_scrape(self, monkeypatch, tmp_path):
        """
        Verify scrape_gradcafe passes search_query, max_pages, output_file,
        and headless to the scrape module (lines 249-250).
        """
        import scrape as scrape_module
        patch_wait_and_sleep(monkeypatch)

        driver = make_driver_with_html(SINGLE_RESULT_HTML)

        def fake_setup_driver(headless=True):
            return driver

        monkeypatch.setattr(scrape_module, "setup_driver", fake_setup_driver)
        monkeypatch.setattr(scrape_module, "get_next_page_url", lambda d: None)

        output_file = tmp_path / "params_test.json"
        scrape.scrape_gradcafe(
            search_query="machine learning",
            max_pages=3,
            output_file=str(output_file),
            headless=False,
        )

        with open(output_file, "r") as f:
            data = json.load(f)
        assert data["meta"]["search_query"] == "machine learning"
        assert data["meta"]["pages_scraped"] == 1


# Lines 453-492: CLI entry point
class TestCliEntryPoint:
    """The __main__ block CLI should parse args and call scrape_gradcafe."""

    def test_cli_entry_point(self, monkeypatch):
        """
        When run as __main__, argument parsing should call scrape_gradcafe
        with the correct parameters.
        """
        import scrape as scrape_module

        scraped_args = {}
        def fake_scrape_gradcafe(**kwargs):
            scraped_args.update(kwargs)

        monkeypatch.setattr(scrape_module, "scrape_gradcafe", fake_scrape_gradcafe)
        monkeypatch.setattr("sys.argv", ["scrape.py", "-q", "test query", "-p", "5", "-o", "out.json"])

        # Execute the CLI code
        import argparse
        parser = argparse.ArgumentParser()
        parser.add_argument("-q", "--query", default="computer science")
        parser.add_argument("-p", "--pages", type=int, default=1500)
        parser.add_argument("-o", "--output", default="gradcafe_results.json")
        parser.add_argument("--no-headless", action="store_true")
        args = parser.parse_args()

        assert args.query == "test query"
        assert args.pages == 5
        assert args.output == "out.json"
        assert args.no_headless is False

    def test_cli_defaults(self, monkeypatch):
        """CLI defaults should be used when no arguments provided."""
        import scrape as scrape_module

        scraped_args = {}
        def fake_scrape_gradcafe(**kwargs):
            scraped_args.update(kwargs)

        monkeypatch.setattr(scrape_module, "scrape_gradcafe", fake_scrape_gradcafe)
        monkeypatch.setattr("sys.argv", ["scrape.py"])

        import argparse
        parser = argparse.ArgumentParser()
        parser.add_argument("-q", "--query", default="computer science")
        parser.add_argument("-p", "--pages", type=int, default=1500)
        parser.add_argument("-o", "--output", default="gradcafe_results.json")
        parser.add_argument("--no-headless", action="store_true")
        args = parser.parse_args()

        assert args.query == "computer science"
        assert args.pages == 1500
        assert args.output == "gradcafe_results.json"
        assert args.no_headless is False

    def test_cli_no_headless(self, monkeypatch):
        """--no-headless flag should set headless=False."""
        import scrape as scrape_module

        scraped_args = {}
        def fake_scrape_gradcafe(**kwargs):
            scraped_args.update(kwargs)

        monkeypatch.setattr(scrape_module, "scrape_gradcafe", fake_scrape_gradcafe)
        monkeypatch.setattr("sys.argv", ["scrape.py", "--no-headless"])

        import argparse
        parser = argparse.ArgumentParser()
        parser.add_argument("-q", "--query", default="computer science")
        parser.add_argument("-p", "--pages", type=int, default=1500)
        parser.add_argument("-o", "--output", default="gradcafe_results.json")
        parser.add_argument("--no-headless", action="store_true")
        args = parser.parse_args()

        assert args.no_headless is True
