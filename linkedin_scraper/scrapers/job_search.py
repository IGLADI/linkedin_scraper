"""
Job search scraper for LinkedIn.

Searches for jobs on LinkedIn and extracts job URLs.
"""
import logging
from typing import Optional, List
from urllib.parse import urlencode
from playwright.async_api import Page

from ..callbacks import ProgressCallback, SilentCallback
from .base import BaseScraper

logger = logging.getLogger(__name__)


class JobSearchScraper(BaseScraper):
    """
    Scraper for LinkedIn job search results.
    
    Example:
        async with BrowserManager() as browser:
            scraper = JobSearchScraper(browser.page)
            job_urls = await scraper.search(
                keywords="software engineer",
                location="San Francisco",
                limit=10
            )
    """
    
    def __init__(self, page: Page, callback: Optional[ProgressCallback] = None):
        """
        Initialize job search scraper.
        
        Args:
            page: Playwright page object
            callback: Optional progress callback
        """
        super().__init__(page, callback or SilentCallback())
    
    async def scrape_current_page(self, limit_left: int) -> List[str]:
        await self.page.wait_for_selector('a[href*="/jobs/view/"]', timeout=10000)
        await self.wait_and_focus(3)

        count = await self.page.locator("li.scaffold-layout__list-item").count()
        for i in range(count):
            selector = f"li.scaffold-layout__list-item >> nth={i}"
            await self.scroll_element_into_view(selector)

        await self.wait_and_focus(2)
        return await self._extract_job_urls(limit_left)


    async def search(
        self,
        keywords: Optional[str] = None,
        location: Optional[str] = None,
        search_url: Optional[str] = None,
        limit: int = 25
    ) -> List[str]:
        logger.info(
            f"Starting job search: keywords='{keywords}', location='{location}', search_url='{search_url}'"
        )

        if search_url:
            search_url_to_use = search_url
        else:
            search_url_to_use = self._build_search_url(keywords, location)

        await self.callback.on_start("JobSearch", search_url_to_use)
        await self.navigate_and_wait(search_url_to_use)

        all_job_urls = []
        seen = set()

        while len(all_job_urls) < limit:
            try:
                job_urls = await self.scrape_current_page(limit - len(all_job_urls))
            except Exception as e:
                logger.warning(f"Failed to scrape current page: {e}")
                break

            for url in job_urls:
                if url not in seen:
                    seen.add(url)
                    all_job_urls.append(url)

            if len(all_job_urls) >= limit:
                break

            next_selector = 'button[aria-label="View next page"]'
            next_button = self.page.locator(next_selector).first

            if await next_button.count() == 0:
                logger.info("No next page button found")
                break

            try:
                await next_button.scroll_into_view_if_needed()
            except:
                pass

            clicked = await self.safe_click(next_selector, timeout=5000)
            if not clicked:
                logger.info("Could not click next page button")
                break

            try:
                await self.page.wait_for_load_state("domcontentloaded")
                await self.page.wait_for_timeout(1500)
            except:
                pass

        await self.callback.on_progress(f"Found {len(all_job_urls)} job URLs", 90)
        return all_job_urls[:limit]
    
    def _build_search_url(
        self,
        keywords: Optional[str] = None,
        location: Optional[str] = None
    ) -> str:
        """Build LinkedIn job search URL with parameters."""
        base_url = "https://www.linkedin.com/jobs/search/"
        
        params = {}
        if keywords:
            params['keywords'] = keywords
        if location:
            params['location'] = location
        
        if params:
            return f"{base_url}?{urlencode(params)}"
        return base_url
    
    async def _extract_job_urls(self, limit: int) -> List[str]:
        """
        Extract job URLs from search results.
        
        Args:
            limit: Maximum number of URLs to extract
            
        Returns:
            List of job posting URLs
        """
        job_urls = []
        
        try:
            # Find all job cards/links
            job_links = await self.page.locator('a[href*="/jobs/view/"]').all()
            
            seen_urls = set()
            for link in job_links:
                if len(job_urls) >= limit:
                    break
                
                try:
                    href = await link.get_attribute('href')
                    if href and '/jobs/view/' in href:
                        # Clean URL (remove query params)
                        clean_url = href.split('?')[0] if '?' in href else href
                        
                        # Ensure full URL
                        if not clean_url.startswith('http'):
                            clean_url = f"https://www.linkedin.com{clean_url}"
                        
                        # Avoid duplicates
                        if clean_url not in seen_urls:
                            job_urls.append(clean_url)
                            seen_urls.add(clean_url)
                except Exception as e:
                    logger.debug(f"Error extracting job URL: {e}")
                    continue
        
        except Exception as e:
            logger.warning(f"Error extracting job URLs: {e}")
        
        return job_urls
