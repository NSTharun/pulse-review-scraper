import json
import argparse
import time
import re
from datetime import datetime
from dateutil.parser import parse as parse_date
from playwright.sync_api import sync_playwright

HEADLESS = False  # Set to False to see the browser (better for debugging/demo)

class ReviewScraper:
    def __init__(self, company, start_date, end_date):
        self.company = company.lower().replace(" ", "-")
        self.start_date = parse_date(start_date)
        self.end_date = parse_date(end_date)
        self.reviews = []

    def _valid_date(self, date_str):
        try:
            # Handle "Jun 26, 2024" format often used on these sites
            date = parse_date(date_str)
            return self.start_date <= date <= self.end_date
        except Exception:
            return False

    def scrape(self, source):
        with sync_playwright() as p:
            # Launch browser - headless=False is safer for detection usually, but slower
            browser = p.chromium.launch(headless=HEADLESS)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = context.new_page()

            try:
                if source == "g2":
                    self._scrape_g2(page)
                elif source == "capterra":
                    self._scrape_capterra(page)
                elif source == "trustradius":
                    self._scrape_trustradius(page)
                else:
                    raise ValueError("Invalid source")
            except Exception as e:
                print(f"Error during scraping: {e}")
            finally:
                browser.close()
        
        return self.reviews

    # ---------------- G2 ----------------
    def _scrape_g2(self, page):
        page_num = 1
        while True:
            url = f"https://www.g2.com/products/{self.company}/reviews?page={page_num}"
            print(f"Navigating to {url}")
            page.goto(url, timeout=60000)
            
            # G2 might have a captcha or cloudflare check. 
            # Simple wait for content.
            try:
                page.wait_for_selector('div.paper, div[itemprop="review"]', timeout=15000)
            except:
                print("Content not found or blocked. (Check for Captcha/Cloudflare)")
                break

            # Adjust selectors based on inspection (generic approximation provided as start)
            # G2 reviews are often in div.paper inside a list
            review_elements = page.query_selector_all('div.paper') 
            
            # If standard selector fails, try falling back to generic review container
            if not review_elements:
                 review_elements = page.query_selector_all('div[itemprop="review"]')

            if not review_elements:
                print("No reviews found on this page.")
                break

            found_on_page = 0
            for element in review_elements:
                try:
                    # G2 specific extracting
                    # Note: Selectors are incredibly fragile on G2.
                    date_el = element.query_selector('time') or element.query_selector('.time-ago')
                    if not date_el: continue
                    
                    date_str = date_el.get_attribute('datetime') or date_el.inner_text()
                    if not self._valid_date(date_str):
                        continue

                    title_el = element.query_selector('h3') or element.query_selector('.review-title')
                    title = title_el.inner_text() if title_el else "No Title"

                    review_el = element.query_selector('div[itemprop="reviewBody"]') or element.query_selector('.review-text')
                    review_text = review_el.inner_text() if review_el else ""

                    reviewer_el = element.query_selector('.user-name, div[itemprop="author"]')
                    reviewer = reviewer_el.inner_text() if reviewer_el else "Anonymous"
                    
                    self.reviews.append({
                        "title": title,
                        "review": review_text[:200] + "...", # Truncate for display
                        "date": date_str,
                        "source": "G2",
                        "reviewer": reviewer
                    })
                    found_on_page += 1
                except Exception as e:
                    continue
            
            print(f"Found {found_on_page} valid reviews on page {page_num}")
            
            # Pagination check
            next_button = page.query_selector('a.pagination__named-link.state--next')
            if not next_button or 'disabled' in next_button.get_attribute('class', ''):
                break
                
            page_num += 1
            time.sleep(3) # Be nice

    # ---------------- Capterra ----------------
    def _scrape_capterra(self, page):
        page_num = 1
        while True:
            # Capterra URL structure
            url = f"https://www.capterra.com/p/{self.company}/reviews/?page={page_num}"
            print(f"Navigating to {url}")
            page.goto(url, timeout=60000)

            try:
                page.wait_for_selector('div.review-card, div.review', timeout=15000)
            except:
                print("Content not found on Capterra.")
                break

            review_elements = page.query_selector_all('div.review-card')
            if not review_elements:
                 review_elements = page.query_selector_all('div.review')

            if not review_elements:
                break
            
            found_on_page = 0
            for element in review_elements:
                try:
                    # Selectors for Capterra
                    date_el = element.query_selector('.review-card-header__date, .date')
                    if not date_el: continue
                    
                    # Capterra often says "Written on Sep 12, 2023"
                    date_text = date_el.inner_text().replace("Written on ", "")
                    if not self._valid_date(date_text):
                        continue

                    title_el = element.query_selector('h3, .review-card-title')
                    title = title_el.inner_text() if title_el else "No Title"

                    review_el = element.query_selector('.review-card-text, .review-text')
                    review_text = review_el.inner_text() if review_el else ""
                    
                    self.reviews.append({
                        "title": title,
                        "review": review_text[:200] + "...",
                        "date": date_text,
                        "source": "Capterra"
                    })
                    found_on_page += 1
                except Exception:
                    continue

            print(f"Found {found_on_page} valid reviews on page {page_num}")
            
            next_button = page.query_selector('button[aria-label="Next Page"]')
            if not next_button: # Or check if disabled
                 break
                 
            page_num += 1
            time.sleep(3)

    # ---------------- TrustRadius ----------------
    def _scrape_trustradius(self, page):
        # TrustRadius uses a different structure, often loading json payload or complex React
        url = f"https://www.trustradius.com/products/{self.company}/reviews"
        print(f"Navigating to {url}")
        page.goto(url, timeout=60000)
        
        try:
             page.wait_for_selector('div.review, article', timeout=15000)
        except:
             print("TrustRadius content not found.")
             return

        review_elements = page.query_selector_all('article.review, div.review')
        for element in review_elements:
             try:
                date_el = element.query_selector('time')
                if not date_el: continue
                date_str = date_el.get_attribute('datetime')
                if not self._valid_date(date_str): continue
                
                title = element.query_selector('h3').inner_text()
                
                self.reviews.append({
                    "title": title,
                    "review": "Content...",
                    "date": date_str,
                    "source": "TrustRadius"
                })
             except: continue

def main():
    parser = argparse.ArgumentParser(description="Pulse Coding Assignment – Review Scraper (Playwright Edition)")
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
