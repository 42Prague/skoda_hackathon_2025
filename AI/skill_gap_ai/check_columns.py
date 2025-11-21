import pandas as pd
import os

data_folder = 'data'
excel_files = [f for f in os.listdir(data_folder) if f.endswith('.xlsx')]

for file in excel_files[:3]:
    print(f"\n=== {file} ===")
    try:
        df = pd.read_excel(os.path.join(data_folder, file))
        print(f"Columns: {list(df.columns)[:10]}")
        print(f"Rows: {len(df)}")
    except Exception as e:
        print(f"Error: {e}")
