"""
Step 4: Merge GSS 2024 respondents with O*NET occupation profiles (issue #12)
Left join on occ10 -> census_code using gss_occ10_work_values.csv (built by
build_gss_onet_crosswalk.py). No gap filling: unmatched rows keep NaN values.
"""

import pandas as pd
import pyreadstat
from pathlib import Path

# Paths relative to this script (notebooks/), so it runs from any folder
HERE = Path(__file__).resolve().parent  # .../notebooks
ROOT = HERE.parent
DATA = ROOT / "data"

# --- 1. GSS columns: IDs/design, outcome, job, baseline factors, person values ---
GSS_COLS = [
    # IDs and survey design (weights, variance estimation for CIs)
    "id", "year", "ballot", "wtssps", "wtssnrps", "vpsu", "vstrat",
    # Outcome
    "satjob",
    # Occupation and job
    "occ10", "indus10", "wrkstat", "wrkslf", "prestg10", "sei10",
    # Income and hours
    "realrinc", "rincom16", "hrs1", "hrs2", "weekswrk",
    # Demographics
    "age", "sex", "race", "hispanic", "born", "educ", "degree", "marital",
    "childs", "region", "union1",
    # Person-side values (the only job-values item in GSS 2024)
    "impjob",
]  # fmt: skip

VALUES = [
    "Achievement",
    "Independence",
    "Recognition",
    "Relationships",
    "Support",
    "Working Conditions",
]

# pyreadstat turns GSS missing codes (iap, don't know, no answer) into NaN
gss, _ = pyreadstat.read_sav(DATA / "GSS2024.sav", usecols=GSS_COLS)
gss = gss[GSS_COLS]

# --- 2. Join keys: both sides as 4-digit text ("0430"), or codes < 1000 won't match ---
cw = pd.read_csv(ROOT / "gss_occ10_work_values.csv", dtype={"census_code": str})
assert cw.census_code.is_unique, "crosswalk must have one row per Census code"

gss["census_code"] = (
    gss.occ10.dropna().astype(int).astype(str).str.zfill(4).reindex(gss.index)
)

# --- 3. Left join from GSS so no respondents are dropped ---
merged = gss.merge(
    cw, on="census_code", how="left", validate="many_to_one", indicator=True
)
assert len(merged) == len(gss), "merge changed the GSS row count"

# Label respondents the crosswalk doesn't cover
merged.loc[merged._merge == "left_only", "match"] = "not in Census list"
merged.loc[merged.occ10.isna(), "match"] = "no occ10"
merged = merged.drop(columns="_merge")
merged["partial_substantive"] = merged.partial_substantive.fillna(False).astype(bool)
merged["has_work_values"] = merged[VALUES[0]].notna()

out = ROOT / "gss2024_onet_merged.csv"
merged.to_csv(out, index=False)
print(f"Wrote {out.name}: {merged.shape[0]} rows x {merged.shape[1]} columns")


# --- 4. Write-up numbers: match rates, unmatched records ---
def pct(mask, w=None):
    """Unweighted and weighted % of rows where mask is True."""
    w = merged.wtssps if w is None else w
    return f"{mask.mean() * 100:.1f}% unweighted, {w[mask].sum() / w.sum() * 100:.1f}% weighted"


usable = merged.dropna(subset=["occ10", "satjob", "wtssps"])
has_occ = merged[merged.occ10.notna()]

print("\nRows:")
print(f"  GSS 2024 respondents:           {len(gss)}")
print(f"  with occ10:                     {len(has_occ)}")
print(f"  usable (occ10, satjob, wtssps): {len(usable)}")
print("  dropped by the merge:           0 (left join, row count checked)")

print("\nMatch rate (has Work Values):")
print(f"  of respondents with occ10: {pct(has_occ.has_work_values, has_occ.wtssps)}")
print(f"  of usable rows:            {pct(usable.has_work_values, usable.wtssps)}")
print(f"  job_zone filled, usable:   {pct(usable.job_zone.notna(), usable.wtssps)}")

print("\nMatch type, usable rows:")
print(
    pd.DataFrame(
        {
            "n": usable.match.value_counts(),
            "weighted_pct": (
                usable.groupby("match").wtssps.sum() / usable.wtssps.sum() * 100
            ).round(1),
        }
    ).sort_values("n", ascending=False)
)
print(
    f"  partial_substantive (borrowed scores): {usable.partial_substantive.sum()} rows"
)

print("\nUnmatched usable rows by occupation (no Work Values):")
unmatched = usable[~usable.has_work_values]
print(
    unmatched.groupby(["census_code", "census_title", "match"], dropna=False)
    .size()
    .rename("n")
    .sort_values(ascending=False)
    .to_string()
)
print(
    f"  {len(unmatched)} rows across {unmatched.census_code.nunique()} codes; "
    f"top 4 codes hold {unmatched.census_code.value_counts().head(4).sum()} rows"
)
