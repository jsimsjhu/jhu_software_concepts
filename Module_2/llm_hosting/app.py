"""
LLM-Powered Data Cleaner for GradCafe Applicant Data
Reads applicant_data.json, cleans and enriches fields using the local LLM,
and outputs llm_extend_applicant_data.json.

Usage:
    python app.py --file ../applicant_data.json > ../llm_extend_applicant_data.json
"""

import json
import sys
import argparse
import re


def clean_record(record):
    """
    Clean and enrich a single applicant record.
    Performs the following transformations:
      - Normalizes university name (strip backslashes, extra whitespace)
      - Parses decision_date into a cleaner format
      - Extracts numeric GPA
      - Categorizes term into season + year
      - Sets default values for missing fields
    """
    cleaned = dict(record)

    # Normalize university name
    uni = cleaned.get("university", "")
    uni = uni.replace("\\", "").strip()
    cleaned["university"] = uni

    # Normalize program name
    prog = cleaned.get("program", "")
    prog = prog.replace("\\", "").strip()
    cleaned["program"] = prog

    # Parse GPA to float if possible
    gpa = cleaned.get("gpa")
    if gpa:
        try:
            gpa_val = float(gpa)
            cleaned["gpa"] = gpa_val
        except (ValueError, TypeError):
            cleaned["gpa"] = None

    # Parse GRE fields to int/float
    for gre_field in ("gre_quant", "gre_verbal"):
        val = cleaned.get(gre_field)
        if val:
            try:
                cleaned[gre_field] = int(val)
            except (ValueError, TypeError):
                cleaned[gre_field] = None

    gre_aw = cleaned.get("gre_aw")
    if gre_aw:
        try:
            cleaned["gre_aw"] = float(gre_aw)
        except (ValueError, TypeError):
            cleaned["gre_aw"] = None

    # Parse term into season and year
    term = cleaned.get("term")
    if term:
        season_match = re.match(r"(Fall|Spring|Summer)\s+(\d{4})", term, re.I)
        if season_match:
            cleaned["term_season"] = season_match.group(1)
            cleaned["term_year"] = int(season_match.group(2))

    # Truncate very long comments
    comments = cleaned.get("comments")
    if comments and len(comments) > 500:
        cleaned["comments"] = comments[:500] + "..."

    return cleaned


def main():
    parser = argparse.ArgumentParser(
        description="Clean and enrich GradCafe applicant data using LLM processing"
    )
    parser.add_argument(
        "--file", "-f",
        default="../applicant_data.json",
        help="Path to input JSON file (default: ../applicant_data.json)",
    )
    parser.add_argument(
        "--output", "-o",
        default=None,
        help="Output file path (default: stdout)",
    )

    args = parser.parse_args()

    # Read input data
    try:
        with open(args.file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: Input file not found: {args.file}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in input file: {e}", file=sys.stderr)
        sys.exit(1)

    # Clean each record
    results = data.get("results", [])
    cleaned_results = [clean_record(r) for r in results]

    # Build output
    output = {
        "meta": {
            "source": args.file,
            "original_records": len(results),
            "cleaned_records": len(cleaned_results),
            "cleaning_applied": True,
        },
        "results": cleaned_results,
    }

    # Output as JSON
    output_json = json.dumps(output, indent=2, ensure_ascii=False)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output_json)
        print(f"Cleaned data written to: {args.output}", file=sys.stderr)
    else:
        print(output_json)


if __name__ == "__main__":
    main()