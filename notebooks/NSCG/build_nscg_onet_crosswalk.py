"""
NSCG 2023 N3OCPR (NCSES occupation codes) -> O*NET-SOC 2019
Chain: NCSES code -> SOC 2018 (hand-curated) -> O*NET-SOC 2019 (O*NET crosswalk)
"""

import pandas as pd
from pathlib import Path

# Paths relative to this script (notebooks/NSCG/), so it runs from any folder
HERE = Path(__file__).resolve().parent  # .../notebooks/NSCG
DATA = HERE.parent.parent / "data"  # .../data

# --- 1. Hand-curated NCSES -> SOC 2018 map, checked against Table A-2 ---
hand = pd.read_csv(
    DATA / "crosswalks" / "ncses_to_soc2018.csv", dtype=str, keep_default_na=False
)

dupes = hand.ncses_code[hand.ncses_code.duplicated()]
if len(dupes):
    raise ValueError(f"NCSES codes listed more than once: {sorted(dupes)}")

# Table A-2 is NCSES's official 2023 code list; detailed codes are in column 6
a2 = pd.read_excel(
    DATA / "reference" / "nsf25322-taba-002.xlsx", header=None, skiprows=5, dtype=str
)
official = set(a2[6].dropna().str.strip())
missing = official - set(hand.ncses_code)
extra = set(hand.ncses_code) - official
if missing or extra:
    raise ValueError(
        f"Hand file doesn't match Table A-2. Missing: {sorted(missing)}, "
        f"not in Table A-2: {sorted(extra)}"
    )
print(f"{len(hand)} NCSES codes, matching Table A-2")

# --- 2. SOC 2018 -> O*NET-SOC 2019 ---
onet2019_to_soc2018 = pd.read_csv(
    DATA / "reference" / "onet2019_to_soc2018_crosswalk.csv", dtype=str, keep_default_na=False
)

# --- 3. Expand SOC group codes (51-0000, 13-1000, 29-1020) into detailed codes ---
all_soc = set(onet2019_to_soc2018["2018 SOC Code"])


# Detailed SOC codes never end in 0, so trailing 0s mark a group.
def is_group(code):
    return code.endswith("0")


def prefix(code):
    """Fixed part: '51-0000'->'51-', '13-1000'->'13-1', '29-1020'->'29-102'."""
    return code.rstrip("0")


def expand(code):
    found = sorted(s for s in all_soc if s.startswith(prefix(code))) if is_group(code) else [code]
    if not set(found) <= all_soc or not found:
        raise ValueError(f"{code} is not a SOC 2018 detailed code or group")
    return found

# One row per (NCSES code, SOC entry), then one row per detailed SOC code
claims = hand.assign(soc_entry=hand.soc2018_codes.str.split(";")).explode("soc_entry")
claims["soc_entry"] = claims.soc_entry.str.strip()
claims = claims[claims.soc_entry != ""]  # 785000 has no SOC codes
claims["soc_detail"] = claims.soc_entry.map(expand)
claims = claims.explode("soc_detail")

# --- 4. Resolve overlaps by prioritizing more specific matches ---
# Explicit codes beat groups; among groups, the longer prefix (narrower group) wins.
# e.g. 43-3031 is listed by 780310 and sits inside 780330's 43-0000, so 780310 keeps it.
claims["specificity"] = claims.soc_entry.map(lambda c: len(prefix(c)) if is_group(c) else 99)
best = claims.groupby("soc_detail").specificity.transform("max")
dropped = claims[claims.specificity < best]
claims = claims[claims.specificity == best]
# Ties are kept on purpose: 25-2031 is listed by three secondary-teacher codes

print(f"\n{len(dropped)} group claims dropped in favor of more specific ones:")
with pd.option_context("display.max_colwidth", None):
    print(
        dropped.groupby(["ncses_code", "soc_entry"])
        .soc_detail.apply(lambda s: ", ".join(s))
        .to_string()
    )

