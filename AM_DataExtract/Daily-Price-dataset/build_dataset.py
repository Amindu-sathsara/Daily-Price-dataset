# build_dataset.py
#import pandas as pd
#import os

# Use script directory for robust path resolution
#_script_dir = os.path.dirname(os.path.abspath(__file__))
#_base_dir = os.path.dirname(_script_dir)
#input_folder = os.path.join(_base_dir, "data", "extracted")
#output_file = os.path.join(_base_dir, "data", "final", "daily_vegetable_prices.csv")

#records = []
#csv_files = sorted(os.listdir(input_folder)) if os.path.exists(input_folder) else []
#for file in csv_files:
 #   if file.endswith(".csv"):
  #      df = pd.read_csv(os.path.join(input_folder, file))
   #     for _, row in df.iterrows():
    ##        min_price =row["Min"]
      ##     avg_price = (row["Min"] + row["Max"]) / 2
        #    records.append({
         #       "Date": row["Date"],
          #      "Crop": row["Crop"],
           #     "Market": row["Market"],
            #    "Min_Price": min_price,
             #   "Max_Price": max_price,
              #  "Avg_Price": avg_price
           # })

#final_df = pd.DataFrame(records)
#os.makedirs(os.path.dirname(output_file), exist_ok=True)
#final_df.to_csv(output_file, index=False)
#print("Final dataset created with", len(final_df), "records")

# build_dataset.py
import pandas as pd
import os

# -------------------------------
# PATH SETUP
# -------------------------------
_script_dir = os.path.dirname(os.path.abspath(__file__))
_base_dir = os.path.dirname(_script_dir)
input_folder = os.path.join(_base_dir, "data", "extracted")
output_file = os.path.join(_base_dir, "data", "final", "daily_vegetable_prices.csv")

all_dfs = []

# -------------------------------
# READ ALL CSV FILES
# -------------------------------
csv_files = sorted(os.listdir(input_folder)) if os.path.exists(input_folder) else []

for file in csv_files:
    if file.endswith(".csv"):
        path = os.path.join(input_folder, file)
        df = pd.read_csv(path)

        # -------------------------------
        # CLEAN + TRANSFORM
        # -------------------------------
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

        df["Min_Price"] = df["Min"]
        df["Max_Price"] = df["Max"]
        df["Avg_Price"] = (df["Min"] + df["Max"]) / 2

        # Keep only required columns
        df = df[["Date", "Crop", "Market", "Min_Price", "Max_Price", "Avg_Price"]]

        all_dfs.append(df)

# -------------------------------
# COMBINE ALL DATA
# -------------------------------
final_df = pd.concat(all_dfs, ignore_index=True)

# -------------------------------
# SORT (VERY IMPORTANT)
# -------------------------------
final_df = final_df.sort_values(by=["Date", "Market", "Crop"]).reset_index(drop=True)

# -------------------------------
# SAVE
# -------------------------------
os.makedirs(os.path.dirname(output_file), exist_ok=True)
final_df.to_csv(output_file, index=False)

print("✅ Final dataset created with", len(final_df), "records")