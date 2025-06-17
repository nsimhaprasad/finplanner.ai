from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import pdfplumber
import io
from typing import Optional, Dict, Any
import logging
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import multi-agent system
from .agents import FinancialOrchestrator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Financial Planner API", version="1.0.0")

# Initialize multi-agent orchestrator
orchestrator = FinancialOrchestrator()

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
    Upload and process NSDL CAS PDF file with multi-agent analysis
    """
    try:
        # Validate file type
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")
        
        # Read file content
        file_content = await file.read()
        
        # Extract text from PDF
        pdf_text = extract_pdf_text(file_content, password)
        
        # Process through multi-agent system (synchronous to avoid hanging)
        result_state = orchestrator.process_financial_planning_sync(
            pdf_content=pdf_text,
            user_responses={}  # Will be enhanced later for user questionnaire
        )
        
        # Debug: Log all errors
        logger.info(f"Total errors in result_state: {len(result_state.errors)}")
        for i, error in enumerate(result_state.errors):
            logger.info(f"Error {i}: {error}")
        
        # Check for fatal errors (not just warnings)
        fatal_errors = [error for error in result_state.errors 
                       if not any(keyword in error.lower() 
                                for keyword in ["timeout", "api key", "fallback", "mock data", 
                                              "no portfolio holdings", "no holdings available",
                                              "no field", "analysis", "parse", "json"])]
        
        logger.info(f"Fatal errors: {len(fatal_errors)}")
        logger.info(f"Analysis complete: {result_state.analysis_complete}")
        
        if fatal_errors:
            logger.error(f"Returning 400 due to fatal errors: {fatal_errors}")
            return JSONResponse(
                status_code=400,
                content={
                    "status": "error", 
                    "message": "; ".join(fatal_errors),
                    "errors": fatal_errors
                }
            )
        
        # Prepare warnings for non-fatal issues
        warnings = [error for error in result_state.errors 
                   if any(keyword in error.lower() 
                        for keyword in ["timeout", "api key", "fallback", "mock data"])]
        
        # Return comprehensive analysis
        logger.info("Returning successful response")
        return JSONResponse(content={
            "status": "success",
            "message": "CAS file processed and analyzed successfully" + 
                      (" (using mock data)" if warnings else ""),
            "warnings": warnings,
            "data": {
                "portfolio": {
                    "total_value": result_state.portfolio.total_value,
                    "asset_allocation": result_state.portfolio.asset_allocation,
                    "sector_allocation": result_state.portfolio.sector_allocation,
                    "holdings_count": len(result_state.portfolio.holdings),
                    "top_holdings": [
                        {
                            "name": holding.name,
                            "symbol": holding.symbol,
                            "value": holding.current_value,
                            "asset_type": holding.asset_type
                        }
                        for holding in sorted(result_state.portfolio.holdings, 
                                            key=lambda x: x.current_value, reverse=True)[:5]
                    ]
                },
                "analysis": {
                    "risk_profile": {
                        "risk_tolerance": result_state.risk_profile.risk_tolerance,
                        "risk_score": result_state.risk_profile.score,
                        "investment_horizon": result_state.risk_profile.investment_horizon
                    },
                    "market_context": {
                        "sentiment": result_state.market_data.market_sentiment,
                        "sector_outlook": result_state.market_data.sector_outlook
                    },
                    "recommendations": {
                        "asset_rebalancing": result_state.recommendations.asset_rebalancing,
                        "sector_adjustments": result_state.recommendations.sector_adjustments,
                        "investment_suggestions": result_state.recommendations.investment_suggestions,
                        "action_items": result_state.recommendations.action_items
                    }
                },
                "workflow_status": orchestrator.get_workflow_status(result_state)
            }
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

def extract_pdf_text(file_content: bytes, password: Optional[str] = None) -> str:
    """
    Extract text content from PDF file
    """
    try:
        # Try to open PDF with password
        with pdfplumber.open(io.BytesIO(file_content), password=password) as pdf:
            text = ""
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            
            if not text.strip():
                raise Exception("No text content found in PDF")
                
            return text
            
    except Exception as e:
        if "password" in str(e).lower() or "decrypt" in str(e).lower():
            raise Exception("Password required or incorrect password provided")
        raise e

@app.post("/risk-assessment")
async def risk_assessment(user_responses: Dict[str, Any]):
    """
    Standalone risk assessment endpoint
    """
    try:
        from .agents.risk_profiler_agent import RiskProfilerAgent
        from .agents.state import FinancialState
        
        # Create state with user responses
        state = FinancialState(user_responses=user_responses)
        
        # Run risk profiler
        risk_agent = RiskProfilerAgent()
        result_state = risk_agent.process(state)
        
        return JSONResponse(content={
            "status": "success",
            "risk_profile": {
                "risk_tolerance": result_state.risk_profile.risk_tolerance,
                "risk_score": result_state.risk_profile.score,
                "investment_horizon": result_state.risk_profile.investment_horizon
            }
        })
        
    except Exception as e:
        logger.error(f"Risk assessment failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Risk assessment failed: {str(e)}")

@app.get("/market-outlook")
async def get_market_outlook():
    """
    Get current market outlook and trends
    """
    try:
        from .agents.market_outlook_agent import MarketOutlookAgent
        from .agents.state import FinancialState
        
        # Create empty state
        state = FinancialState()
        
        # Run market outlook agent
        market_agent = MarketOutlookAgent()
        result_state = market_agent.process(state)
        
        return JSONResponse(content={
            "status": "success",
            "market_data": {
                "sentiment": result_state.market_data.market_sentiment,
                "sector_outlook": result_state.market_data.sector_outlook,
                "market_indices": result_state.market_data.market_indices,
                "last_updated": result_state.market_data.last_updated
            }
        })
        
    except Exception as e:
        logger.error(f"Market outlook failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Market outlook failed: {str(e)}")

@app.get("/agent-status")
async def get_agent_status():
    """
    Get information about available agents and their capabilities
    """
    return {
        "agents": {
            "cas_parser": "Extracts portfolio data from CAS PDF files",
            "portfolio_analyzer": "Analyzes portfolio composition and risks",
            "market_outlook": "Provides current market trends and outlook",
            "risk_profiler": "Assesses user risk tolerance and profile",
            "financial_advisor": "Generates personalized investment recommendations"
        },
        "workflow": "Sequential processing through all agents",
        "features": [
            "LLM-powered PDF parsing",
            "Real-time market data integration",
            "Personalized risk assessment",
            "Comprehensive financial recommendations"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)