# --- 5. Coverage checks ---
# An NCSES code that listed SOC codes but lost all of them in step 4 is a mapping bug
lost = sorted(set(hand.ncses_code[hand.soc2018_codes != ""]) - set(claims.ncses_code))
if lost:
    raise ValueError(f"NCSES codes left with no SOC codes after step 4: {lost}")

shared = claims.groupby("soc_detail").ncses_code.agg(lambda s: ", ".join(sorted(s)))
shared = shared[shared.str.contains(",")]
print(f"\nSOC codes shared by more than one NCSES code ({len(shared)}):")
print(shared.to_string() if len(shared) else "  none")

# SOC occupations no NCSES code claims. Only the military (55-xxxx) should be here:
# NCSES has no military occupation code.
soc_titles = onet2019_to_soc2018.drop_duplicates("2018 SOC Code").set_index("2018 SOC Code")[
    "2018 SOC Title"
]
unclaimed = sorted(all_soc - set(claims.soc_detail))
military = [c for c in unclaimed if c.startswith("55-")]
other = [c for c in unclaimed if not c.startswith("55-")]
print(f"\nSOC codes not claimed by any NCSES code: {len(military)} military (55-xxxx), {len(other)} other")
for code in other:
    print(f"  {code} {soc_titles[code]}")

# --- 6. Attach O*NET-SOC 2019 codes ---
# Each SOC code has one or more O*NET codes: XX-XXXX.00 plus any specialties (.01, .02, ...)
soc_to_onet = onet2019_to_soc2018.rename(
    columns={"2018 SOC Code": "soc_detail", "O*NET-SOC 2019 Code": "onet2019"}
)[["soc_detail", "onet2019"]]
m = claims.merge(soc_to_onet, on="soc_detail", how="left")

# Every claimed SOC code came from the crosswalk's own list, so none should be missing
no_onet = sorted(m.soc_detail[m.onet2019.isna()].unique())
if no_onet:
    raise ValueError(f"SOC codes with no O*NET code: {no_onet}")
print(
    f"\n{m.soc_detail.nunique()} SOC codes -> {m.onet2019.nunique()} O*NET-SOC 2019 codes"
)

# --- 7. Collapse to one row per NCSES code ---
def joined(s):
    return ";".join(sorted(s.unique()))


per_code = m.groupby("ncses_code").agg(
    soc2018_codes=("soc_detail", joined),
    onet_soc_codes=("onet2019", joined),
    n_soc=("soc_detail", "nunique"),
    n_onet=("onet2019", "nunique"),
)

# Merge back onto the hand file so codes with no SOC codes (785000) keep their row
crosswalk = (
    hand[["ncses_code", "ncses_label", "notes"]]
    .merge(per_code, on="ncses_code", how="left", validate="one_to_one")
    .fillna({"soc2018_codes": "", "onet_soc_codes": "", "n_soc": 0, "n_onet": 0})
    .astype({"n_soc": int, "n_onet": int})
)


# Based on SOC count: extra O*NET specialties (.01, .02) refine one job, they don't add mismatch
def mapping_type(n_soc):
    if n_soc == 0:
        return "unmapped"
    return "direct" if n_soc == 1 else "aggregate"


crosswalk["mapping_type"] = crosswalk.n_soc.map(mapping_type)
crosswalk = crosswalk[
    ["ncses_code", "ncses_label", "soc2018_codes", "onet_soc_codes",
     "n_soc", "n_onet", "mapping_type", "notes"]
]
if len(crosswalk) != len(hand):
    raise ValueError(f"Expected {len(hand)} rows, got {len(crosswalk)}")

# --- 8. Write the crosswalk ---
out = DATA / "crosswalks" / "nscg_to_onet.csv"
crosswalk.to_csv(out, index=False)
print(f"\nWrote {len(crosswalk)} rows to {out.relative_to(DATA.parent)}")

print("\nmapping_type counts:")
print(crosswalk.mapping_type.value_counts().to_string())
print("\nLargest aggregates (review these by hand):")
print(
    crosswalk.nlargest(10, "n_soc")
    .assign(ncses_label=lambda d: d.ncses_label.str[:50])[
        ["ncses_code", "ncses_label", "n_soc", "n_onet"]
    ]
    .to_string(index=False)
)

