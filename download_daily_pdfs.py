import requests
import os
from datetime import datetime, timedelta

output_folder = "../data/raw_pdfs"
os.makedirs(output_folder, exist_ok=True)

start_date = datetime(2025,1,1)
end_date = datetime(2025,4,31)

current = start_date

while current <= end_date:

    day = current.strftime("%d-%m-%Y")
    month = current.strftime("%B").lower()
    year = current.strftime("%Y")

    url = f"https://www.harti.gov.lk/images/download/market_information/{year}/daily/{month}/daily_{day}.pdf"

    filename = f"{day}.pdf"
    path = os.path.join(output_folder, filename)

    try:

        r = requests.get(url)

        if r.status_code == 200:

            with open(path,"wb") as f:
                f.write(r.content)

            print("Downloaded:", filename)

        else:
            print("Not found:", filename)

    except:
        print("Error:", filename)

    current += timedelta(days=1)