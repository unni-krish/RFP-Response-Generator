"""
A4_Compliance.py
─────────────────────────────────────────────────────────────────────────────
Compliance Validation Agent
Takes extracted requirements and validates them against regulatory frameworks,
industry standards, and legal obligations using LLM reasoning and Web Search.
"""

import os
import json
import logging
from typing import List

import sys
# Add parent directory to path so we can import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.llm_engine import invoke
from utils.config import load_config

# Attempt to load TavilyClient
try:
    from tavily import TavilyClient
    HAS_TAVILY = True
except ImportError:
    HAS_TAVILY = False

config = load_config()
compliance_config = config.get("compliance", {})

DEFAULT_MODEL = compliance_config.get("model", "gpt-4o")
SEARCH_MODEL = compliance_config.get("search_query_model", "gpt-4o-mini")
PROMPT_VALIDATION = compliance_config.get("prompt_validation", "A4_compliance_validation.txt")

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

class A4ComplianceAgent:
    def __init__(self, model=DEFAULT_MODEL, search_model=SEARCH_MODEL):
        self.model = model
        self.search_model = search_model
        
        self.tavily_client = None
        if HAS_TAVILY and os.getenv("TAVILY_API_KEY"):
            self.tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
        elif os.getenv("TAVILY_API_KEY"):
            logger.warning("TAVILY_API_KEY is present but 'tavily-python' is not installed. Using raw requests fallback if possible, or search will be disabled.")
            
    def _formulate_search_queries(self, requirements: str) -> List[str]:
        """Uses a faster LLM to determine what to search for based on requirements."""
        logger.info("Formulating search queries based on requirements...")
        
        prompt = f"""
        Based on the following extracted requirements from a project, generate exactly 2 specific search queries to find recent regulatory changes, compliance frameworks, or security standards that would apply to this project.
        Return ONLY the queries, one per line. No bullet points, no extra text.
        
        Requirements:
        {requirements}  # Trim to avoid huge prompts for query generation
        """
        
        try:
            response = invoke(prompt, model=self.search_model)
            queries = [q.strip("- *1234567890.") for q in response.strip().split("\n") if q.strip()]
            return queries[:2]  # limit to 2 just in case
        except Exception as e:
            logger.error(f"Failed to formulate search queries: {e}")
            return ["general data protection regulations 2026", "software compliance standards latest"]

    def _execute_searches(self, queries: List[str]) -> str:
        """Executes Tavily searches and compiles context."""
        if not self.tavily_client and not os.getenv("TAVILY_API_KEY"):
            logger.warning("Tavily search is disabled (Missing API Key or tavily-python package).")
            return "No web search context available. Rely on internal knowledge."

        context_blocks = []
        for query in queries:
            logger.info(f"Searching Tavily for: '{query}'")
            try:
                # Fallback to direct requests if tavily package is missing but key is there
                if self.tavily_client:
                    result = self.tavily_client.search(query=query, search_depth="basic", max_results=3)
                    results_list = result.get("results", [])
                else:
                    import requests
                    resp = requests.post(
                        "https://api.tavily.com/search",
                        json={"api_key": os.getenv("TAVILY_API_KEY"), "query": query, "search_depth": "basic", "max_results": 3}
                    )
                    results_list = resp.json().get("results", [])
                
                context_blocks.append(f"### Search Results for '{query}':")
                for r in results_list:
                    context_blocks.append(f"- {r.get('title', 'No Title')}: {r.get('content', '')}")
            except Exception as e:
                logger.error(f"Search failed for query '{query}': {e}")
        
        if not context_blocks:
            return "No web search context available."
            
        return "\n".join(context_blocks)

    def validate_requirements(self, extracted_requirements: str) -> str:
        """Main method: validates requirements and returns the Markdown report."""
        if not extracted_requirements or not extracted_requirements.strip():
            return "Error: No extracted requirements provided to validate."

        logger.info("=== Phase 1: Formulate and Execute Compliance Searches ===")
        queries = self._formulate_search_queries(extracted_requirements)
        search_context = self._execute_searches(queries)

        logger.info("=== Phase 2: Generating Compliance Validation Report ===")
        prompt_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "prompts", PROMPT_VALIDATION)
        
        try:
            with open(prompt_path, "r", encoding="utf-8") as f:
                validation_prompt_template = f.read()
        except FileNotFoundError:
            logger.error(f"Prompt file not found at {prompt_path}")
            return "Error: Prompt file missing."
            
        prompt = validation_prompt_template.replace("{extracted_requirements}", extracted_requirements)
        prompt = prompt.replace("{search_context}", search_context)
        
        logger.info(f"Calling LLM ({self.model}) for compliance validation...")
        report = invoke(prompt, model=self.model)
        
        return report

# ====================== Example Usage ======================
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))
    
    agent = A4ComplianceAgent()
    
    dummy_requirements = """
    The proposed healthcare portal must allow patients to view their medical records, 
    book appointments, and pay bills online via credit card. 
    The system will be hosted on AWS. It needs to be accessible globally 
    but specifically targets users in the European Union and California.
    """
    
    print("Testing A4 Compliance Validation Agent...")
    print("-" * 50)
    report = agent.validate_requirements(dummy_requirements)
    
    print("\n\n" + "="*50)
    print("COMPLIANCE VALIDATION REPORT:")
    print("="*50)
    print(report)
