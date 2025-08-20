# main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import os
from analyzer import analyze_app_reviews

app = FastAPI()

# Allow CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # you can restrict to your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "App Analyzer Backend is running"}


@app.get("/analyze")
def analyze(app_id: str):
    try:
        results = analyze_app_reviews(app_id)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/download_csv")
def download_csv(app_id: str):
    csv_filename = f"cleaned_reviews_{app_id}.csv"
    if os.path.exists(csv_filename):
        return FileResponse(
            path=csv_filename,
            media_type="text/csv",
            filename=csv_filename
        )
    else:
        raise HTTPException(status_code=404, detail="CSV file not found. Run /analyze first.")
