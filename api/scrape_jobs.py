#!/usr/bin/env python3
import asyncio
from typing import Optional

from linkedin_scraper.scrapers.job_search import JobSearchScraper
from linkedin_scraper.scrapers.job import JobScraper
from linkedin_scraper.core.browser import BrowserManager

async def scrape_jobs(
    limit: int = 5,
    keywords: Optional[str] = None,
    location: Optional[str] = None,
    search_url: Optional[str] = None,
):
    if search_url:
        if keywords or location:
            raise ValueError("Provide either search_url or keywords+location, not both.")
    else:
        if not keywords or not location:
            raise ValueError("Provide both keywords and location, or provide search_url.")

    async with BrowserManager(headless=True) as browser:
        await browser.load_session("linkedin_session.json")

        search_scraper = JobSearchScraper(browser.page)
        job_urls = await search_scraper.search(
            keywords=keywords,
            location=location,
            search_url=search_url,
            limit=limit,
        )

        jobs = []
        job_scraper = JobScraper(browser.page)

        for url in job_urls:
            job = await job_scraper.scrape(url)
            jobs.append({
                "url": url,
                "job_title": job.job_title,
                "company": job.company,
                "company_url": job.company_linkedin_url,
                "job_description": job.job_description
            })

        return {
            "count": len(jobs),
            "jobs": jobs,
        }