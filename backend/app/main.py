from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import pdfplumber
import pandas as pd
import io
from typing import Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Financial Planner API", version="1.0.0")

# CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Financial Planner API", "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/upload-cas")
async def upload_cas_file(
    file: UploadFile = File(...),
    password: Optional[str] = None
):
    """
    Upload and parse NSDL CAS PDF file
    """
    try:
        # Validate file type
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")
        
        # Read file content
        file_content = await file.read()
        
        # Parse PDF
        portfolio_data = parse_cas_pdf(file_content, password)
        
        return JSONResponse(content={
            "status": "success",
            "message": "CAS file processed successfully",
            "data": portfolio_data
        })
        
    except Exception as e:
        logger.error(f"Error processing CAS file: {str(e)}")
        if "password" in str(e).lower():
            return JSONResponse(
                status_code=400,
                content={
                    "status": "error",
                    "message": "Password required or incorrect password",
                    "error_type": "password_required"
                }
            )
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

def parse_cas_pdf(file_content: bytes, password: Optional[str] = None) -> dict:
    """
    Parse CAS PDF and extract portfolio data
    """
    try:
        # Try to open PDF with password
        with pdfplumber.open(io.BytesIO(file_content), password=password) as pdf:
            text = ""
            for page in pdf.pages:
                text += page.extract_text() or ""
            
            # Basic portfolio data extraction (simplified for now)
            portfolio_data = {
                "total_pages": len(pdf.pages),
                "has_content": len(text) > 0,
                "extracted_text_length": len(text),
                "holdings": extract_holdings(text),
                "summary": {
                    "total_equity_value": 0,
                    "total_mutual_fund_value": 0,
                    "asset_allocation": {}
                }
            }
            
            return portfolio_data
            
    except Exception as e:
        if "password" in str(e).lower() or "decrypt" in str(e).lower():
            raise Exception("Password required or incorrect password provided")
        raise e

def extract_holdings(text: str) -> dict:
    """
    Extract holdings from CAS text (simplified implementation)
    """
    # This is a simplified extraction - in reality, you'd need more sophisticated parsing
    holdings = {
        "equity": [],
        "mutual_funds": [],
        "bonds": [],
        "other": []
    }
    
    # Add basic parsing logic here
    # For now, return empty structure
    return holdings

@app.post("/analyze-portfolio")
async def analyze_portfolio(portfolio_data: dict):
    """
    Analyze portfolio and provide insights
    """
    try:
        analysis = {
            "asset_allocation": calculate_asset_allocation(portfolio_data),
            "sector_concentration": analyze_sector_concentration(portfolio_data),
            "recommendations": generate_basic_recommendations(portfolio_data)
        }
        
        return JSONResponse(content={
            "status": "success",
            "analysis": analysis
        })
        
    except Exception as e:
        logger.error(f"Error analyzing portfolio: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error analyzing portfolio: {str(e)}")

def calculate_asset_allocation(portfolio_data: dict) -> dict:
    """Calculate asset allocation percentages"""
    # Simplified implementation
    return {
        "equity": 60.0,
        "debt": 30.0,
        "others": 10.0
    }

def analyze_sector_concentration(portfolio_data: dict) -> dict:
    """Analyze sector-wise concentration"""
    # Simplified implementation
    return {
        "IT": 25.0,
        "Banking": 20.0,
        "Healthcare": 15.0,
        "Others": 40.0
    }

def generate_basic_recommendations(portfolio_data: dict) -> list:
    """Generate basic investment recommendations"""
    return [
        "Consider diversifying your IT sector exposure",
        "Add more debt instruments for balanced allocation",
        "Review underperforming mutual funds"
    ]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)