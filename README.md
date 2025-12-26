# Pulse Review Scraper

The assignment was to build a scraper for G2 and Capterra.

**Note**: This project uses **Playwright** to handle dynamic content and
anti-bot measures. However, sites like G2 and Capterra enforce strict
residential proxy and captcha requirements which may still block automated
access from data center IPs.

## Requirements

- Python 3.8+
- Playwright

## Installation

```bash
pip install -r requirements.txt
playwright install chromium
```

## Usage

```bash
python scraper.py --company hubspot --start_date 2024-01-01 --end_date 2024-06-30 --source g2
```

## Features

- **Playwright Integration**: Mimics a real browser to attempt bypassing basic
  blocking.
- **Modular Structure**: Easily extensible for other sources.
- **Trusted Sources**: G2, Capterra, and TrustRadius (bonus).

## Bonus

TrustRadius support is included via `--source trustradius`.
