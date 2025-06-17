from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class Holding(BaseModel):
    """Individual holding information"""
    symbol: str
    name: str
    quantity: float
    current_value: float
    sector: Optional[str] = None
    asset_type: str  # equity, mutual_fund, bond, etc.


class PortfolioData(BaseModel):
    """Portfolio holdings and analysis"""
    holdings: List[Holding] = Field(default_factory=list)
    total_value: float = 0.0
    asset_allocation: Dict[str, float] = Field(default_factory=dict)
    sector_allocation: Dict[str, float] = Field(default_factory=dict)
    analysis: Optional[Dict[str, Any]] = None


class MarketData(BaseModel):
    """Market outlook and trends"""
    market_sentiment: str = "neutral"  # bullish, bearish, neutral
    sector_outlook: Dict[str, str] = Field(default_factory=dict)
    market_indices: Dict[str, float] = Field(default_factory=dict)
    last_updated: Optional[str] = None
    analysis: Optional[Dict[str, Any]] = None


class RiskProfile(BaseModel):
    """User risk assessment"""
    risk_tolerance: str = "moderate"  # conservative, moderate, aggressive
    investment_horizon: str = "medium"  # short, medium, long
    age_group: Optional[str] = None
    income_stability: Optional[str] = None
    score: float = 0.0
    assessment: Optional[Dict[str, Any]] = None


class Recommendations(BaseModel):
    """Financial recommendations"""
    asset_rebalancing: List[str] = Field(default_factory=list)
    sector_adjustments: List[str] = Field(default_factory=list)
    investment_suggestions: List[str] = Field(default_factory=list)
    risk_warnings: List[str] = Field(default_factory=list)
    action_items: List[str] = Field(default_factory=list)
    detailed_advice: Optional[Dict[str, Any]] = None


class FinancialState(BaseModel):
    """Central state for the financial planning workflow"""
    
    # Input data
    pdf_content: Optional[str] = None
    user_responses: Dict[str, Any] = Field(default_factory=dict)
    
    # Agent outputs
    portfolio: PortfolioData = Field(default_factory=PortfolioData)
    market_data: MarketData = Field(default_factory=MarketData)
    risk_profile: RiskProfile = Field(default_factory=RiskProfile)
    recommendations: Recommendations = Field(default_factory=Recommendations)
    
    # Workflow control
    current_agent: str = "cas_parser"
    completed_agents: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    
    # Final output
    analysis_complete: bool = False
    final_report: Optional[Dict[str, Any]] = None