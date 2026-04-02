"""Person/Profile scraper for LinkedIn."""

import logging
import re
from typing import Optional, List
from urllib.parse import urljoin
from playwright.async_api import Page

from .base import BaseScraper
from ..models import Person, Experience, Education
from ..callbacks import ProgressCallback
from ..core.exceptions import ScrapingError

logger = logging.getLogger(__name__)

class PersonScraper(BaseScraper):
    """Async scraper for LinkedIn person profiles."""

    def __init__(self, page: Page, callback: Optional[ProgressCallback] = None):
        super().__init__(page, callback)

    async def scrape(
        self, 
        linkedin_url: str,
        scrape_company_url: bool = False,
        scrape_education: bool = False,
        scrape_skills: bool = True,
        scrape_certifications: bool = True,
        scrape_languages: bool = True
    ) -> Person:
        await self.callback.on_start("person", linkedin_url)

        try:
            await self.navigate_and_wait(linkedin_url)
            await self.ensure_logged_in()
            await self.page.wait_for_selector("main", timeout=10000)
            await self.wait_and_focus(1)

            name, location = await self._get_name_and_location()
            headline = await self._get_headline()
            about = await self._get_about()
            await self.callback.on_progress("Got basic profile data", 30)

            await self.scroll_page_to_half()
            await self.scroll_page_to_bottom(pause_time=0.5, max_scrolls=2)

            experiences = await self._get_experiences(linkedin_url, scrape_company_url)
            await self.callback.on_progress(f"Got {len(experiences)} experiences", 60)

            educations = await self._get_educations(linkedin_url) if scrape_education else []
            skills = await self._get_skills(linkedin_url) if scrape_skills else []
            certifications = await self._get_simple_list(linkedin_url, "certifications") if scrape_certifications else []
            languages = await self._get_languages(linkedin_url) if scrape_languages else []

            person = Person(
                linkedin_url=linkedin_url,
                name=name,
                headline=headline,
                location=location,
                about=about,
                experiences=experiences,
                educations=educations,
                skills=skills,
                certifications=certifications,
                languages=languages,
                open_to_work=False,
                interests=[],
                accomplishments=[],
                contacts=[]
            )

            await self.callback.on_progress("Scraping complete", 100)
            await self.callback.on_complete("person", person)
            return person

        except Exception as e:
            await self.callback.on_error(e)
            raise ScrapingError(f"Failed to scrape person profile: {e}")

    async def _get_name_and_location(self) -> tuple[str, Optional[str]]:
        try:
            name = await self.safe_extract_text("h1", default="Unknown")
            location = await self.safe_extract_text(".text-body-small.inline.t-black--light.break-words", default="")
            return name, location if location else None
        except Exception:
            return "Unknown", None

    async def _get_headline(self) -> Optional[str]:
        try:
            headline = await self.safe_extract_text("div.text-body-medium.break-words", default="")
            return headline.strip() if headline else None
        except Exception:
            return None

    async def _get_about(self) -> Optional[str]:
        try:
            profile_cards = await self.page.locator('[data-view-name="profile-card"]').all()
            for card in profile_cards:
                card_text = await card.inner_text()
                if card_text.strip().startswith("About"):
                    about_spans = await card.locator('span[aria-hidden="true"]').all()
                    if len(about_spans) > 1:
                        about_text = await about_spans[1].text_content()
                        return about_text.strip() if about_text else None
            return None
        except Exception:
            return None

    async def _extract_unique_texts_from_element(self, element) -> list[str]:
        text_elements = await element.locator('span[aria-hidden="true"], div > span').all()
        if not text_elements:
            text_elements = await element.locator('span, div').all()
        
        seen_texts = set()
        unique_texts = []
        for el in text_elements:
            text = await el.text_content()
            if text and text.strip():
                text = text.strip()
                if text not in seen_texts and not any(text in t or t in text for t in seen_texts if len(t) > 3):
                    seen_texts.add(text)
                    unique_texts.append(text)
        return unique_texts

    def _find_date_index(self, texts: list[str]) -> int:
        """Finds the index of the string containing the employment duration (e.g., 'Jan 2020 - Present')."""
        for i, text in enumerate(texts):
            # Looks for " - " alongside a year (4 digits) or the word "Present"
            if " - " in text and (re.search(r'\b\d{4}\b', text) or "Present" in text):
                return i
        return -1

    async def _get_experiences(self, base_url: str, scrape_company_url: bool) -> list[Experience]:
        experiences = []
        try:
            exp_url = f"{base_url.rstrip('/')}/details/experience/"
            await self.navigate_and_wait(exp_url)
            await self.page.wait_for_selector("main", timeout=5000)
            await self.scroll_page_to_bottom(pause_time=0.5, max_scrolls=5)

            main_list = self.page.locator('main ul').first
            if await main_list.count() == 0:
                return experiences
                
            list_items = await main_list.locator('xpath=./li').all()
            
            for item in list_items:
                company_url = None
                if scrape_company_url:
                    company_link = item.locator("a").first
                    if await company_link.count() > 0:
                        company_url = await company_link.get_attribute("href")
                
                unique_texts = await self._extract_unique_texts_from_element(item)
                if not unique_texts:
                    continue
                
                nested_container = item.locator(".pvs-list__container").first
                nested_lis = []
                if await nested_container.count() > 0:
                    nested_lis = await nested_container.locator('xpath=.//ul/li').all()
                    
                if len(nested_lis) > 0:
                    # Logic for multiple roles under the same company
                    company_name = unique_texts[0]
                    for nested_li in nested_lis:
                        nested_texts = await self._extract_unique_texts_from_element(nested_li)
                        date_idx = self._find_date_index(nested_texts)
                        
                        if date_idx >= 1:
                            pos_title = nested_texts[date_idx - 1]
                            times_str = nested_texts[date_idx]
                            from_date, to_date, duration = self._parse_work_times(times_str)
                            
                            # Safely extract location vs description
                            loc_str = nested_texts[date_idx + 1] if len(nested_texts) > date_idx + 1 else ""
                            is_location = len(loc_str) < 60 and not any(c in loc_str for c in ['·', '\n', '•']) and not loc_str.startswith('-')
                            loc = loc_str if is_location else None
                            
                            desc_start = date_idx + 2 if is_location else date_idx + 1
                            desc = "\n".join(nested_texts[desc_start:]) if len(nested_texts) > desc_start else None
                            
                            experiences.append(Experience(
                                position_title=pos_title,
                                institution_name=company_name,
                                linkedin_url=company_url,
                                from_date=from_date,
                                to_date=to_date,
                                duration=duration,
                                location=loc,
                                description=desc.strip() if desc else None
                            ))
                else:
                    # Logic for single roles
                    date_idx = self._find_date_index(unique_texts)
                    if date_idx >= 1:
                        pos_title = unique_texts[0]
                        comp_name = unique_texts[1] if date_idx >= 2 else unique_texts[0]
                        
                        times_str = unique_texts[date_idx]
                        from_date, to_date, duration = self._parse_work_times(times_str)
                        
                        loc_str = unique_texts[date_idx + 1] if len(unique_texts) > date_idx + 1 else ""
                        is_location = len(loc_str) < 60 and not any(c in loc_str for c in ['·', '\n', '•']) and not loc_str.startswith('-')
                        loc = loc_str if is_location else None
                        
                        desc_start = date_idx + 2 if is_location else date_idx + 1
                        desc = "\n".join(unique_texts[desc_start:]) if len(unique_texts) > desc_start else None
                        
                        experiences.append(Experience(
                            position_title=pos_title,
                            institution_name=comp_name,
                            linkedin_url=company_url,
                            from_date=from_date,
                            to_date=to_date,
                            duration=duration,
                            location=loc,
                            description=desc.strip() if desc else None
                        ))
        except Exception as e:
            logger.debug(f"Error extracting experiences: {e}")
            
        return experiences

    async def _get_skills(self, base_url: str) -> list[str]:
        skills_list = []
        try:
            url = f"{base_url.rstrip('/')}/details/skills/"
            await self.navigate_and_wait(url)
            await self.page.wait_for_selector("main", timeout=4000)
            
            # Increased scrolling to capture large skill lists (like the 40+ skills here)
            await self.scroll_page_to_bottom(pause_time=0.8, max_scrolls=6)

            list_items = await self.page.locator('main .pvs-list__paged-list-item').all()
            if not list_items:
                list_items = await self.page.locator('main ul > li').all()

            for item in list_items:
                # Grab the very first aria-hidden span inside the item. 
                # This inherently bypasses nested spans (like "Endorsed by X colleagues" or "Passed assessment")
                span = item.locator('span[aria-hidden="true"]').first
                
                if await span.count() > 0:
                    skill_name = await span.text_content()
                    if skill_name and skill_name.strip():
                        skill_name = skill_name.strip()
                        # Filter out navigation tabs
                        if skill_name.lower() not in ["all", "industry knowledge", "tools & technologies", "interpersonal skills", "other skills", "languages"]:
                            skills_list.append(skill_name)
        except Exception as e:
            logger.debug(f"Error occurred getting skills: {e}")
            
        return list(dict.fromkeys(skills_list))

    async def _get_languages(self, base_url: str) -> list[str]:
        languages = []
        try:
            url = f"{base_url.rstrip('/')}/details/languages/"
            await self.navigate_and_wait(url)
            await self.page.wait_for_selector("main", timeout=4000)
            await self.scroll_page_to_bottom(pause_time=0.5, max_scrolls=2)

            list_items = await self.page.locator('main .pvs-list__paged-list-item').all()
            if not list_items:
                list_items = await self.page.locator('main ul > li').all()

            for item in list_items:
                spans = await item.locator('span[aria-hidden="true"]').all()
                texts = []
                for span in spans:
                    text = await span.text_content()
                    if text and text.strip():
                        texts.append(text.strip())
                
                unique_texts = list(dict.fromkeys(texts))
                if unique_texts:
                    lang = unique_texts[0]
                    if len(unique_texts) > 1:
                        lang += f" ({unique_texts[1]})"
                    languages.append(lang)
        except Exception as e:
            logger.debug(f"Error occurred getting languages: {e}")
            
        return list(dict.fromkeys(languages))

    async def _get_simple_list(self, base_url: str, section: str) -> list[str]:
        items_list = []
        try:
            url = f"{base_url.rstrip('/')}/details/{section}/"
            await self.navigate_and_wait(url)
            await self.page.wait_for_selector("main", timeout=4000)
            await self.scroll_page_to_bottom(pause_time=0.5, max_scrolls=2)

            list_items = await self.page.locator('main .pvs-list__paged-list-item').all()
            if not list_items:
                list_items = await self.page.locator('main ul > li').all()

            for item in list_items:
                span = item.locator('span[aria-hidden="true"]').first
                if await span.count() > 0:
                    text = await span.text_content()
                    if text and text.strip():
                        items_list.append(text.strip())
        except Exception as e:
            logger.debug(f"Error occurred in {section}: {e}")
            
        return list(dict.fromkeys(items_list))

    def _parse_work_times(self, work_times: str) -> tuple[Optional[str], Optional[str], Optional[str]]:
        if not work_times:
            return None, None, None
            
        try:
            parts = work_times.split("·")
            times = parts[0].strip() if len(parts) > 0 else ""
            duration = parts[1].strip() if len(parts) > 1 else None

            if " - " in times:
                date_parts = times.split(" - ")
                from_date = date_parts[0].strip()
                to_date = date_parts[1].strip() if len(date_parts) > 1 else ""
            else:
                from_date = times
                to_date = ""
            return from_date, to_date, duration
        except Exception:
            return None, None, None

    async def _get_educations(self, base_url: str) -> list[Education]:
        return []