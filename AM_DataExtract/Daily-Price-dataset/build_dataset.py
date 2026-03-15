# build_dataset.py
import pandas as pd
import os

# Use script directory for robust path resolution
_script_dir = os.path.dirname(os.path.abspath(__file__))
_base_dir = os.path.dirname(_script_dir)
input_folder = os.path.join(_base_dir, "data", "extracted")
output_file = os.path.join(_base_dir, "data", "final", "daily_vegetable_prices.csv")

records = []
csv_files = sorted(os.listdir(input_folder)) if os.path.exists(input_folder) else []
for file in csv_files:
    if file.endswith(".csv"):
        df = pd.read_csv(os.path.join(input_folder, file))
        for _, row in df.iterrows():
            price = (row["Min"] + row["Max"]) / 2
            records.append({
                "Date": row["Date"],
                "Crop": row["Crop"],
                "Market": row["Market"],
                "Price": price
            })

final_df = pd.DataFrame(records)
os.makedirs(os.path.dirname(output_file), exist_ok=True)
final_df.to_csv(output_file, index=False)
print("Final dataset created with", len(final_df), "records")