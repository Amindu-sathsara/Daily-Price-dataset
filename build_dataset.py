# build_dataset.py
import pandas as pd
import os

input_folder = "../data/extracted"
output_file = "../data/final/daily_vegetable_prices.csv"

records = []
for file in os.listdir(input_folder):
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
os.makedirs("../data/final", exist_ok=True)
final_df.to_csv(output_file, index=False)
print("Final dataset created with", len(final_df), "records")