import pandas as pd
import numpy as np

df = pd.read_csv('gss2024_onet_merged.csv')
#print(df.shape) #3986 rows x 48 columns

initial_rows = len(df) #3986

df = df.drop_duplicates()
#print("Row count after removing duplicates:", len(df)) #3986 --> no duplicates

df = pd.read_csv('gss2024_onet_merged.csv')

# Find missing values for every column and show only the ones missing data
missing_counts = df.isnull().sum()
missing_counts = missing_counts[missing_counts > 0]

print("Columns with missing values:")
print(missing_counts)

# drop administrative columns, survey weights, and crosswalk flags not needed for models
drop_cols = [
    'id', 'year', 'ballot', 'wtssps', 'wtssnrps', 'vpsu', 'vstrat',
    'census_code', 'census_title', 'soc2010', 'n_onet', 'n_with_data', 
    'n_with_job_zone', 'match', 'onet_no_data', 'partial_substantive', 'has_work_values',
    'hrs2', 'impjob'
]

# filter down to only columns that actually exist in the dataframe
cols_to_drop = [c for c in drop_cols if c in df.columns]
df_cleaned = df.drop(columns=cols_to_drop)

print("Shape after dropping extra cols:", df_cleaned.shape)

# save the streamlined file to work with next
df_cleaned.to_csv('gss2024_cleaned.csv', index=False)
print("Saved to gss2024_cleaned.csv")

# load cleaned dataset
df = pd.read_csv('gss2024_cleaned.csv')

# see which columns still have missing data
missing = df.isnull().sum()
missing = missing[missing > 0]

print("\nMissing values left in remaining 29 columns:")
print(missing)

# HANDLE MISSING VALUES (IMPUTATION)
imputation_log = {}

# fill numeric columns with the median (skip satjob target variable!)
numeric_cols = df.select_dtypes(include=[np.number]).columns
for col in numeric_cols:
    if col == 'satjob':
        continue
    if df[col].isnull().sum() > 0:
        fill_val = df[col].median()
        df[col] = df[col].fillna(fill_val)
        imputation_log[col] = ('Median', fill_val)

# fill categorical columns with the mode
cat_cols = df.select_dtypes(include=['object']).columns
for col in cat_cols:
    if df[col].isnull().sum() > 0:
        if df[col].dropna().empty:
            fill_val = 'Missing'
        else:
            fill_val = df[col].mode()[0]
        df[col] = df[col].fillna(fill_val)
        imputation_log[col] = ('Mode', fill_val)

# print out what was used for imputation
print("\n--- Imputation Log ---")
for col, (method, val) in imputation_log.items():
    print(f"{col}: filled with {method} ({val})")

# verify zero missing values remain in features (satjob will still have its 1204 missing, which is correct)
feature_cols = [c for c in df.columns if c != 'satjob']
print("\nRemaining missing values in features:", df[feature_cols].isnull().sum().sum())

# save the fully imputed dataset
df.to_csv('gss2024_onet_cleaned.csv', index=False)

# load the imputed dataset
df = pd.read_csv('gss2024_imputed.csv')

# check numeric columns for extreme values
cols = ['realrinc', 'hrs1', 'age', 'weekswrk', 'prestg10']

print("Summary Stats:")
print(df[cols].describe())

print("\nOutlier Counts (using 1.5 * IQR rule):")
for col in cols:
    q1 = df[col].quantile(0.25)
    q3 = df[col].quantile(0.75)
    iqr = q3 - q1
    low = q1 - 1.5 * iqr
    high = q3 + 1.5 * iqr
    
    # count rows outside the standard IQR bounds
    count = len(df[(df[col] < low) | (df[col] > high)])
    print(f"{col}: {count} outliers (bounds: {low:.1f} to {high:.1f})")

