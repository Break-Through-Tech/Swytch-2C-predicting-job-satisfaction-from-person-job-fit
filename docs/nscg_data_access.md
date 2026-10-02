# NSCG Raw Data Access

The raw 2023 National Survey of College Graduates (NSCG) public-use files
(`pcg23Public/`) are not tracked in this repo. The dataset is ~400MB total,
and several individual files (`epcg23.sas7bdat`, `epcg23.csv`, `EPCG23.DAT`)
exceed GitHub's 100MB per-file limit, so it's kept in a shared Google Drive
folder instead.

## Where it lives

Google Drive: https://drive.google.com/drive/u/0/folders/11LgwaGdOBq3e0bd4apFqI1IZJeAtswBt

## How to add it to your local project

1. Download the `pcg23Public` folder from the Drive link above.
2. Place it at `data/pcg23Public/` in the repo root, so paths like
   `data/pcg23Public/epcg23.csv` resolve correctly from notebooks.
3. `data/pcg23Public/` is already in `.gitignore`, so it won't be picked up
   by `git status` or accidentally committed.

The original source (with technical notes and documentation) is the NCSES
NSCG 2023 survey page, linked from `data/pcg23Public/README.TXT` once you've
downloaded the folder.
