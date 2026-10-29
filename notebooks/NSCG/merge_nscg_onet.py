"""
Merge NSCG 2023 respondents with O*NET occupation profiles (issue #20)
Left join on N3OCPR -> ncses_code using data/crosswalks/nscg_to_onet.csv (built by
build_nscg_onet_crosswalk.py). No gap filling: missing O*NET values stay NaN.
"""

import pandas as pd
from pathlib import Path

# Paths relative to this script (notebooks/NSCG/), so it runs from any folder
HERE = Path(__file__).resolve().parent  # .../notebooks/NSCG
DATA = HERE.parent.parent / "data"  # .../data

# --- 1. NSCG columns (keep_cols from nscg_initial_work.ipynb), employed only ---
NSCG_COLS = [
    # id / weight
    "OBSNUM", "WTSURVY",
    # target
    "JOBSATIS",
    # satisfaction facets: keep for validation, NOT as baseline predictors (leakage risk)
    "SATADV", "SATBEN", "SATCHAL", "SATIND", "SATLOC", "SATRESP", "SATSAL", "SATSEC", "SATSOC",
    # person side of fit: how important each job factor is to the respondent
    "FACADV", "FACBEN", "FACCHAL", "FACIND", "FACLOC", "FACRESP", "FACSAL", "FACSEC", "FACSOC",
    # occupation / fit
    "N3OCPR", "OCEDRLP", "MGRNAT", "MGROTH", "MGRSOC",
    # employer / job characteristics
    "NEDTP", "INDCODE", "JOBINS", "JOBPENS", "JOBPROFT", "JOBVAC",
    # degree field
    "NDGMEMG",
    # career timing / degree: year current job started, year and type of highest degree
    "STRTYR", "DGRYR", "DGRDG",
    # baseline: demographics
    "AGE", "SEX_2023", "RACETHM", "HISPANIC", "CTZN", "MARSTA",
    # baseline: work
    "SALARY", "EARN", "HRSWK", "WKSWK", "WKSYR", "LFSTAT", "TELEC", "TELEFR", "EMSIZE",
]  # fmt: skip

# Read as text so codes keep their exact form ("110510", "L"); cleaning comes later
nscg = pd.read_csv(DATA / "pcg23Public" / "epcg23.csv", usecols=NSCG_COLS, dtype=str)
nscg = nscg[NSCG_COLS]
print(f"NSCG 2023 respondents: {len(nscg)}")

# Occupation and JOBSATIS are only asked of people working (LFSTAT 1)
nscg = nscg[nscg.LFSTAT == "1"].reset_index(drop=True)
nscg["WTSURVY"] = nscg.WTSURVY.astype(float)
print(f"Employed (LFSTAT == 1): {len(nscg)}")

# --- 2. One O*NET profile per NCSES code (simple mean over its O*NET occupations) ---
VALUES = [
    "Achievement",
    "Independence",
    "Recognition",
    "Relationships",
    "Support",
    "Working Conditions",
]

cw = pd.read_csv(
    DATA / "crosswalks" / "nscg_to_onet.csv", dtype=str, keep_default_na=False
)
assert cw.ncses_code.is_unique, "crosswalk must have one row per NCSES code"

wv = pd.read_csv(HERE.parent / "formatting_onet" / "formatted_work_values.csv").rename(
    columns={"O*NET-SOC Code": "onet2019"}
)
jz = pd.read_csv(HERE.parent / "formatting_onet" / "formatted_job_zones.csv").rename(
    columns={"O*NET-SOC Code": "onet2019", "Job Zone": "job_zone"}
)

# One row per (NCSES code, O*NET code); 785000 has none and drops out here
long = cw.assign(onet2019=cw.onet_soc_codes.str.split(";")).explode("onet2019")
long = long[long.onet2019 != ""][["ncses_code", "onet2019"]]
long = long.merge(wv[["onet2019"] + VALUES], on="onet2019", how="left").merge(
    jz[["onet2019", "job_zone"]], on="onet2019", how="left"
)
long["has_wv"] = long[VALUES[0]].notna()


# A missing .00 code that isn't an "All Other" catch-all (SOC ending in 9) means a real
# occupation is absent, e.g. 15-2051.00 Data Scientists. A missing specialty (.01, .02)
# is less serious: its base occupation is still in the profile.
def is_substantive(code):
    return code.endswith(".00") and code[6] != "9"


long["missing_substantive"] = ~long.has_wv & long.onet2019.map(is_substantive)

