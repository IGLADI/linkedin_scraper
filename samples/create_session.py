import asyncio
import os
from dotenv import load_dotenv
from linkedin_scraper import BrowserManager, login_with_credentials

# Load the environment variables from the .env file in the root folder
load_dotenv()

async def login():
    # Fetch credentials
    email = os.getenv("LINKEDIN_EMAIL")
    password = os.getenv("LINKEDIN_PASSWORD")
    
    if not email or not password:
        print("❌ Error: Missing credentials.")
        print("Please make sure you have a .env file with LINKEDIN_EMAIL and LINKEDIN_PASSWORD set.")
        return

    print("==================================================")
    print("🤖 Auto-Login Session Creator")
    print("==================================================")
    
    # Keeping headless=False so you can visually verify if LinkedIn throws a CAPTCHA
    async with BrowserManager(headless=False) as browser:
        print(f"Attempting to automatically log in as {email}...")
        
        try:
            # The library's built-in automatic login
            await login_with_credentials(
                browser.page,
                email=email,
                password=password
            )
            
            # Save the session matching the filename we set in test.py
            session_file = "linkedin_session.json"
            await browser.save_session(session_file)
            
            print(f"✅ Success! Session saved to {session_file}")
            print("==================================================")
            
        except Exception as e:
            print(f"\n❌ Login failed: {e}")
            print("LinkedIn might have blocked the login or required a CAPTCHA.")

if __name__ == "__main__":
    asyncio.run(login())