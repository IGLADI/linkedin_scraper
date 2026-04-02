from linkedin_scraper import BrowserManager, login_with_credentials

SESSION_FILE = "linkedin_session.json"

async def create_session(email: str, password: str):
    async with BrowserManager(headless=True) as browser:
        await login_with_credentials(
            browser.page,
            email=email,
            password=password
        )
        await browser.save_session(SESSION_FILE)