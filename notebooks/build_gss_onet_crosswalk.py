"""
Step 3: GSS 2024 occ10 (2010 Census codes) -> O*NET Work Values
Chain: Census 2010 code -> SOC 2010 -> O*NET-SOC 2010 -> O*NET-SOC 2019 -> Work Values
"""

import re
import pandas as pd
import pyreadstat
from pathlib import Path

# Paths relative to this script (notebooks/), so it runs from any folder
HERE = Path(__file__).resolve().parent  # .../notebooks
DATA = HERE.parent / "data"  # .../data

VALUES = [
    "Achievement",
    "Independence",
    "Recognition",
    "Relationships",
    "Support",
    "Working Conditions",
]

# --- 1. Census 2010 -> SOC 2010 (same cleaning as crosswalk.ipynb) ---
raw = pd.read_excel(DATA / "census_2010_occ_soc.xls", header=None)
census = raw.iloc[:, [1, 2, 3]].dropna(subset=[2, 3]).astype(str)
census.columns = ["census_title", "census_code", "soc2010"]
census = census.apply(lambda s: s.str.strip())
census = census[
    census.census_code.str.fullmatch(r"\d{1,4}(\.0)?")
    & census.soc2010.str.fullmatch(r"\d{2}-[\dX]{4}")
].copy()
census["census_code"] = census.census_code.str.replace(
    r"\.0$", "", regex=True
).str.zfill(4)

# --- 2. O*NET-SOC 2010 -> 2019 crosswalk (from onetcenter.org) ---
raw_xw = pd.read_excel(DATA / "2010_to_2019_Crosswalk.xlsx", header=None, dtype=str)


# Find the real header row (O*NET files often have title rows on top):
# the first row with a cell mentioning both "2010" and "code".
def is_code_col(cell, year):
    s = str(cell).lower()
    return year in s and "code" in s


hdr = next(
    (i for i, row in raw_xw.iterrows() if any(is_code_col(c, "2010") for c in row)),
    None,
)
if hdr is None:
    raise ValueError(
        "No '2010 ... Code' header found. First rows:\n" + raw_xw.head(10).to_string()
    )

xw = raw_xw.iloc[hdr + 1 :].copy()
xw.columns = [str(c).strip() for c in raw_xw.iloc[hdr]]
col2010 = next(c for c in xw.columns if is_code_col(c, "2010"))
col2019 = next(c for c in xw.columns if is_code_col(c, "2019"))
print(f"Crosswalk header row {hdr}: using '{col2010}' and '{col2019}'")

xw = xw.rename(columns={col2010: "onet2010", col2019: "onet2019"}).dropna(
    subset=["onet2010", "onet2019"]
)
xw["onet2010"] = xw.onet2010.str.strip()
xw["onet2019"] = xw.onet2019.str.strip()
xw["soc_detail"] = xw.onet2010.str[:7]
xw = xw[["soc_detail", "onet2019"]].drop_duplicates()
all_soc = set(xw.soc_detail)


# --- 3. Expand aggregate Census SOC codes (15-113X, 25-90XX, 11-2020, 25-1000) ---
# Detailed SOC codes never end in 0, so trailing 0s and X's are wildcards.
def is_aggregate(code):
    return "X" in code or code.endswith("0")


def prefix(code):
    """Fixed part: '11-2020'->'11-202', '25-1000'->'25-1', '25-90XX'->'25-90'."""
    return code.split("X")[0] if "X" in code else code.rstrip("0")


def candidates(code):
    if not is_aggregate(code):
        return [code]
    return sorted(s for s in all_soc if s.startswith(prefix(code)))


# Specificity: explicit codes beat aggregates; longer prefixes beat shorter.
census["spec"] = census.soc2010.map(lambda c: len(prefix(c)) if is_aggregate(c) else 99)
claims = census.assign(soc_detail=census.soc2010.map(candidates)).explode("soc_detail")

# Each detailed SOC code goes only to the most specific Census code claiming it
best = claims.groupby("soc_detail").spec.transform("max")
long = claims[(claims.spec == best) | claims.soc_detail.isna()].drop(columns="spec")

