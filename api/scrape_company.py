#!/usr/bin/env python3
import asyncio
from linkedin_scraper.scrapers.company import CompanyScraper
from linkedin_scraper.core.browser import BrowserManager


async def scrape_company(company_url: str):
    async with BrowserManager(headless=True) as browser:
        await browser.load_session("linkedin_session.json")

        scraper = CompanyScraper(browser.page)
        company = await scraper.scrape(company_url)

        return {
            "name": company.name,
            "company_id": company.company_id,
            "website": company.website
        }