import pandas as pd
import os

# Directory where the extracted CSV files are stored
script_dir = os.path.dirname(os.path.abspath(__file__))
extracted_folder = os.path.join(script_dir, "..", "data", "extracted")

# Process all CSV files in that folder
for filename in os.listdir(extracted_folder):
    if filename.endswith(".csv") and not filename.startswith("cleaned_"):
        input_path = os.path.join(extracted_folder, filename)
        output_path = os.path.join(extracted_folder, f"cleaned_{filename}")

        print(f"Processing {filename}...")
        df = pd.read_csv(input_path)

        # Strategy 1: Merge ranges (overall min and max)
        def merge_ranges(group):
            return pd.Series({
                'Min': group['Min'].min(),
                'Max': group['Max'].max()
            })

        df_clean = df.groupby(['Date', 'Crop', 'Market'], as_index=False).apply(
            merge_ranges, include_groups=False
        ).reset_index(drop=True)

        # --- Alternative strategy: keep the row with the highest minimum price ---
        # df_clean = df.loc[df.groupby(['Date', 'Crop', 'Market'])['Min'].idxmax()].reset_index(drop=True)

        df_clean.to_csv(output_path, index=False)
        print(f"Saved cleaned file: {output_path}")