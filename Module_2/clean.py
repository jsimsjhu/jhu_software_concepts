"""
clean.py — Wrapper Script for LLM Data Cleaning
Runs the LLM cleaner from the llm_hosting folder on applicant_data.json
and produces llm_extend_applicant_data.json.

Usage:
    python clean.py              (uses default: ../applicant_data.json -> ../llm_extend_applicant_data.json)
    python clean.py -f data.json -o output.json
"""

import sys
import os
import subprocess
import argparse


def main():
    parser = argparse.ArgumentParser(
        description="Run the LLM cleaner on scraped GradCafe data"
    )
    parser.add_argument(
        "-f", "--file",
        default="applicant_data.json",
        help="Input JSON file to clean (default: applicant_data.json)",
    )
    parser.add_argument(
        "-o", "--output",
        default="llm_extend_applicant_data.json",
        help="Output JSON file (default: llm_extend_applicant_data.json)",
    )
    parser.add_argument(
        "--llm-app",
        default=None,
        help="Path to the LLM app.py (default: llm_hosting/app.py)",
    )

    args = parser.parse_args()

    # Determine the directory of this script
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Resolve input file path
    input_path = args.file
    if not os.path.isabs(input_path):
        input_path = os.path.join(script_dir, input_path)

    # Resolve output file path
    output_path = args.output
    if not os.path.isabs(output_path):
        output_path = os.path.join(script_dir, output_path)

    # Resolve LLM app path
    if args.llm_app:
        llm_app_path = args.llm_app
    else:
        llm_app_path = os.path.join(script_dir, "llm_hosting", "app.py")

    # Verify paths
    if not os.path.exists(llm_app_path):
        print(f"Error: LLM app not found at: {llm_app_path}", file=sys.stderr)
        print(f"Make sure llm_hosting/app.py exists.", file=sys.stderr)
        sys.exit(1)

    if not os.path.exists(input_path):
        print(f"Error: Input file not found at: {input_path}", file=sys.stderr)
        print(f"Run scrape.py first to generate applicant_data.json.", file=sys.stderr)
        sys.exit(1)

    print("╔══════════════════════════════════════════╗")
    print("║    LLM Data Cleaning Wrapper (clean.py)  ║")
    print("╚══════════════════════════════════════════╝")
    print(f"  Input file:   {input_path}")
    print(f"  Output file:  {output_path}")
    print(f"  LLM app:      {llm_app_path}")
    print()

    # Run the LLM cleaner
    cmd = [
        sys.executable,
        llm_app_path,
        "--file", input_path,
    ]

    print(f"Running: {' '.join(cmd)}")
    print()

    try:
        with open(output_path, "w", encoding="utf-8") as out_f:
            result = subprocess.run(
                cmd,
                stdout=out_f,
                stderr=subprocess.PIPE,
                text=True,
                check=True,
            )
            if result.stderr:
                print(result.stderr)

        print(f"\n✓ LLM cleaning complete!")
        print(f"  Output written to: {output_path}")

    except subprocess.CalledProcessError as e:
        print(f"\n✗ LLM cleaning failed with exit code {e.returncode}", file=sys.stderr)
        if e.stderr:
            print(f"  Error output: {e.stderr}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()