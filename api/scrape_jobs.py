#!/usr/bin/env python3
import asyncio
from linkedin_scraper.scrapers.job_search import JobSearchScraper
from linkedin_scraper.scrapers.job import JobScraper
from linkedin_scraper.core.browser import BrowserManager

async def scrape_jobs(
    keywords: str, 
    location: str, 
    limit: int = 5
):
    async with BrowserManager(headless=True) as browser:
        await browser.load_session("linkedin_session.json")

        search_scraper = JobSearchScraper(browser.page)
        job_urls = await search_scraper.search(
            keywords=keywords,
            location=location,
            limit=limit
        )

        jobs = []
        job_scraper = JobScraper(browser.page)

        for url in job_urls:
            job = await job_scraper.scrape(url)
            jobs.append({
                "url": url,
                "job_title": job.job_title,
                "company": job.company,
                # "location": job.location,
                # "posted_date": job.posted_date,
                # "applicant_count": job.applicant_count,
                "job_description": job.job_description,
            })

        return {
            "count": len(jobs),
            "jobs": jobs,
        }