profile = long.groupby("ncses_code").agg(
    n_onet_with_wv=("has_wv", "sum"),
    n_onet_with_jz=("job_zone", "count"),
    partial_substantive=("missing_substantive", "any"),
    onet_no_wv=("onet2019", lambda s: ";".join(sorted(s[~long.loc[s.index, "has_wv"]]))),
)
profile = profile.join(long.groupby("ncses_code")[VALUES + ["job_zone"]].mean())

# Merge onto the crosswalk so 785000 keeps a row. The long code lists stay in the
# crosswalk file; repeating them on ~80k respondent rows would bloat the output.
profile = cw[["ncses_code", "ncses_label", "mapping_type", "n_soc", "n_onet"]].merge(
    profile.reset_index(), on="ncses_code", how="left", validate="one_to_one"
)
profile = profile.astype({"n_soc": int, "n_onet": int}).fillna(
    {"n_onet_with_wv": 0, "n_onet_with_jz": 0, "onet_no_wv": ""}
)
profile = profile.astype({"n_onet_with_wv": int, "n_onet_with_jz": int})


def wv_status(r):
    if r.n_onet == 0:
        return "unmapped"
    if r.n_onet_with_wv == 0:
        return "no data"
    return "partial" if r.n_onet_with_wv < r.n_onet else "full"


profile["wv_status"] = profile.apply(wv_status, axis=1)
# Only partial profiles can borrow scores; "no data" rows have no scores to borrow
# .eq(True) also turns 785000's blank (no O*NET codes) into False
profile["partial_substantive"] = (profile.wv_status == "partial") & profile[
    "partial_substantive"
].eq(True)

print(f"\nO*NET profiles for {len(profile)} NCSES codes. Work Values status:")
print(profile.wv_status.value_counts().to_string())
print(f"partial_substantive: {profile.partial_substantive.sum()} codes")

# --- 3. Left join respondents to profiles on N3OCPR -> ncses_code ---
merged = nscg.merge(
    profile,
    left_on="N3OCPR",
    right_on="ncses_code",
    how="left",
    validate="many_to_one",
    indicator=True,
)
assert len(merged) == len(nscg), "merge changed the NSCG row count"

# Every employed respondent's code should be in the crosswalk (all 129 codes are)
unknown = merged.N3OCPR[merged._merge == "left_only"].value_counts()
if len(unknown):
    raise ValueError(f"N3OCPR codes not in the crosswalk:\n{unknown.to_string()}")

merged = merged.drop(columns=["_merge", "ncses_code"])
merged["has_work_values"] = merged[VALUES[0]].notna()
merged["has_job_zone"] = merged.job_zone.notna()
print(f"\nMerged: {merged.shape[0]} rows x {merged.shape[1]} columns (row count unchanged)")

# --- 4. Write output and write-up numbers (gitignored; rebuild by rerunning) ---
out = DATA / "nscg2023_onet_merged.csv"
merged.to_csv(out, index=False)
print(f"Wrote {out.relative_to(DATA.parent)}")


def pct(mask, w=None):
    """Unweighted and weighted % of rows where mask is True."""
    w = merged.WTSURVY if w is None else w
    return f"{mask.mean() * 100:.1f}% unweighted, {w[mask].sum() / w.sum() * 100:.1f}% weighted"


def breakdown(col):
    """Rows and weighted % for each value of col."""
    return pd.DataFrame(
        {
            "n": merged[col].value_counts(),
            "weighted_pct": (
                merged.groupby(col).WTSURVY.sum() / merged.WTSURVY.sum() * 100
            ).round(1),
        }
    ).sort_values("n", ascending=False)


print("\nCoverage (employed respondents):")
print(f"  has Work Values: {pct(merged.has_work_values)}")
print(f"  has Job Zone:    {pct(merged.has_job_zone)}")
print(f"  partial_substantive (borrowed scores): {pct(merged.partial_substantive)}")

print("\nmapping_type:")
print(breakdown("mapping_type").to_string())
print("\nwv_status:")
print(breakdown("wv_status").to_string())

print("\nRespondents with no Work Values, by occupation:")
unmatched = merged[~merged.has_work_values]
print(
    unmatched.groupby(["N3OCPR", "ncses_label", "wv_status"])
    .WTSURVY.agg(n="size", weighted_pct=lambda w: w.sum() / merged.WTSURVY.sum() * 100)
    .round({"weighted_pct": 2})
    .sort_values("n", ascending=False)
    .to_string()
)
