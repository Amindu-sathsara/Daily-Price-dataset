import requests
import os
from datetime import datetime, timedelta

# -------------------------------
# PATH SETUP
# -------------------------------
_script_dir = os.path.dirname(os.path.abspath(__file__))
_base_dir = os.path.dirname(_script_dir)
output_folder = os.path.join(_base_dir, "data", "raw_pdfs")
os.makedirs(output_folder, exist_ok=True)

# -------------------------------
# DATE RANGE
# -------------------------------
start_date = datetime(2021, 1, 1)
end_date = datetime(2021, 12, 31)

# -------------------------------
# HEADERS (IMPROVED)
# -------------------------------
headers = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/pdf",
    "Referer": "https://www.harti.gov.lk/"
}
# -------------------------------
# COUNTERS 🔥
# -------------------------------
download_count = 0
skip_count = 0
not_found_count = 0
# -------------------------------
# DOWNLOAD LOOP
# -------------------------------
current = start_date

while current <= end_date:

    day_full = current.strftime("%d-%m-%Y")
    day_short = current.strftime("%d-%m-%y")
    month_lower = current.strftime("%B").lower()
    month_cap = current.strftime("%B")
    year = current.strftime("%Y")
    prev_year = str(int(year) - 1)

    filename = f"{day_full}.pdf"
    path = os.path.join(output_folder, filename)

    # Skip existing
    if os.path.exists(path):
        print(f"⏩ Skipped: {filename}")
        skip_count += 1
        current += timedelta(days=1)
        continue

    # -------------------------------
    # POSSIBLE URLS
    # -------------------------------
    possible_urls = []

    # 2015
    if year == "2015":
        possible_urls += [
            f"https://www.harti.gov.lk/images/download/market_information/{year}/{month_cap}/daily_{day_full}.pdf"
        ]

    # 2016 (messy)
    elif year == "2016":
        months = [
            "january","february","march","april","may","june",
            "july","august","september","october","november","december"
        ]

        possible_urls += [
            f"https://www.harti.gov.lk/images/download/market_information/{year}/{month_lower}{year}/daily_{day_short}.pdf",
            f"https://www.harti.gov.lk/images/download/market_information/{year}/{month_lower}/daily_{day_short}.pdf",
            f"https://www.harti.gov.lk/images/download/market_information/{year}/{month_lower}/daily_{day_full}.pdf",
        ]

        for m in months:
            possible_urls.append(
                f"https://www.harti.gov.lk/images/download/market_information/{year}/{m}/daily_{day_full}.pdf"
            )

    # 2024
    elif year == "2024":
        possible_urls += [
            f"https://www.harti.gov.lk/images/download/market_information/{year}/{month_cap}/daily_{day_full}.pdf",
            f"https://www.harti.gov.lk/images/download/market_information/{year}/{month_lower}/daily_{day_full}.pdf",
        ]

    # 2017–2023 (FIXED ✅)
    else:
        possible_urls += [
            # Normal
            f"https://www.harti.gov.lk/images/download/market_information/{year}/daily/{month_lower}/daily_{day_full}.pdf",
            f"https://www.harti.gov.lk/images/download/market_information/{year}/daily/daily_{day_full}.pdf",
            f"https://www.harti.gov.lk/images/download/market_information/{year}/daily/{month_lower}/wholesale_prices_of_rice_{day_full}.pdf",

            # 🔥 previous year fallback
            f"https://www.harti.gov.lk/images/download/market_information/{year}/daily/{month_lower}/daily_{current.strftime('%d-%m-')}{prev_year}.pdf",
            f"https://www.harti.gov.lk/images/download/market_information/{year}/daily/daily_{current.strftime('%d-%m-')}{prev_year}.pdf",
        ]

    # -------------------------------
    # CASE VARIATIONS
    # -------------------------------
    possible_urls += [
        f"https://www.harti.gov.lk/images/download/market_information/{year}/daily/{month_lower}/Daily_{day_full}.pdf",
        f"https://www.harti.gov.lk/images/download/market_information/{year}/Daily/{month_cap}/Daily_{day_full}.pdf",
    ]

    # -------------------------------
    # DOWNLOAD ATTEMPTS
    # -------------------------------
    downloaded = False

    for url in possible_urls:
        try:
            print(f"Trying: {url}")

            r = requests.get(url, headers=headers, timeout=30)

            if r.status_code == 200 and r.content[:4] == b'%PDF':
                with open(path, "wb") as f:
                    f.write(r.content)

                print(f"✅ Downloaded: {filename}")
                download_count += 1
                downloaded = True
                break

        except requests.RequestException as e:
            print(f"⚠️ Error: {url} → {e}")

    if not downloaded:
        print(f"❌ Not found: {filename}")
        not_found_count += 1

    current += timedelta(days=1)

print("\n🎉 Download process completed!")
print(f"✅ Downloaded: {download_count}")
print(f"⏩ Skipped: {skip_count}")
print(f"❌ Not found: {not_found_count}")