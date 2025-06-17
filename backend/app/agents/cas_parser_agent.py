from langchain_core.prompts import ChatPromptTemplate
from .base_agent import BaseFinancialAgent
from .state import FinancialState, Holding, PortfolioData
import json
import logging

logger = logging.getLogger(__name__)


class CASParserAgent(BaseFinancialAgent):
    """Agent responsible for parsing CAS PDF content and extracting portfolio holdings"""
    
    def __init__(self):
        # Use Pro model for complex PDF parsing
        super().__init__("cas_parser", model="gemini-1.5-pro")
    
    def get_prompt_template(self) -> ChatPromptTemplate:
        return ChatPromptTemplate.from_messages([
            ("system", """You are a CAS (Consolidated Account Statement) parser for Indian financial markets. 
            Your job is to extract portfolio holdings from CAS PDF text content.
            
            Extract the following information:
            1. Equity holdings (stocks) with quantity, current value, and company names
            2. Mutual fund holdings with units, NAV, and current value
            3. Bond/debt holdings if any
            4. Calculate total portfolio value
            
            Return the data in this JSON format:
            {{
                "holdings": [
                    {{
                        "symbol": "RELIANCE",
                        "name": "Reliance Industries Ltd",
                        "quantity": 100,
                        "current_value": 250000,
                        "asset_type": "equity",
                        "sector": "Energy"
                    }}
                ],
                "total_value": 1000000,
                "parsing_errors": []
            }}
            
            If you cannot parse certain sections, add them to parsing_errors.
            Be precise with numbers and company names."""),
            ("human", "Parse this CAS content:\n\n{cas_content}")
        ])
    
    def process(self, state: FinancialState) -> FinancialState:
        """Parse CAS content and extract portfolio holdings"""
        try:
            if not state.pdf_content:
                state.errors.append("No PDF content provided for parsing")
                return self._update_state(state)
            
            # Use LLM to parse the CAS content
            result = self._invoke_llm(
                prompt="",  # Empty as we use template
                cas_content=state.pdf_content
            )
            
            # Parse LLM response
            parsed_data = json.loads(result)
            
            # Convert to Pydantic models
            holdings = [
                Holding(**holding) for holding in parsed_data.get("holdings", [])
            ]
            
            # Update state with parsed portfolio
            state.portfolio = PortfolioData(
                holdings=holdings,
                total_value=parsed_data.get("total_value", 0.0)
            )
            
            # Calculate asset allocation
            state.portfolio.asset_allocation = self._calculate_asset_allocation(holdings)
            state.portfolio.sector_allocation = self._calculate_sector_allocation(holdings)
            
            logger.info(f"Successfully parsed {len(holdings)} holdings worth ₹{state.portfolio.total_value:,.2f}")
            
        except json.JSONDecodeError as e:
            error_msg = f"Failed to parse LLM response as JSON: {str(e)}"
            logger.error(error_msg)
            state.errors.append(error_msg)
        except Exception as e:
            error_msg = f"CAS parsing failed: {str(e)}"
            logger.error(error_msg)
            state.errors.append(error_msg)
        
        return self._update_state(state)
    
    def _calculate_asset_allocation(self, holdings: list[Holding]) -> dict[str, float]:
        """Calculate percentage allocation by asset type"""
        if not holdings:
            return {}
        
        total_value = sum(h.current_value for h in holdings)
        if total_value == 0:
            return {}
        
        allocation = {}
        for holding in holdings:
            asset_type = holding.asset_type
            if asset_type not in allocation:
                allocation[asset_type] = 0
            allocation[asset_type] += holding.current_value
        
        # Convert to percentages
        return {k: (v / total_value) * 100 for k, v in allocation.items()}
    
    def _calculate_sector_allocation(self, holdings: list[Holding]) -> dict[str, float]:
        """Calculate percentage allocation by sector"""
        if not holdings:
            return {}
        
        equity_value = sum(h.current_value for h in holdings if h.asset_type == "equity")
        if equity_value == 0:
            return {}
        
        allocation = {}
        for holding in holdings:
            if holding.asset_type == "equity" and holding.sector:
                sector = holding.sector
                if sector not in allocation:
                    allocation[sector] = 0
                allocation[sector] += holding.current_value
        
        # Convert to percentages
        return {k: (v / equity_value) * 100 for k, v in allocation.items()}