from langchain_core.prompts import ChatPromptTemplate
from .base_agent import BaseFinancialAgent
from .state import FinancialState, RiskProfile
import json
import logging

logger = logging.getLogger(__name__)


class RiskProfilerAgent(BaseFinancialAgent):
    """Agent responsible for assessing user risk tolerance and investment profile"""
    
    def __init__(self):
        # Use Flash model for risk assessment (structured analysis)
        super().__init__("risk_profiler", model="gemini-1.5-flash")
    
    def get_prompt_template(self) -> ChatPromptTemplate:
        return ChatPromptTemplate.from_messages([
            ("system", """You are a risk profiling expert for financial planning.
            Based on user responses and portfolio data, determine their risk profile.
            
            Risk Categories:
            - Conservative (1-3): Capital preservation, stable returns
            - Moderate (4-6): Balanced growth and stability  
            - Aggressive (7-10): High growth potential, volatility tolerance
            
            Return assessment in JSON format:
            {{
                "risk_tolerance": "moderate",
                "risk_score": 5.5,
                "investment_horizon": "medium",
                "profile_analysis": {{
                    "strengths": ["Diversified portfolio", "Long-term perspective"],
                    "concerns": ["High equity allocation for age", "Lack of emergency fund"],
                    "recommendations": ["Increase debt allocation", "Build emergency corpus"]
                }},
                "suitable_products": {{
                    "equity": 60,
                    "debt": 30,
                    "alternatives": 10
                }},
                "investment_style": "Balanced investor with moderate risk appetite"
            }}"""),
            ("human", """Assess risk profile based on:
            
User Responses:
{user_responses}

Current Portfolio:
- Total Value: ₹{total_value:,.0f}
- Asset Allocation: {asset_allocation}
- Sector Concentration: {sector_allocation}

Provide detailed risk assessment and recommendations.""")
        ])
    
    def process(self, state: FinancialState) -> FinancialState:
        """Assess user risk profile based on responses and portfolio"""
        try:
            # Use default responses if no user input provided
            user_responses = state.user_responses or self._get_default_responses()
            
            # Use LLM to assess risk profile
            result = self._invoke_llm(
                prompt="",  # Empty as we use template
                user_responses=json.dumps(user_responses, indent=2),
                total_value=state.portfolio.total_value,
                asset_allocation=state.portfolio.asset_allocation,
                sector_allocation=state.portfolio.sector_allocation
            )
            
            # Parse risk assessment
            try:
                assessment = json.loads(result)
            except json.JSONDecodeError as json_err:
                logger.warning(f"Invalid JSON from LLM: {str(json_err)}, using fallback")
                assessment = {
                    "risk_tolerance": "moderate",
                    "risk_score": 5.0,
                    "investment_horizon": "medium",
                    "profile_analysis": {"note": "LLM returned invalid JSON - using default profile"}
                }
            
            # Update state with risk profile
            state.risk_profile = RiskProfile(
                risk_tolerance=assessment.get("risk_tolerance", "moderate"),
                investment_horizon=assessment.get("investment_horizon", "medium"),
                score=assessment.get("risk_score", 5.0)
            )
            
            # Store detailed assessment
            state.risk_profile.assessment = assessment
            
            logger.info(f"Risk profiling completed. Risk tolerance: {state.risk_profile.risk_tolerance}, Score: {state.risk_profile.score}")
            
        except json.JSONDecodeError as e:
            error_msg = f"Failed to parse risk assessment JSON: {str(e)}"
            logger.error(error_msg)
            state.errors.append(error_msg)
            
            # Provide fallback risk profile
            state.risk_profile = RiskProfile(
                risk_tolerance="moderate",
                investment_horizon="medium",
                score=5.0
            )
        except Exception as e:
            error_msg = f"Risk profiling failed: {str(e)}"
            logger.error(error_msg)
            state.errors.append(error_msg)
            
            # Provide fallback risk profile
            state.risk_profile = RiskProfile(
                risk_tolerance="moderate", 
                investment_horizon="medium",
                score=5.0
            )
        
        return self._update_state(state)
    
    def _get_default_responses(self) -> dict:
        """Provide default responses for risk assessment when user input is not available"""
        return {
            "age_group": "30-45",
            "investment_experience": "3-5 years",
            "income_stability": "stable",
            "investment_goals": "wealth creation",
            "time_horizon": "5-10 years",
            "loss_tolerance": "can handle 10-20% temporary loss",
            "investment_knowledge": "moderate",
            "emergency_fund": "3-6 months expenses",
            "debt_situation": "manageable EMIs",
            "family_dependents": "spouse and children"
        }