lost = sorted(set(census.census_code) - set(long.census_code))
if lost:
    print("WARNING: Census codes left with no SOC after overlap fix:", lost)

print("Aggregate expansions -- review these by hand:")
agg = long[long.soc2010.map(is_aggregate)]
print(
    agg.groupby(["census_code", "soc2010"])
    .soc_detail.apply(lambda s: list(s.dropna()))
    .to_string()
)

# --- 4. Attach O*NET 2019 codes, Work Values, and Job Zones ---
wv = pd.read_csv(HERE / "formatting_onet" / "formatted_work_values.csv").rename(
    columns={"O*NET-SOC Code": "onet2019"}
)
jz = pd.read_csv(HERE / "formatting_onet" / "formatted_job_zones.csv").rename(
    columns={"O*NET-SOC Code": "onet2019", "Job Zone": "job_zone"}
)
m = (
    long.merge(xw, on="soc_detail", how="left")
    .merge(wv[["onet2019"] + VALUES], on="onet2019", how="left")
    .merge(jz[["onet2019", "job_zone"]], on="onet2019", how="left")
    .drop_duplicates(["census_code", "onet2019"])
)
m["has_data"] = m[VALUES[0]].notna()

# --- 5. Collapse to one row per Census code (simple mean) ---
diag = m.groupby("census_code").agg(
    census_title=("census_title", "first"),
    soc2010=("soc2010", "first"),
    n_onet=("onet2019", "nunique"),
    n_with_data=("has_data", "sum"),
    n_with_job_zone=("job_zone", "count"),
)


def match_type(r):
    if r.n_onet == 0:
        return "no O*NET code"
    if r.n_with_data == 0:
        return "no data"
    if r.n_with_data < r.n_onet:
        return "partial"  # mean uses only some occupations: check bias
    return "1:1" if r.n_onet == 1 else "1:many"


diag["match"] = diag.apply(match_type, axis=1)

# Which O*NET 2019 codes had no Work Values (tells benign vs real gaps apart)
diag["onet_no_data"] = (
    m[~m.has_data & m.onet2019.notna()]
    .groupby("census_code")
    .onet2019.apply(lambda s: ", ".join(sorted(s)))
)


# Partial matches missing a real occupation, not just an "All Other" catch-all.
# SOC residual ("All Other") codes end in 9, e.g. 25-3099.
def missing_real_occupation(codes):
    return any(c[6] != "9" for c in codes.split(", "))


diag["partial_substantive"] = (diag["match"] == "partial") & diag.onet_no_data.fillna(
    ""
).map(lambda s: bool(s) and missing_real_occupation(s))

crosswalk = diag.join(
    m.groupby("census_code")[VALUES + ["job_zone"]].mean()
).reset_index()
crosswalk.to_csv(HERE.parent / "gss_occ10_work_values.csv", index=False)
print(crosswalk["match"].value_counts())

# --- 6. Validate: weighted coverage of GSS 2024 respondents ---
gss, _ = pyreadstat.read_sav(
    DATA / "GSS2024.sav", usecols=["occ10", "satjob", "wtssps"]
)
gss = gss.dropna(subset=["occ10"])
gss["census_code"] = gss.occ10.astype(int).astype(str).str.zfill(4)
g = gss.merge(crosswalk, on="census_code", how="left")
g["match"] = g["match"].fillna("not in Census list")

print("\nWeighted % of GSS respondents by match type:")
print((g.groupby("match").wtssps.sum() / g.wtssps.sum() * 100).round(1))

bad = ["no data", "partial", "no O*NET code", "not in Census list"]
pd.set_option("display.max_colwidth", 80)
print("\nBiggest problem codes (% of weighted GSS sample):")
print(
    g[g["match"].isin(bad)]
    .groupby(["census_code", "soc2010", "match", "onet_no_data"], dropna=False)
    .wtssps.sum()
    .div(g.wtssps.sum())
    .mul(100)
    .round(2)
    .sort_values(ascending=False)
    .head(25)
)

print("\nGSS codes not in the Census 2010 list:")
print(g.loc[g["match"] == "not in Census list", "census_code"].value_counts())
