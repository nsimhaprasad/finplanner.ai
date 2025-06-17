from langgraph.graph import StateGraph, END
from .state import FinancialState
from .cas_parser_agent import CASParserAgent
from .portfolio_analyzer_agent import PortfolioAnalyzerAgent
from .market_outlook_agent import MarketOutlookAgent
from .risk_profiler_agent import RiskProfilerAgent
from .financial_advisor_agent import FinancialAdvisorAgent
import logging

logger = logging.getLogger(__name__)


class FinancialOrchestrator:
    """Orchestrates the multi-agent financial planning workflow using LangGraph"""
    
    def __init__(self):
        self.agents = {
            "cas_parser": CASParserAgent(),
            "portfolio_analyzer": PortfolioAnalyzerAgent(),
            "market_outlook": MarketOutlookAgent(),
            "risk_profiler": RiskProfilerAgent(),
            "financial_advisor": FinancialAdvisorAgent()
        }
        self.workflow = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        """Build the agent workflow using LangGraph"""
        
        # Define the workflow graph
        workflow = StateGraph(FinancialState)
        
        # Add agent nodes
        workflow.add_node("cas_parser", self._run_cas_parser)
        workflow.add_node("portfolio_analyzer", self._run_portfolio_analyzer)
        workflow.add_node("market_outlook", self._run_market_outlook)
        workflow.add_node("risk_profiler", self._run_risk_profiler)
        workflow.add_node("financial_advisor", self._run_financial_advisor)
        
        # Define the workflow edges
        workflow.set_entry_point("cas_parser")
        
        # Sequential flow with conditional routing
        workflow.add_edge("cas_parser", "portfolio_analyzer")
        workflow.add_conditional_edges(
            "portfolio_analyzer",
            self._should_continue_analysis,
            {
                "continue": "market_outlook",
                "error": END
            }
        )
        workflow.add_edge("market_outlook", "risk_profiler")
        workflow.add_edge("risk_profiler", "financial_advisor")
        workflow.add_edge("financial_advisor", END)
        
        return workflow.compile()
    
    def _run_cas_parser(self, state: FinancialState) -> FinancialState:
        """Execute CAS parser agent"""
        logger.info("Running CAS Parser Agent")
        state.current_agent = "cas_parser"
        return self.agents["cas_parser"].process(state)
    
    def _run_portfolio_analyzer(self, state: FinancialState) -> FinancialState:
        """Execute portfolio analyzer agent"""
        logger.info("Running Portfolio Analyzer Agent")
        state.current_agent = "portfolio_analyzer"
        return self.agents["portfolio_analyzer"].process(state)
    
    def _run_market_outlook(self, state: FinancialState) -> FinancialState:
        """Execute market outlook agent"""
        logger.info("Running Market Outlook Agent")
        state.current_agent = "market_outlook"
        return self.agents["market_outlook"].process(state)
    
    def _run_risk_profiler(self, state: FinancialState) -> FinancialState:
        """Execute risk profiler agent"""
        logger.info("Running Risk Profiler Agent")
        state.current_agent = "risk_profiler"
        return self.agents["risk_profiler"].process(state)
    
    def _run_financial_advisor(self, state: FinancialState) -> FinancialState:
        """Execute financial advisor agent"""
        logger.info("Running Financial Advisor Agent")
        state.current_agent = "financial_advisor"
        return self.agents["financial_advisor"].process(state)
    
    def _should_continue_analysis(self, state: FinancialState) -> str:
        """Conditional logic to decide whether to continue analysis"""
        # Check if portfolio parsing was successful
        if not state.portfolio.holdings and not state.errors:
            logger.warning("No portfolio holdings found, but no errors reported")
            return "continue"
        
        if state.errors:
            logger.error(f"Errors detected: {state.errors}")
            return "error"
        
        return "continue"
    
    def process_financial_planning_sync(
        self, 
        pdf_content: str, 
        user_responses: dict = None
    ) -> FinancialState:
        """
        Process complete financial planning workflow synchronously
        
        Args:
            pdf_content: Extracted text from CAS PDF
            user_responses: User questionnaire responses (optional)
            
        Returns:
            FinancialState: Complete analysis results
        """
        try:
            # Initialize state
            initial_state = FinancialState(
                pdf_content=pdf_content,
                user_responses=user_responses or {}
            )
            
            logger.info("Starting financial planning workflow (synchronous)")
            
            # Execute agents sequentially instead of using LangGraph workflow
            current_state = initial_state
            
            # Run each agent in sequence
            try:
                current_state = self._run_cas_parser(current_state)
                logger.info("CAS Parser completed")
                
                if not current_state.errors:
                    current_state = self._run_portfolio_analyzer(current_state)
                    logger.info("Portfolio Analyzer completed")
                
                if not current_state.errors:
                    current_state = self._run_market_outlook(current_state)
                    logger.info("Market Outlook completed")
                
                if not current_state.errors:
                    current_state = self._run_risk_profiler(current_state)
                    logger.info("Risk Profiler completed")
                
                if not current_state.errors:
                    current_state = self._run_financial_advisor(current_state)
                    logger.info("Financial Advisor completed")
                
                current_state.analysis_complete = True
                logger.info("All agents completed successfully")
                
            except Exception as agent_error:
                logger.error(f"Agent execution failed: {str(agent_error)}")
                current_state.errors.append(f"Agent execution failed: {str(agent_error)}")
            
            return current_state
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {str(e)}")
            # Return state with error
            error_state = FinancialState(
                pdf_content=pdf_content,
                user_responses=user_responses or {},
                errors=[f"Workflow execution failed: {str(e)}"]
            )
            return error_state
    
    def get_workflow_status(self, state: FinancialState) -> dict:
        """Get current workflow status and progress"""
        total_agents = len(self.agents)
        completed_agents = len(state.completed_agents)
        
        return {
            "current_agent": state.current_agent,
            "completed_agents": state.completed_agents,
            "progress_percentage": (completed_agents / total_agents) * 100,
            "errors": state.errors,
            "analysis_complete": state.analysis_complete
        }