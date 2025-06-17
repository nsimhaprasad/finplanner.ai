from langchain_core.prompts import ChatPromptTemplate
from .base_agent import BaseFinancialAgent
from .state import FinancialState, Recommendations
import json
import logging

logger = logging.getLogger(__name__)


class FinancialAdvisorAgent(BaseFinancialAgent):
    """Agent responsible for generating personalized financial recommendations"""
    
    def __init__(self):
        # Use Pro model for comprehensive financial advice (complex reasoning)
        super().__init__("financial_advisor", model="gemini-1.5-pro")
    
    def get_prompt_template(self) -> ChatPromptTemplate:
        return ChatPromptTemplate.from_messages([
            ("system", """You are a certified financial advisor specializing in Indian markets.
            Generate comprehensive, personalized financial advice based on:
            - Portfolio analysis
            - Risk profile
            - Market conditions
            - Financial goals
            
            Provide specific, actionable recommendations in JSON format:
            {{
                "asset_rebalancing": [
                    "Reduce equity allocation from 75% to 65%",
                    "Increase debt allocation to 25% for stability",
                    "Add 10% alternative investments (REITs, Gold)"
                ],
                "sector_adjustments": [
                    "Reduce IT sector exposure from 45% to 25%",
                    "Add FMCG and Healthcare exposure",
                    "Consider adding Banking sector ETF"
                ],
                "investment_suggestions": [
                    "SIP in Nifty 50 Index Fund: ₹10,000/month",
                    "Lump sum in Corporate Bond Fund: ₹2,00,000",
                    "Consider Tax Saving ELSS: ₹1,50,000"
                ],
                "risk_warnings": [
                    "High concentration in single sector increases volatility",
                    "Lack of debt instruments for downside protection"
                ],
                "action_items": [
                    "Set up emergency fund of ₹5,00,000",
                    "Review and rebalance portfolio quarterly",
                    "Increase SIP amount by 10% annually"
                ],
                "tax_optimization": [
                    "Utilize 80C limit fully with ELSS",
                    "Consider debt funds for tax efficiency",
                    "Long-term capital gains planning"
                ],
                "priority_score": {{
                    "high": ["Emergency fund", "Sector diversification"],
                    "medium": ["Tax optimization", "SIP increase"],
                    "low": ["Alternative investments", "Insurance review"]
                }}
            }}"""),
            ("human", """Generate personalized financial advice for:
            
PORTFOLIO ANALYSIS:
{portfolio_analysis}

RISK PROFILE:
- Risk Tolerance: {risk_tolerance}
- Investment Horizon: {investment_horizon}
- Risk Score: {risk_score}/10

MARKET CONDITIONS:
- Market Sentiment: {market_sentiment}
- Sector Outlook: {sector_outlook}

CURRENT PORTFOLIO:
- Total Value: ₹{total_value:,.0f}
- Asset Allocation: {asset_allocation}
- Top Holdings: {top_holdings}

Provide comprehensive, actionable financial advice.""")
        ])
    
    def process(self, state: FinancialState) -> FinancialState:
        """Generate comprehensive financial recommendations"""
        try:
            # Prepare data for recommendation generation
            portfolio_analysis = getattr(state.portfolio, 'analysis', {})
            top_holdings = self._get_top_holdings(state.portfolio.holdings)
            
            # Use LLM to generate recommendations
            result = self._invoke_llm(
                prompt="",  # Empty as we use template
                portfolio_analysis=json.dumps(portfolio_analysis, indent=2),
                risk_tolerance=state.risk_profile.risk_tolerance,
                investment_horizon=state.risk_profile.investment_horizon,
                risk_score=state.risk_profile.score,
                market_sentiment=state.market_data.market_sentiment,
                sector_outlook=json.dumps(state.market_data.sector_outlook, indent=2),
                total_value=state.portfolio.total_value,
                asset_allocation=state.portfolio.asset_allocation,
                top_holdings=top_holdings
            )
            
            # Parse recommendations
            try:
                advice = json.loads(result)
            except json.JSONDecodeError as json_err:
                logger.warning(f"Invalid JSON from LLM: {str(json_err)}, using fallback")
                advice = {
                    "asset_rebalancing": ["LLM returned invalid JSON - please configure API properly"],
                    "sector_adjustments": ["Review portfolio diversification"],
                    "investment_suggestions": ["Consider systematic investment plans"],
                    "risk_warnings": ["Monitor portfolio concentration"],
                    "action_items": ["Set up proper Google API key for detailed recommendations"]
                }
            
            # Update state with recommendations
            state.recommendations = Recommendations(
                asset_rebalancing=advice.get("asset_rebalancing", []),
                sector_adjustments=advice.get("sector_adjustments", []),
                investment_suggestions=advice.get("investment_suggestions", []),
                risk_warnings=advice.get("risk_warnings", []),
                action_items=advice.get("action_items", [])
            )
            
            # Store detailed advice
            state.recommendations.detailed_advice = advice
            
            # Generate final report
            state.final_report = self._generate_final_report(state, advice)
            state.analysis_complete = True
            
            logger.info("Financial recommendations generated successfully")
            
        except json.JSONDecodeError as e:
            error_msg = f"Failed to parse financial advice JSON: {str(e)}"
            logger.error(error_msg)
            state.errors.append(error_msg)
            
            # Provide fallback recommendations
            state.recommendations = self._get_fallback_recommendations()
        except Exception as e:
            error_msg = f"Financial advice generation failed: {str(e)}"
            logger.error(error_msg)
            state.errors.append(error_msg)
            
            # Provide fallback recommendations
            state.recommendations = self._get_fallback_recommendations()
        
        return self._update_state(state)
    
    def _get_top_holdings(self, holdings, top_n=5) -> str:
        """Get top N holdings by value"""
        if not holdings:
            return "No holdings available"
        
        sorted_holdings = sorted(holdings, key=lambda x: x.current_value, reverse=True)
        top_holdings = []
        
        for holding in sorted_holdings[:top_n]:
            top_holdings.append(
                f"{holding.name}: ₹{holding.current_value:,.0f} ({holding.asset_type})"
            )
        
        return "\n".join(top_holdings)
    
    def _generate_final_report(self, state: FinancialState, advice: dict) -> dict:
        """Generate comprehensive final report"""
        return {
            "portfolio_summary": {
                "total_value": state.portfolio.total_value,
                "asset_allocation": state.portfolio.asset_allocation,
                "sector_allocation": state.portfolio.sector_allocation,
                "holdings_count": len(state.portfolio.holdings)
            },
            "risk_assessment": {
                "risk_tolerance": state.risk_profile.risk_tolerance,
                "risk_score": state.risk_profile.score,
                "investment_horizon": state.risk_profile.investment_horizon
            },
            "market_context": {
                "sentiment": state.market_data.market_sentiment,
                "last_updated": state.market_data.last_updated
            },
            "recommendations": advice,
            "next_steps": advice.get("action_items", []),
            "priority_actions": advice.get("priority_score", {}).get("high", [])
        }
    
    def _get_fallback_recommendations(self) -> Recommendations:
        """Provide basic recommendations when LLM fails"""
        return Recommendations(
            asset_rebalancing=[
                "Consider rebalancing portfolio for better diversification",
                "Review asset allocation based on risk tolerance"
            ],
            sector_adjustments=[
                "Diversify across multiple sectors",
                "Avoid concentration in single sector"
            ],
            investment_suggestions=[
                "Consider systematic investment plans (SIPs)",
                "Explore debt instruments for stability"
            ],
            risk_warnings=[
                "Monitor portfolio concentration risks",
                "Keep emergency fund separate from investments"
            ],
            action_items=[
                "Review portfolio monthly",
                "Consult with financial advisor",
                "Stay updated with market conditions"
            ]
        )