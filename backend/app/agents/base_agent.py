from abc import ABC, abstractmethod
from typing import Dict, Any
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from .state import FinancialState
import os
import logging
import signal
from contextlib import contextmanager

logger = logging.getLogger(__name__)

@contextmanager
def timeout_handler(seconds):
    """Context manager to handle timeouts"""
    def timeout_signal_handler(signum, frame):
        raise TimeoutError(f"Operation timed out after {seconds} seconds")
    
    # Set the signal handler
    signal.signal(signal.SIGALRM, timeout_signal_handler)
    signal.alarm(seconds)
    
    try:
        yield
    finally:
        signal.alarm(0)  # Disable the alarm


class BaseFinancialAgent(ABC):
    """Base class for all financial agents"""
    
    def __init__(self, name: str, model: str = "gemini-1.5-flash"):
        self.name = name
        self.model = model
        self.llm = ChatGoogleGenerativeAI(
            model=model,  # gemini-1.5-flash (fast) or gemini-1.5-pro (powerful)
            temperature=0.1,  # Low temperature for consistent financial advice
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            convert_system_message_to_human=True,  # Gemini compatibility
            timeout=30,  # 30 second timeout
            max_retries=1  # Only retry once
        )
    
    @abstractmethod
    def get_prompt_template(self) -> ChatPromptTemplate:
        """Return the prompt template for this agent"""
        pass
    
    @abstractmethod
    def process(self, state: FinancialState) -> FinancialState:
        """Process the state and return updated state"""
        pass
    
    def _invoke_llm(self, prompt: str, **kwargs) -> str:
        """Helper method to invoke LLM with error handling"""
        try:
            logger.info(f"[{self.name}] Starting LLM call with model: {self.model}")
            
            # Check if API key is available
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                logger.warning(f"[{self.name}] No GOOGLE_API_KEY found in environment, using mock data")
                raise Exception("Google API key not configured")
            
            template = self.get_prompt_template()
            chain = template | self.llm
            
            logger.info(f"[{self.name}] Invoking LLM with 30s timeout...")
            
            # Use timeout wrapper
            try:
                with timeout_handler(30):
                    result = chain.invoke({"input": prompt, **kwargs})
                
                logger.info(f"[{self.name}] LLM call completed successfully")
                return result.content
            except TimeoutError as te:
                logger.error(f"[{self.name}] LLM call timed out: {str(te)}")
                raise Exception(f"LLM call timed out after 30 seconds")
            
        except Exception as e:
            logger.error(f"[{self.name}] LLM invocation failed: {str(e)}")
            logger.error(f"[{self.name}] Exception type: {type(e).__name__}")
            
            # Return mock data instead of failing
            logger.warning(f"[{self.name}] Falling back to mock data")
            return self._get_fallback_response()
    
    def _get_fallback_response(self) -> str:
        """Provide fallback response when LLM fails"""
        if self.name == "cas_parser":
            return '{"holdings": [], "total_value": 0, "parsing_errors": ["LLM unavailable - using mock data"]}'
        elif self.name == "portfolio_analyzer":
            return '{"diversification_score": 5.0, "concentration_risks": ["LLM unavailable"], "key_insights": ["Please configure Google API key"]}'
        elif self.name == "market_outlook":
            return '{"market_sentiment": "neutral", "sector_outlook": {}, "key_trends": ["LLM unavailable"]}'
        elif self.name == "risk_profiler":
            return '{"risk_tolerance": "moderate", "risk_score": 5.0, "investment_horizon": "medium"}'
        elif self.name == "financial_advisor":
            return '{"asset_rebalancing": ["Configure Google API key for recommendations"], "sector_adjustments": [], "investment_suggestions": [], "risk_warnings": [], "action_items": []}'
        else:
            return '{"status": "fallback", "message": "LLM unavailable"}'
    
    def _update_state(self, state: FinancialState) -> FinancialState:
        """Mark this agent as completed in state"""
        if self.name not in state.completed_agents:
            state.completed_agents.append(self.name)
        return state