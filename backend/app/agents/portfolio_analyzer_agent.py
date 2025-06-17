from langchain_core.prompts import ChatPromptTemplate
from .base_agent import BaseFinancialAgent
from .state import FinancialState
import json
import logging

logger = logging.getLogger(__name__)


class PortfolioAnalyzerAgent(BaseFinancialAgent):
    """Agent responsible for analyzing portfolio composition and identifying issues"""
    
    def __init__(self):
        # Use Flash model for portfolio analysis (fast and efficient)
        super().__init__("portfolio_analyzer", model="gemini-1.5-flash")
    
    def get_prompt_template(self) -> ChatPromptTemplate:
        return ChatPromptTemplate.from_messages([
            ("system", """You are a portfolio analysis expert for Indian financial markets.
            Analyze the given portfolio for:
            
            1. Diversification analysis
            2. Concentration risks
            3. Asset allocation efficiency
            4. Sector exposure risks
            5. Overall portfolio health
            
            Provide specific, actionable insights in JSON format:
            {{
                "diversification_score": 7.5,
                "concentration_risks": [
                    "IT sector exposure is 45% - too high",
                    "Single stock RELIANCE is 25% of portfolio"
                ],
                "asset_allocation_analysis": {{
                    "current": {{"equity": 75, "debt": 20, "others": 5}},
                    "recommended": {{"equity": 60, "debt": 30, "others": 10}},
                    "deviation": "Overweight in equity, underweight in debt"
                }},
                "sector_analysis": {{
                    "overweight": ["IT", "Banking"],
                    "underweight": ["FMCG", "Healthcare"],
                    "missing": ["Real Estate", "Pharma"]
                }},
                "key_insights": [
                    "Portfolio lacks diversification in defensive sectors",
                    "High correlation risk in technology stocks"
                ]
            }}"""),
            ("human", """Analyze this portfolio:
            
Total Value: ₹{total_value:,.2f}
Asset Allocation: {asset_allocation}
Sector Allocation: {sector_allocation}
Number of Holdings: {num_holdings}

Holdings Details:
{holdings_details}""")
        ])
    
    def process(self, state: FinancialState) -> FinancialState:
        """Analyze portfolio composition and identify risks/opportunities"""
        try:
            if not state.portfolio.holdings:
                logger.warning("No portfolio holdings found, using default analysis")
                # Set default analysis instead of erroring
                state.portfolio.analysis = {
                    "diversification_score": 5.0,
                    "concentration_risks": ["No holdings data available"],
                    "key_insights": ["Upload a valid CAS file for detailed analysis"]
                }
                return self._update_state(state)
            
            # Prepare holdings details for analysis
            holdings_details = self._format_holdings_for_analysis(state.portfolio.holdings)
            
            # Use LLM to analyze portfolio
            result = self._invoke_llm(
                prompt="",  # Empty as we use template
                total_value=state.portfolio.total_value,
                asset_allocation=state.portfolio.asset_allocation,
                sector_allocation=state.portfolio.sector_allocation,
                num_holdings=len(state.portfolio.holdings),
                holdings_details=holdings_details
            )
            
            # Parse analysis results
            try:
                analysis = json.loads(result)
            except json.JSONDecodeError as json_err:
                logger.warning(f"Invalid JSON from LLM: {str(json_err)}, using fallback")
                analysis = {
                    "diversification_score": 5.0,
                    "concentration_risks": ["LLM returned invalid JSON"],
                    "key_insights": ["Please configure proper API settings for detailed analysis"]
                }
            
            # Store analysis in state (we'll create a proper analysis field later)
            state.portfolio.analysis = analysis
            
            logger.info(f"Portfolio analysis completed. Diversification score: {analysis.get('diversification_score', 'N/A')}")
            
        except json.JSONDecodeError as e:
            error_msg = f"Failed to parse portfolio analysis JSON: {str(e)}"
            logger.error(error_msg)
            state.errors.append(error_msg)
        except Exception as e:
            error_msg = f"Portfolio analysis failed: {str(e)}"
            logger.error(error_msg)
            state.errors.append(error_msg)
        
        return self._update_state(state)
    
    def _format_holdings_for_analysis(self, holdings) -> str:
        """Format holdings data for LLM analysis"""
        details = []
        for holding in holdings:
            details.append(
                f"- {holding.name} ({holding.symbol}): ₹{holding.current_value:,.0f} "
                f"({holding.asset_type}, {holding.sector or 'Unknown sector'})"
            )
        return "\n".join(details)