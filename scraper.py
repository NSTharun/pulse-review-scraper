import requests
import json
import argparse
import time
from bs4 import BeautifulSoup
from datetime import datetime
from dateutil.parser import parse as parse_date


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Pulse Coding Assignment)"
}

RATE_LIMIT = 2  # seconds


class ReviewScraper:
    def __init__(self, company, start_date, end_date):
        self.company = company.lower().replace(" ", "-")
        self.start_date = parse_date(start_date)
        self.end_date = parse_date(end_date)

    def _valid_date(self, date):
        return self.start_date <= date <= self.end_date

    def scrape(self, source):
        if source == "g2":
            return self._scrape_g2()
        elif source == "capterra":
            return self._scrape_capterra()
        elif source == "trustradius":
            return self._scrape_trustradius()
        else:
            raise ValueError("Invalid source")

    # ---------------- G2 ----------------
    def _scrape_g2(self):
        reviews = []
        page = 1

        while True:
            url = f"https://www.g2.com/products/{self.company}/reviews?page={page}"
            res = requests.get(url, headers=HEADERS)
            if res.status_code != 200:
                break

            soup = BeautifulSoup(res.text, "html.parser")
            blocks = soup.select("div.review")

            if not blocks:
                break

            for block in blocks:
                try:
                    date = parse_date(block.select_one("time")["datetime"])
                    if not self._valid_date(date):
                        continue

                    reviews.append({
                        "title": block.select_one("h3").get_text(strip=True),
                        "review": block.select_one("p").get_text(strip=True),
                        "date": date.isoformat(),
                        "rating": block.select_one(".rating").get_text(strip=True),
                        "reviewer": block.select_one(".user-name").get_text(strip=True),
                        "source": "G2"
                    })
                except Exception:
                    continue

            page += 1
            time.sleep(RATE_LIMIT)

        return reviews

    # ---------------- Capterra ----------------
    def _scrape_capterra(self):
        reviews = []
        page = 1

        while True:
            url = f"https://www.capterra.com/p/{self.company}/reviews/?page={page}"
            res = requests.get(url, headers=HEADERS)
            if res.status_code != 200:
                break

            soup = BeautifulSoup(res.text, "html.parser")
            blocks = soup.select("div.review")

            if not blocks:
                break

            for block in blocks:
                try:
                    date = parse_date(block.select_one(".date").get_text(strip=True))
                    if not self._valid_date(date):
                        continue

                    reviews.append({
                        "title": block.select_one("h3").get_text(strip=True),
                        "review": block.select_one("p").get_text(strip=True),
                        "date": date.isoformat(),
                        "rating": block.select_one(".star-rating").get_text(strip=True),
                        "reviewer": block.select_one(".reviewer-name").get_text(strip=True),
                        "source": "Capterra"
                    })
                except Exception:
                    continue

            page += 1
            time.sleep(RATE_LIMIT)

        return reviews

    # ---------------- TrustRadius (Bonus) ----------------
    def _scrape_trustradius(self):
        reviews = []
        page = 1

        while True:
            url = f"https://www.trustradius.com/products/{self.company}/reviews?page={page}"
            res = requests.get(url, headers=HEADERS)
            if res.status_code != 200:
                break

            soup = BeautifulSoup(res.text, "html.parser")
            blocks = soup.select("div.review")

            if not blocks:
                break

            for block in blocks:
                try:
                    date = parse_date(block.select_one("time")["datetime"])
                    if not self._valid_date(date):
                        continue

                    reviews.append({
                        "title": block.select_one("h3").get_text(strip=True),
                        "review": block.select_one("p").get_text(strip=True),
                        "date": date.isoformat(),
                        "rating": block.select_one(".rating").get_text(strip=True),
                        "reviewer": block.select_one(".reviewer").get_text(strip=True),
                        "source": "TrustRadius"
                    })
                except Exception:
                    continue

            page += 1
            time.sleep(RATE_LIMIT)

        return reviews


def main():
    parser = argparse.ArgumentParser(description="Pulse Coding Assignment – Review Scraper")
    parser.add_argument("--company", required=True)
    parser.add_argument("--start_date", required=True)
    parser.add_argument("--end_date", required=True)
    parser.add_argument("--source", required=True, choices=["g2", "capterra", "trustradius"])

    args = parser.parse_args()

    scraper = ReviewScraper(args.company, args.start_date, args.end_date)
    reviews = scraper.scrape(args.source)

    filename = f"{args.company}_{args.source}_reviews.json"
    with open(filename, "w") as f:
        json.dump(reviews, f, indent=2)

    print(f"Saved {len(reviews)} reviews to {filename}")


if __name__ == "__main__":
    main()
