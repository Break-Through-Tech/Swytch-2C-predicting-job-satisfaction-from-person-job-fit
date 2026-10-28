
from pathlib import Path

import pandas as pd


# Project paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent

FEVS_DIR = PROJECT_ROOT / "data" / "fevs" / "2024"

DATA_PATH = FEVS_DIR / "FEVS_2024_PRDF_rv20250625.csv"
CODEBOOK_PATH = FEVS_DIR / "2024_OPM_FEVS_PRDF_Codebook.xlsx"


def main():
    print("=== ISSUE #22: FEVS + O*NET MERGE FEASIBILITY ===")

    # Confirm source files exist
    for path in [DATA_PATH, CODEBOOK_PATH]:
        if not path.exists():
            raise FileNotFoundError(f"Missing required file: {path}")

    # Load FEVS respondent-level data
    df = pd.read_csv(DATA_PATH, low_memory=False)

    print("\n=== DATASET OVERVIEW ===")
    print(f"Respondents: {len(df):,}")
    print(f"Columns: {len(df.columns)}")
    print(
        "Duplicate respondent IDs:",
        df["RandomID"].duplicated().sum()
    )

    # Search for occupation-related column names
    occupation_terms = [
        "occupation",
        "occ_code",
        "occ10",
        "occ2010",
        "soc",
        "census_occ",
        "job_series",
        "occupational_series",
    ]

    occupation_columns = [
        col for col in df.columns
        if any(term in col.lower() for term in occupation_terms)
    ]

    print("\n=== OCCUPATION IDENTIFIER CHECK ===")
    print("Potential occupation columns:", occupation_columns)

    # Check official codebook sheets
    workbook = pd.ExcelFile(CODEBOOK_PATH)

    print("\n=== OFFICIAL CODEBOOK ===")
    print("Sheets:", workbook.sheet_names)

    for sheet_name in workbook.sheet_names:
        sheet = pd.read_excel(
            CODEBOOK_PATH,
            sheet_name=sheet_name
        )
        print(f"{sheet_name}: {len(sheet)} rows")

    # Examine available organizational identifiers
    print("\n=== ORGANIZATIONAL IDENTIFIERS ===")

    for col in ["agency", "level1"]:
        print(f"\n{col}")
        print("Unique values:", df[col].nunique(dropna=True))
        print("Missing values:", df[col].isna().sum())
        print(df[col].value_counts(dropna=False).head(10))

    # Verify identifiers against codebook
    print("\n=== IDENTIFIER CODEBOOK VALIDATION ===")

    for col, sheet_name in [
        ("agency", "Agency Variable"),
        ("level1", "LEVEL1 Variable"),
    ]:
        lookup = pd.read_excel(
            CODEBOOK_PATH,
            sheet_name=sheet_name
        )

        observed = set(
            df[col].dropna().astype(str).str.strip()
        )

        documented = set(
            lookup["CODE"].dropna().astype(str).str.strip()
        )

        unmatched = observed - documented

        print(
            f"{col}: {len(observed)} observed codes, "
            f"{len(unmatched)} undocumented codes"
        )

    # Inspect job satisfaction outcome
    print("\n=== JOB SATISFACTION: Q70 ===")

    if "Q70" in df.columns:
        print(
            "Valid responses:",
            f"{df['Q70'].notna().sum():,}"
        )
        print(
            "Missing responses:",
            f"{df['Q70'].isna().sum():,}"
        )
        print(df["Q70"].value_counts(dropna=False).sort_index())

    # Explicit feasibility decision
    print("\n=== FEASIBILITY DECISION ===")

    if occupation_columns:
        print(
            "REVIEW REQUIRED: Potential occupation fields found. "
            "Verify their coding scheme before merging."
        )
    else:
        print(
            "NO-GO for an occupation-level respondent-to-O*NET merge."
        )
        print(
            "No Census/SOC/federal occupational-series identifier "
            "is present in the released columns."
        )
        print(
            "Agency/subdivision codes cannot uniquely identify "
            "a respondent's occupation."
        )
        print(
            "Per Issue #22, stop before crosswalk, merge, "
            "and merged-data EDA."
        )


if __name__ == "__main__":
    main()
