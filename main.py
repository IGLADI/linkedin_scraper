# Build with:
# python3 -m venv .venv && source .venv/bin/activate && python3 -m pip install --upgrade pip && python3 -m pip install -r requirements-dev.txt && python3 -m pip install -e .
from fastapi import FastAPI, Query, HTTPException
from api.scrape_jobs import scrape_jobs
from api.scrape_person import scrape_person
from api.create_session import create_session

# uvicorn main:app --host 0.0.0.0 --port 9000
app = FastAPI()

# curl -X POST "http://localhost:9000/auth/linkedin/refresh?email=test%40example.uk&password=%23uGfoFZSz6w4hQ9P" (needs encoding)
@app.post("/auth/linkedin/refresh")
async def refresh_linkedin_session(
    email: str = Query(...),
    password: str = Query(...)
):
    try:
        await create_session(email=email, password=password)
        return {"status": True, "message": "LinkedIn session saved"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# curl "http://localhost:9000/jobs?keywords=software%20engineer&country=Toronto&limit=5"
@app.get("/jobs")
async def get_jobs(
    keywords: str = Query(...),
    country: str = Query(...),
    limit: int = Query(5, ge=1, le=500)
):
    try:
        result = await scrape_jobs(
            keywords=keywords,
            location=country,
            limit=limit
        )
        return {
            "keywords": keywords,
            "country": country,
            "limit": limit,
            **result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# curl "http://localhost:9000/person?profile_url=https%3A%2F%2Fwww.linkedin.com%2Fin%2Fwilliamhgates%2F&scrape_education=true&scrape_company_url=true"
@app.get("/person")
async def get_person(
    profile_url: str = Query(...),
    scrape_company_url: bool = Query(False),
    scrape_education: bool = Query(False),
    scrape_skills: bool = Query(True),
    scrape_certifications: bool = Query(True),
    scrape_languages: bool = Query(True),
):
    try:
        result = await scrape_person(
            profile_url=profile_url,
            scrape_company_url=scrape_company_url,
            scrape_education=scrape_education,
            scrape_skills=scrape_skills,
            scrape_certifications=scrape_certifications,
            scrape_languages=scrape_languages,
        )
        return {
            "profile_url": profile_url,
            "scrape_company_url": scrape_company_url,
            "scrape_education": scrape_education,
            "scrape_skills": scrape_skills,
            "scrape_certifications": scrape_certifications,
            "scrape_languages": scrape_languages,
            **result,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
