from pathlib import Path
import pandas as pd
import time

data_path = Path(__file__).parent / "data" / "GSS_data_SPSS" / "2022_spss" / "2022" / "GSS2022.sav"
df = pd.read_spss(data_path, convert_categoricals=False)


print("Loading...")
start_time = time.perf_counter()

print("\n\n")
print(df.head())


#pd.set_option('display.max_columns', None)
#pd.set_option('display.width', 1000)
#pd.set_option('display.max_colwidth', None)
#print("\n\n")
#print(df.columns.tolist())

#print("\n\n")
#print(df.describe())

#end_time = time.perf_counter()
#execution_time = end_time - start_time

#print(f"Execution time: {execution_time:.6f} seconds")
