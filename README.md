# Market Data Web Scraping and Analysis Tool

This project automates competitor market research by scraping product and review
signals from multiple websites, storing structured data, and producing
analysis-ready insights.

## Objectives Covered

- Build a Python-based web scraping tool (`requests` + `BeautifulSoup`).
- Collect data from three market-relevant web sources.
- Store output in CSV and Excel formats.
- Analyze pricing/rating data using `pandas` and `matplotlib`.
- Generate actionable insight artifacts for decision-making.

## Project Structure

- `src/market_scraper.py`: Main scraper + analyzer workflow.
- `requirements.txt`: Python dependencies.
- `output/`: Generated artifacts after execution.

## Data Sources (Default)

1. `https://books.toscrape.com/` (book prices and ratings)
2. `https://webscraper.io/test-sites/e-commerce/static/computers/laptops`
3. `https://webscraper.io/test-sites/e-commerce/static/phones/touch`

> Note: These default sources are public demo pages intended for scraping practice.
> Replace with approved production targets for real competitor intelligence.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
python src/market_scraper.py
```

## Generated Outputs

After a successful run, the `output/` directory contains:

- `market_data.csv` and `market_data.xlsx`: Unified scraped dataset.
- `price_summary.csv`: Pricing aggregation by source.
- `top_rated_products.csv`: Top-rated product shortlist.
- `insights.md`: Actionable summary and recommendations.
- `price_distribution.png`: Price distribution visualization by source.

## Scope Mapping

- **Research on targets**: documented default websites and how to swap sources.
- **Implementation**: complete scraping pipeline in Python.
- **Storage + analysis**: CSV/Excel + pandas aggregation + matplotlib chart.
- **Documentation**: setup, execution, and output description in this README.
