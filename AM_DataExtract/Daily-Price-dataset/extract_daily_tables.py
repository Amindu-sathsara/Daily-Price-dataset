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
    "Pettah","Keppetipola", "Nuwaraeliya", "Bandarawela", "Veyangoda",
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
    date_pattern = r"\d{4}\.\d{2}\.\d{2}"
    dates = re.findall(date_pattern, footer_text)
    footer_clean = re.sub(date_pattern, "", footer_text).strip()
    tokens = footer_clean.split()
    markets_in_footer = [t for t in tokens if t in MARKET_NAMES]
    if len(dates) == len(markets_in_footer):
        return dict(zip(markets_in_footer, dates))
    else:
        # Fallback: assume all markets share the file date
        return {}

# ===== CHANGE 1: Use regex patterns with word boundaries and ordered list =====
# Patterns are checked in order (more specific first). All map to canonical names.
# If a pattern maps to None, that crop is explicitly skipped (e.g., Long beans).
VEGETABLE_PATTERNS = [
    (r"\bLong beans\b", None),            # skip Long beans (exclude)
    (r"\bBeet root \(Nuwaraeliya\)\b", "beetroot"),
    (r"\bBeet root\b", "beetroot"),
    (r"\bCabbage \(N'eliya\)\b", "cabbage"),
    (r"\bCabbage \(Kandy\)\b", "cabbage"),
    (r"\bCabbage\b", "cabbage"),
    (r"\bCarrot\b", "carrot"),
    (r"\bTomato\b", "tomato"),
    (r"\bBeans\b", "beans"),              # only exact "Beans", after "Long beans" check
]
# ========================================================================

# ===== CHANGE 2: New function to extract min/max from a cell =====
def extract_prices(cell):
    """Return (min, max) from a cell string."""
    if not cell or cell == "-":
        return None, None
    cell_str = str(cell).strip()
    # Range pattern: "100.00 - 130.00"
    match = re.search(r'(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)', cell_str)
    if match:
        min_p = int(float(match.group(1)))
        max_p = int(float(match.group(2)))
        return min_p, max_p
    # Fallback: extract all numbers
    nums = re.findall(r'\d+(?:\.\d+)?', cell_str)
    if nums:
        ints = [int(float(n)) for n in nums]
        return min(ints), max(ints)
    return None, None
# ==================================================================

for file in os.listdir(input_folder):
    if not file.endswith(".pdf"):
        continue

    path = os.path.join(input_folder, file)

    # Skip if already extracted
    out_file = os.path.join(output_folder, file.replace(".pdf", ".csv"))
    if os.path.exists(out_file):
        print(f"⏩ Skipped (already extracted): {file}")
        continue

    date_str = file.replace(".pdf", "")   # e.g., "31-03-2025"

    print(f"Processing {file}...")

    # ===== CHANGE 3: Use a dictionary to merge duplicates on the fly =====
    # Key: (date, crop, market) → Value: (min_price, max_price)
    merged = {}
    # ===================================================================

    with pdfplumber.open(path) as pdf:
        full_text = ""
        for page in pdf.pages:
            full_text += page.extract_text() + "\n"

        # Extract footer to get market dates
        footer_map = extract_market_dates(full_text)

        for page in pdf.pages:
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
                    for m in MARKET_NAMES:
                        if m in cell_str:
                            markets.append(m)
                            break
                    else:
                        markets.append(None)

                # Process data rows below the header
                for row in table[header_idx+1:]:
                    if not row or not row[0]:
                        continue
                    crop_cell = str(row[0]).strip()
                    # ===== CHANGE 4: Use regex patterns for matching =====
                    matched_crop = None
                    for pattern, can_name in VEGETABLE_PATTERNS:
                        if re.search(pattern, crop_cell, re.IGNORECASE):
                            matched_crop = can_name
                            break
                    # If no match or matched_crop is None, skip this row
                    if matched_crop is None:
                        continue
                    # ===================================================

                    # For each market column, extract min and max
                    for col_idx, market in enumerate(markets):
                        if market is None:
                            continue
                        if col_idx >= len(row):
                            continue
                        cell = row[col_idx]
                        if not cell or cell == "-":
                            continue

                        # ===== CHANGE 5: Use the new extract_prices function =====
                        min_p, max_p = extract_prices(cell)
                        if min_p is None or max_p is None:
                            continue
                        # =======================================================

                        # Determine date for this market
                        mkt_date = footer_map.get(market, date_str)

                        # ===== CHANGE 6: Merge into dictionary =====
                        key = (mkt_date, matched_crop, market)
                        if key not in merged:
                            merged[key] = (min_p, max_p)
                        else:
                            curr_min, curr_max = merged[key]
                            merged[key] = (min(curr_min, min_p), max(curr_max, max_p))
                        # ==========================================

    # ===== CHANGE 7: Convert merged dictionary to DataFrame and save =====
    if merged:
        rows = [[date, crop, market, min_p, max_p] for (date, crop, market), (min_p, max_p) in merged.items()]
        df = pd.DataFrame(rows, columns=["Date", "Crop", "Market", "Min", "Max"])
        out_file = os.path.join(output_folder, file.replace(".pdf", ".csv"))
        df.to_csv(out_file, index=False)
        print(f"Saved {len(df)} rows to {out_file}")
    else:
        print(f"No data extracted from {file}")
    # ====================================================================