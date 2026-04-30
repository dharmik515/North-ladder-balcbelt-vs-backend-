"""
Mismatch Review & Decision Application Tool

Allows analysts to review confidence-tiered match results and apply corrections to company data.
"""

import argparse
import csv
from pathlib import Path
from typing import Dict, List, Optional
import pandas as pd


def load_report(filepath: str) -> pd.DataFrame:
    """Load a CSV report file."""
    if not Path(filepath).exists():
        print(f"File not found: {filepath}")
        return pd.DataFrame()
    return pd.read_csv(filepath)


def review_report(report_df: pd.DataFrame, confidence_level: str = "medium") -> Dict[int, str]:
    """
    Interactive review of matches. User can approve, reject, or skip.
    Returns a dict of {row_index: decision}
    """
    decisions = {}
    for idx, row in report_df.iterrows():
        print(f"\n{'='*80}")
        print(f"Record {idx + 1} of {len(report_df)}")
        print(f"{'='*80}")
        print(f"Decision: {row.get('decision', 'N/A')}")
        print(f"Confidence: {row.get('confidence_score', 'N/A')}%")
        print(f"Reason: {row.get('description', 'N/A')}")
        print(f"\nCompany Data:")
        print(f"  IMEI: {row.get('company_imei', 'N/A')}")
        print(f"  Brand: {row.get('company_brand', 'N/A')}")
        print(f"  Model: {row.get('company_model', 'N/A')}")
        print(f"  Storage: {row.get('company_storage', 'N/A')}")
        print(f"  Color: {row.get('company_color', 'N/A')}")
        print(f"\nBlackbelt Data:")
        print(f"  IMEI: {row.get('blackbelt_imei', 'N/A')}")
        print(f"  IMEI2: {row.get('blackbelt_imei2', 'N/A')}")
        print(f"  Brand: {row.get('blackbelt_brand', 'N/A')}")
        print(f"  Model: {row.get('blackbelt_model', 'N/A')}")
        print(f"  Storage: {row.get('blackbelt_storage', 'N/A')}")
        print(f"  Color: {row.get('blackbelt_color', 'N/A')}")
        print(f"\nSuggested Correction: {row.get('suggested_correction', 'N/A')}")
        
        while True:
            choice = input("\nDecision (A=Approve, R=Reject, S=Skip, Q=Quit): ").strip().upper()
            if choice in ["A", "R", "S", "Q"]:
                decisions[idx] = {"A": "APPROVED", "R": "REJECTED", "S": "SKIPPED", "Q": "QUIT"}[choice]
                if choice == "Q":
                    return decisions
                break
    return decisions


def generate_correction_script(decisions: Dict[int, str], report_df: pd.DataFrame, output_path: str):
    """Generate a SQL/Python script to apply corrections."""
    approvals = [idx for idx, decision in decisions.items() if decision == "APPROVED"]
    corrections = []
    
    for idx in approvals:
        row = report_df.iloc[idx]
        suggestion = row.get("suggested_correction", "")
        if suggestion and suggestion != "Manual research required":
            corrections.append({
                "company_row": row.get("company_row_index"),
                "blackbelt_row": row.get("blackbelt_row_index"),
                "from_imei": row.get("company_imei"),
                "to_imei": row.get("blackbelt_imei"),
                "correction": suggestion,
            })
    
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        if corrections:
            writer = csv.DictWriter(f, fieldnames=["company_row", "blackbelt_row", "from_imei", "to_imei", "correction"])
            writer.writeheader()
            writer.writerows(corrections)
    
    print(f"\n=== APPROVAL SUMMARY ===")
    print(f"Total approved corrections: {len(corrections)}")
    print(f"Correction script saved to: {output_path}")
    return corrections


def generate_summary_report(output_dir: str):
    """Generate a summary of all matches across all confidence levels."""
    output_path = Path(output_dir)
    summary = {
        "high_confidence": 0,
        "medium_confidence": 0,
        "low_confidence": 0,
        "unmatched": 0,
    }
    
    for level, filename in [
        ("high_confidence", "high_confidence_matches.csv"),
        ("medium_confidence", "medium_confidence_matches.csv"),
        ("low_confidence", "low_confidence_matches.csv"),
        ("unmatched", "unmatched.csv"),
    ]:
        filepath = output_path / filename
        if filepath.exists():
            df = pd.read_csv(filepath)
            summary[level] = len(df)
    
    total = sum(summary.values())
    print(f"\n=== MATCHING SUMMARY ===")
    for level, count in summary.items():
        pct = 100 * count / total if total > 0 else 0
        print(f"{level.replace('_', ' ').title()}: {count} ({pct:.1f}%)")
    print(f"Total Records: {total}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Review and apply mismatch corrections")
    parser.add_argument("--output-dir", required=True, help="Output directory from pipeline")
    parser.add_argument("--level", default="medium", choices=["high", "medium", "low", "all"], 
                       help="Confidence level to review")
    parser.add_argument("--summary", action="store_true", help="Print summary and exit")
    return parser.parse_args()


def main():
    args = parse_args()
    output_dir = Path(args.output_dir)
    
    if args.summary:
        generate_summary_report(args.output_dir)
        return
    
    level_map = {
        "high": "high_confidence_matches.csv",
        "medium": "medium_confidence_matches.csv",
        "low": "low_confidence_matches.csv",
    }
    
    if args.level == "all":
        levels = ["high", "medium", "low"]
    else:
        levels = [args.level]
    
    for level in levels:
        filename = level_map[level]
        filepath = output_dir / filename
        
        if not filepath.exists():
            print(f"No {level} confidence matches found.")
            continue
        
        print(f"\n{'='*80}")
        print(f"REVIEWING {level.upper()} CONFIDENCE MATCHES")
        print(f"{'='*80}")
        
        report_df = load_report(str(filepath))
        decisions = review_report(report_df, level)
        
        correction_output = output_dir / f"corrections_{level}.csv"
        generate_correction_script(decisions, report_df, str(correction_output))


if __name__ == "__main__":
    main()
