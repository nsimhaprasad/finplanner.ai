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
        # Debug API key
        api_key = os.getenv("GOOGLE_API_KEY")
        logger.info(f"[{self.name}] API key present: {bool(api_key)}")
        logger.info(f"[{self.name}] API key length: {len(api_key) if api_key else 0}")
        
        self.llm = ChatGoogleGenerativeAI(
            model=model,  # gemini-1.5-flash (fast) or gemini-1.5-pro (powerful)
            temperature=0.1,  # Low temperature for consistent financial advice
            google_api_key=api_key,
            convert_system_message_to_human=True,  # Gemini compatibility
            # Remove timeout and max_retries to use defaults
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
                logger.info(f"[{self.name}] Raw LLM response: {repr(result.content)}")
                logger.info(f"[{self.name}] Response length: {len(result.content) if result.content else 0}")
                
                if not result.content or not result.content.strip():
                    logger.error(f"[{self.name}] LLM returned empty response")
                    raise Exception("LLM returned empty response")
                
                # Clean the response (remove markdown formatting)
                cleaned_response = self._clean_llm_response(result.content)
                logger.info(f"[{self.name}] Cleaned response: {repr(cleaned_response)}")
                
                return cleaned_response
            except TimeoutError as te:
                logger.error(f"[{self.name}] LLM call timed out: {str(te)}")
                raise Exception(f"LLM call timed out after 30 seconds")
            
        except Exception as e:
            logger.error(f"[{self.name}] LLM invocation failed: {str(e)}")
            logger.error(f"[{self.name}] Exception type: {type(e).__name__}")
            
            # Don't fall back - let the error propagate to force fixing the real issue
            raise Exception(f"LLM call failed in {self.name}: {str(e)}")
    
    def _clean_llm_response(self, response: str) -> str:
        """Clean LLM response by removing markdown formatting"""
        import re
        
        # Remove markdown code blocks (```json ... ``` or ``` ... ```)
        response = re.sub(r'^```(?:json)?\s*\n', '', response, flags=re.MULTILINE)
        response = re.sub(r'\n```\s*$', '', response, flags=re.MULTILINE)
        
        # Remove any leading/trailing whitespace
        response = response.strip()
        
        return response
    
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