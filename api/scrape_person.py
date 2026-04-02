#!/usr/bin/env python3
import asyncio
from linkedin_scraper.scrapers.person import PersonScraper
from linkedin_scraper.core.browser import BrowserManager

async def scrape_person(
    profile_url: str,
    scrape_company_url: bool = False,
    scrape_education: bool = False,
    scrape_skills: bool = True,
    scrape_certifications: bool = True,
    scrape_languages: bool = True,
):
    async with BrowserManager(headless=True) as browser:
        await browser.load_session("linkedin_session.json")

        scraper = PersonScraper(browser.page)
        person = await scraper.scrape(
            linkedin_url=profile_url,
            scrape_company_url=scrape_company_url,
            scrape_education=scrape_education,
            scrape_skills=scrape_skills,
            scrape_certifications=scrape_certifications,
            scrape_languages=scrape_languages,
        )

        return {
            "url": profile_url,
            "name": person.name,
            "headline": person.headline,
            "location": person.location,
            "about": person.about,
            "experiences": [
                {
                    "position_title": exp.position_title,
                    "institution_name": exp.institution_name,
                    "linkedin_url": exp.linkedin_url,
                    "from_date": exp.from_date,
                    "to_date": exp.to_date,
                    "duration": exp.duration,
                    "location": exp.location,
                    "description": exp.description,
                }
                for exp in getattr(person, "experiences", [])
            ],
            "educations": [
                {
                    "school": edu.school,
                    "degree": edu.degree,
                    "field_of_study": edu.field_of_study,
                    "dates": edu.dates,
                }
                for edu in getattr(person, "educations", [])
            ],
            "skills": getattr(person, "skills", []),
            "certifications": getattr(person, "certifications", []),
            "languages": getattr(person, "languages", []),
        }