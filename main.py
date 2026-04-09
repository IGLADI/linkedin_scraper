# Build with:
# python3 -m venv .venv && source .venv/bin/activate && python3 -m pip install --upgrade pip && python3 -m pip install -r requirements-dev.txt && python3 -m pip install -e .
from fastapi import FastAPI, Query, HTTPException
from typing import Optional

from api.create_session import create_session
from api.scrape_jobs import scrape_jobs
from api.scrape_company import scrape_company
from api.scrape_person import scrape_person

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
# curl "http://localhost:9000/jobs?search_url=https%3A%2F%2Fwww.linkedin.com%2Fjobs%2Fsearch%2F%3Ff_C%3D165953%26geoId%3D100565514"
@app.get("/jobs")
async def get_jobs(
    keywords: Optional[str] = Query(None),
    country: Optional[str] = Query(None),
    search_url: Optional[str] = Query(None),
    limit: int = Query(5, ge=1, le=500),
):
    try:
        if search_url:
            if keywords or country:
                raise HTTPException(
                    status_code=400,
                    detail="Provide either search_url or keywords+country, not both."
                )
            result = await scrape_jobs(
                search_url=search_url,
                limit=limit
            )
            return {
                "search_url": search_url,
                "limit": limit,
                **result
            }

        if not keywords or not country:
            raise HTTPException(
                status_code=400,
                detail="Provide both keywords and country, or provide search_url."
            )

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

# curl "http://localhost:9000/company?company_url=https%3A%2F%2Fwww.linkedin.com%2Fcompany%2Fmicrosoft%2F"
@app.get("/company")
async def get_company(
    company_url: str = Query(...),
):
    try:
        result = await scrape_company(
            company_url=company_url
        )
        return {
            "company_url": company_url,
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
