"""Market intelligence scraper and analyzer.

This module scrapes product and review data from predefined public demo pages,
stores normalized data, and generates quick competitor insights.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import matplotlib.pyplot as plt
import pandas as pd
import requests
from bs4 import BeautifulSoup


@dataclass(frozen=True)
class TargetSource:
    """Represents a source webpage and parser function."""

    name: str
    url: str
    parser: Callable[[str, str], list[dict]]


class MarketScraper:
    """Scrapes product data from multiple websites and builds insights."""

    def __init__(self, output_dir: str = "output", timeout: int = 20) -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.timeout = timeout

        self.sources: list[TargetSource] = [
            TargetSource(
                name="BooksToScrape",
                url="https://books.toscrape.com/",
                parser=self._parse_books_to_scrape,
            ),
            TargetSource(
                name="WebScraperLaptops",
                url="https://webscraper.io/test-sites/e-commerce/static/computers/laptops",
                parser=self._parse_webscraper_catalog,
            ),
            TargetSource(
                name="WebScraperPhones",
                url="https://webscraper.io/test-sites/e-commerce/static/phones/touch",
                parser=self._parse_webscraper_catalog,
            ),
        ]

    def scrape_all(self) -> pd.DataFrame:
        """Scrape all sources and return a normalized DataFrame."""
        all_rows: list[dict] = []

        for source in self.sources:
            print(f"Scraping {source.name}: {source.url}")
            html = self._get_html(source.url)
            rows = source.parser(source.name, html)
            print(f"  -> collected {len(rows)} rows")
            all_rows.extend(rows)

        if not all_rows:
            raise RuntimeError("No rows were scraped from any source.")

        df = pd.DataFrame(all_rows)
        df["price"] = pd.to_numeric(df["price"], errors="coerce")
        df["review_count"] = pd.to_numeric(df["review_count"], errors="coerce")
        df["rating"] = pd.to_numeric(df["rating"], errors="coerce")
        return df

    def save_data(self, df: pd.DataFrame) -> tuple[Path, Path]:
        """Persist data as CSV and Excel."""
        csv_path = self.output_dir / "market_data.csv"
        excel_path = self.output_dir / "market_data.xlsx"
        df.to_csv(csv_path, index=False)
        df.to_excel(excel_path, index=False)
        return csv_path, excel_path

    def analyze(self, df: pd.DataFrame) -> dict[str, pd.DataFrame | str]:
        """Run basic competitor and pricing analysis."""
        price_summary = (
            df.groupby("source", dropna=False)["price"]
            .agg(["count", "mean", "min", "max"])
            .sort_values("mean", ascending=False)
            .round(2)
        )

        top_rated = (
            df.sort_values(["rating", "review_count"], ascending=False)
            .loc[:, ["source", "product_name", "price", "rating", "review_count", "url"]]
            .head(10)
        )

        low_price_high_rating = df[(df["price"] <= df["price"].quantile(0.25)) & (df["rating"] >= 4)]

        insight_lines = [
            "# Market Insights",
            "",
            f"- Total products scraped: **{len(df)}**",
            f"- Sources covered: **{df['source'].nunique()}**",
            "",
            "## Pricing Summary by Source",
            price_summary.to_markdown(),
            "",
            "## Actionable Insights",
            (
                f"- Highest average pricing appears in **{price_summary.index[0]}** "
                f"(avg ${price_summary.iloc[0]['mean']:.2f})."
            ),
            (
                f"- Found **{len(low_price_high_rating)}** products in the lowest 25% price band "
                "with rating >= 4, which can be used to benchmark value offerings."
            ),
            (
                "- Review-heavy items should be prioritized for sentiment mining in a next phase "
                "(export includes review counts where available)."
            ),
        ]

        return {
            "price_summary": price_summary,
            "top_rated": top_rated,
            "insights_markdown": "\n".join(insight_lines),
        }

    def save_analysis(self, analysis: dict[str, pd.DataFrame | str]) -> tuple[Path, Path, Path]:
        """Save analysis artifacts to output directory."""
        summary_csv = self.output_dir / "price_summary.csv"
        top_rated_csv = self.output_dir / "top_rated_products.csv"
        insights_md = self.output_dir / "insights.md"

        analysis["price_summary"].to_csv(summary_csv)
        analysis["top_rated"].to_csv(top_rated_csv, index=False)
        insights_md.write_text(str(analysis["insights_markdown"]), encoding="utf-8")
        return summary_csv, top_rated_csv, insights_md

    def plot_price_distribution(self, df: pd.DataFrame) -> Path:
        """Generate and save a boxplot of price distribution by source."""
        plot_path = self.output_dir / "price_distribution.png"
        plt.figure(figsize=(10, 6))
        df.boxplot(column="price", by="source", grid=False)
        plt.title("Price Distribution by Source")
        plt.suptitle("")
        plt.xlabel("Source")
        plt.ylabel("Price")
        plt.tight_layout()
        plt.savefig(plot_path, dpi=150)
        plt.close()
        return plot_path

    def _get_html(self, url: str) -> str:
        response = requests.get(url, timeout=self.timeout)
        response.raise_for_status()
        return response.text

    @staticmethod
    def _parse_books_to_scrape(source_name: str, html: str) -> list[dict]:
        soup = BeautifulSoup(html, "html.parser")
        rows: list[dict] = []

        star_map = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}

        for article in soup.select("article.product_pod"):
            title_tag = article.select_one("h3 a")
            price_tag = article.select_one("p.price_color")
            rating_tag = article.select_one("p.star-rating")

            if not title_tag or not price_tag or not rating_tag:
                continue

            rating_class = next((c for c in rating_tag.get("class", []) if c in star_map), None)
            rows.append(
                {
                    "source": source_name,
                    "product_name": title_tag.get("title", "").strip(),
                    "price": price_tag.text.replace("£", "").strip(),
                    "rating": star_map.get(rating_class, None),
                    "review_count": None,
                    "category": "Books",
                    "url": "https://books.toscrape.com/",
                }
            )

        return rows

    @staticmethod
    def _parse_webscraper_catalog(source_name: str, html: str) -> list[dict]:
        soup = BeautifulSoup(html, "html.parser")
        rows: list[dict] = []

        for card in soup.select("div.thumbnail"):
            name_tag = card.select_one("a.title")
            price_tag = card.select_one("h4.price")
            rating_tag = card.select_one("div.ratings p[data-rating]")
            reviews_tag = card.select_one("div.ratings p.pull-right")

            if not name_tag or not price_tag:
                continue

            rating = rating_tag.get("data-rating") if rating_tag else None
            review_count = None
            if reviews_tag:
                review_count = reviews_tag.text.split()[0]

            rows.append(
                {
                    "source": source_name,
                    "product_name": name_tag.get("title", "").strip() or name_tag.text.strip(),
                    "price": price_tag.text.replace("$", "").strip(),
                    "rating": rating,
                    "review_count": review_count,
                    "category": source_name.replace("WebScraper", ""),
                    "url": f"https://webscraper.io{name_tag.get('href', '')}",
                }
            )

        return rows


def main() -> None:
    scraper = MarketScraper(output_dir="output")
    df = scraper.scrape_all()
    csv_path, excel_path = scraper.save_data(df)

    analysis = scraper.analyze(df)
    summary_csv, top_rated_csv, insights_md = scraper.save_analysis(analysis)
    plot_path = scraper.plot_price_distribution(df)

    print("\nArtifacts generated:")
    for path in [csv_path, excel_path, summary_csv, top_rated_csv, insights_md, plot_path]:
        print(f"- {path}")


if __name__ == "__main__":
    main()
