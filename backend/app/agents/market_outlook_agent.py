from langchain_core.prompts import ChatPromptTemplate
from .base_agent import BaseFinancialAgent
from .state import FinancialState, MarketData
import yfinance as yf
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class MarketOutlookAgent(BaseFinancialAgent):
    """Agent responsible for fetching and analyzing current market conditions"""
    
    def __init__(self):
        # Use Flash model for market analysis (real-time data processing)
        super().__init__("market_outlook", model="gemini-1.5-flash")
    
    def get_prompt_template(self) -> ChatPromptTemplate:
        return ChatPromptTemplate.from_messages([
            ("system", """You are a market analysis expert for Indian financial markets.
            Analyze the provided market data and provide outlook in JSON format:
            
            {{
                "market_sentiment": "bullish/bearish/neutral",
                "sector_outlook": {{
                    "IT": "positive - strong earnings growth expected",
                    "Banking": "neutral - NPA concerns persist",
                    "FMCG": "positive - rural recovery visible"
                }},
                "key_trends": [
                    "FII flows turning positive",
                    "Interest rates peaking",
                    "Rupee strengthening"
                ],
                "investment_themes": [
                    "Focus on quality mid-caps",
                    "Defensive sectors preferred",
                    "Export-oriented companies benefiting"
                ],
                "risk_factors": [
                    "Global recession fears",
                    "Geopolitical tensions",
                    "Inflation concerns"
                ]
            }}"""),
            ("human", """Analyze current market conditions:
            
Market Indices:
{market_indices}

Sector Performance:
{sector_performance}

Recent Trends:
{recent_trends}

Provide market outlook and investment themes.""")
        ])
    
    def process(self, state: FinancialState) -> FinancialState:
        """Fetch market data and analyze current conditions"""
        try:
            # Fetch current market data
            market_data = self._fetch_market_data()
            
            # Use LLM to analyze market conditions
            result = self._invoke_llm(
                prompt="",  # Empty as we use template
                market_indices=market_data["indices"],
                sector_performance=market_data["sectors"],
                recent_trends=market_data["trends"]
            )
            
            # Parse market analysis
            try:
                analysis = json.loads(result)
            except json.JSONDecodeError as json_err:
                logger.warning(f"Invalid JSON from LLM: {str(json_err)}, using fallback")
                analysis = {
                    "market_sentiment": "neutral",
                    "sector_outlook": {"IT": "Mixed performance", "Banking": "Stable"},
                    "key_trends": ["LLM returned invalid JSON - using fallback data"]
                }
            
            # Update state with market data
            state.market_data = MarketData(
                market_sentiment=analysis.get("market_sentiment", "neutral"),
                sector_outlook=analysis.get("sector_outlook", {}),
                market_indices=market_data["indices"],
                last_updated=datetime.now().isoformat()
            )
            
            # Store additional analysis data
            state.market_data.analysis = analysis
            
            logger.info(f"Market analysis completed. Sentiment: {state.market_data.market_sentiment}")
            
        except Exception as e:
            error_msg = f"Market analysis failed: {str(e)}"
            logger.error(error_msg)
            state.errors.append(error_msg)
            
            # Provide fallback market data
            state.market_data = MarketData(
                market_sentiment="neutral",
                sector_outlook={},
                market_indices={},
                last_updated=datetime.now().isoformat()
            )
        
        return self._update_state(state)
    
    def _fetch_market_data(self) -> dict:
        """Fetch current market data from various sources"""
        try:
            # Fetch major Indian indices
            indices = {}
            indian_indices = [
                ("^NSEI", "NIFTY 50"),
                ("^BSESN", "SENSEX"),
                ("^NSEBANK", "BANK NIFTY"),
                ("^NSEIT", "NIFTY IT")
            ]
            
            for symbol, name in indian_indices:
                try:
                    ticker = yf.Ticker(symbol)
                    hist = ticker.history(period="5d")
                    if not hist.empty:
                        current_price = hist['Close'].iloc[-1]
                        prev_price = hist['Close'].iloc[-2] if len(hist) > 1 else current_price
                        change_pct = ((current_price - prev_price) / prev_price) * 100
                        indices[name] = {
                            "price": round(current_price, 2),
                            "change_pct": round(change_pct, 2)
                        }
                except Exception as e:
                    logger.warning(f"Failed to fetch {name}: {str(e)}")
                    continue
            
            # Sector performance (simplified)
            sectors = {
                "IT": "Mixed performance with earnings pressure",
                "Banking": "Stable growth with credit expansion",
                "FMCG": "Rural recovery driving growth",
                "Auto": "EV transition creating opportunities",
                "Pharma": "Export demand remains strong"
            }
            
            # Recent trends (this would typically come from news APIs)
            trends = [
                "FII flows turned positive in recent sessions",
                "RBI maintains accommodative stance",
                "Q3 earnings showing recovery signs",
                "Geopolitical tensions affecting energy sector"
            ]
            
            return {
                "indices": indices,
                "sectors": sectors,
                "trends": trends
            }
            
        except Exception as e:
            logger.error(f"Failed to fetch market data: {str(e)}")
            return {
                "indices": {},
                "sectors": {},
                "trends": ["Market data temporarily unavailable"]
            }