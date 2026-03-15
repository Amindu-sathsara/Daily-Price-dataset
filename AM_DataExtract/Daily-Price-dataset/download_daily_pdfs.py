import requests
import os
from datetime import datetime, timedelta

# Use script directory for robust path resolution
_script_dir = os.path.dirname(os.path.abspath(__file__))
_base_dir = os.path.dirname(_script_dir)
output_folder = os.path.join(_base_dir, "data", "raw_pdfs")
os.makedirs(output_folder, exist_ok=True)

start_date = datetime(2025,1,1)
end_date = datetime(2025,4,30)

current = start_date
 
while current <= end_date:

    day = current.strftime("%d-%m-%Y")
    month = current.strftime("%B").lower()
    year = current.strftime("%Y")

    url = f"https://www.harti.gov.lk/images/download/market_information/{year}/daily/{month}/daily_{day}.pdf"

    filename = f"{day}.pdf"
    path = os.path.join(output_folder, filename)

    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        r = requests.get(url, headers=headers, timeout=30)

        if r.status_code == 200:
            with open(path, "wb") as f:
                f.write(r.content)
            print("Downloaded:", filename)
        else:
            print("Not found:", filename)

    except requests.RequestException as e:
        print("Error:", filename, str(e))

    current += timedelta(days=1)