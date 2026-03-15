import pdfplumber
import pandas as pd
import os
import re

# Use script directory for robust path resolution
_script_dir = os.path.dirname(os.path.abspath(__file__))
_base_dir = os.path.dirname(_script_dir)
input_folder = os.path.join(_base_dir, "data", "raw_pdfs")
output_folder = os.path.join(_base_dir, "data", "extracted")
os.makedirs(output_folder, exist_ok=True)

# List of all possible market names (as they appear in the PDF)
MARKET_NAMES = [
    "Keppetipola", "Nuwaraeliya", "Bandarawela", "Veyangoda",
    "Peliyagoda", "Kandy", "Dambulla", "Meegoda", "Norochchole",
    "Thambuththegama"   # also appears in footer
]

def find_header_row(table):
    """Find the row index that contains market names."""
    for i, row in enumerate(table):
        row_str = " ".join(str(cell) for cell in row if cell)
        # Check if any market name appears in this row
        if any(market in row_str for market in MARKET_NAMES):
            return i
    return None

def extract_market_dates(footer_text):
    """
    Parse the footer to get a mapping of market -> date.
    Footer format example:
        "Keppetipola Nuwaraeliya Bandarawela Veyangoda Peliyagoda Kandy Dambulla Meegoda Norochchole 2025.03.31 2025.03.31 2025.03.31 2025.03.30 2025.03.31"
    This function aligns market names with the dates that follow.
    """
    # A simple heuristic: find all dates (YYYY.MM.DD) and assume they correspond
    # to the markets in order, but the footer may have extra text.
    date_pattern = r"\d{4}\.\d{2}\.\d{2}"
    dates = re.findall(date_pattern, footer_text)
    # Remove dates from footer text to get the market list
    footer_clean = re.sub(date_pattern, "", footer_text).strip()
    # Split by whitespace to get potential market names
    tokens = footer_clean.split()
    markets_in_footer = [t for t in tokens if t in MARKET_NAMES]
    # If the number of dates matches the number of markets, zip them
    if len(dates) == len(markets_in_footer):
        return dict(zip(markets_in_footer, dates))
    else:
        # Fallback: assume all markets share the file date
        return {} 

# Your vegetables of interest (map to canonical names)
# Sort by pattern length descending so longer variants match first
VEGETABLES = {
    "beans": "beans",
    "carrot": "carrot",
    "tomato": "tomato",
    "cabbage": "cabbage",
    "beet root": "beetroot",
    "beet root (n eliya)": "beetroot",
    "cabbage (n'eliya)": "cabbage",
    "cabbage (kandy)": "cabbage"
}
VEGETABLES_SORTED = sorted(VEGETABLES.items(), key=lambda x: -len(x[0]))

for file in os.listdir(input_folder):
    if not file.endswith(".pdf"):
        continue

    path = os.path.join(input_folder, file)
    date_str = file.replace(".pdf", "")   # e.g., "31-03-2025"

    print(f"Processing {file}...")
    rows = []

    with pdfplumber.open(path) as pdf:
        full_text = ""
        for page in pdf.pages:
            full_text += page.extract_text() + "\n"

        # Extract footer to get market dates
        footer_map = extract_market_dates(full_text)

        for page in pdf.pages:
            # Use default extraction - "text" strategy fragments table cells incorrectly
            tables = page.extract_tables()

            for table in tables:
                if not table:
                    continue

                # Locate header row (with market names)
                header_idx = find_header_row(table)
                if header_idx is None:
                    continue

                header = table[header_idx]
                # Clean header cells
                markets = []
                for cell in header:
                    cell_str = str(cell).strip() if cell else ""
                    # Find which market name is in this cell
                    for m in MARKET_NAMES:
                        if m in cell_str:
                            markets.append(m)
                            break
                    else:
                        markets.append(None)

                # Now process data rows below the header
                for row in table[header_idx+1:]:
                    if not row or not row[0]:
                        continue
                    crop_cell = str(row[0]).strip().lower()
                    # Check if this crop is in our list (longest pattern first)
                    matched_crop = None
                    for pattern, can_name in VEGETABLES_SORTED:
                        if pattern in crop_cell:
                            matched_crop = can_name
                            break
                    if not matched_crop:
                        continue

                    # For each market column, extract min and max
                    for col_idx, market in enumerate(markets):
                        if market is None:
                            continue
                        if col_idx >= len(row):
                            continue
                        cell = row[col_idx]
                        if not cell or cell == "-":
                            continue
                        # Extract two numbers
                        match = re.search(r"(\d+)\s*-\s*(\d+)", str(cell))
                        if match:
                            min_p = int(match.group(1))
                            max_p = int(match.group(2))
                            # Determine date for this market
                            mkt_date = footer_map.get(market, date_str)
                            rows.append([
                                mkt_date,
                                matched_crop,
                                market,
                                min_p,
                                max_p
                            ])

    # Save extracted rows to CSV
    if rows:
        df = pd.DataFrame(rows, columns=["Date", "Crop", "Market", "Min", "Max"])
        out_file = os.path.join(output_folder, file.replace(".pdf", ".csv"))
        df.to_csv(out_file, index=False)
        print(f"Saved {len(df)} rows to {out_file}")
    else:
        print(f"No data extracted from {file}")