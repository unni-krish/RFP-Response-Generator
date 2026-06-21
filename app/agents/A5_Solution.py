"""
A5_Solution.py
─────────────────────────────────────────────────────────────────────────────
Solution Architecture Agent
Generates a comprehensive solution recommendation based on extracted 
requirements, compliance validation, and the organization's capabilities.
"""

import os
import json
import yaml
import logging
import requests

import sys
# Add parent directory to path so we can import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.llm_engine import invoke
from utils.config import load_config

config = load_config()
solution_config = config.get("solution", {})

MODEL = solution_config.get("model", "gpt-4o")
PROMPT_FILE = solution_config.get("prompt_architecture", "A5_solution.txt")

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

class A5SolutionAgent:
    def __init__(self, model=MODEL):
        self.model = model
        
    def _load_tech_stack(self) -> str:
        """Fetches the tech_stack value from the API and returns it as a string for the prompt."""
        BASE_URL = "https://resource-service-jzdf.onrender.com"
        try:
            response = requests.get(f"{BASE_URL}/tables/tech_stack")
            response.raise_for_status()
            return response.text
        except Exception as e:
            logger.error(f"Failed to fetch tech stack from API: {e}")
            return "Technology stack information not available."

    def generate_solution(self, requirements: str, compliance_report: str) -> str:
        """Generates the solution architecture markdown report."""
        if not requirements or not requirements.strip():
            return "Error: No extracted requirements provided to generate a solution."

        logger.info("=== Phase 1: Loading Technology Stack ===")
        tech_stack = self._load_tech_stack()

        logger.info("=== Phase 2: Generating Solution Architecture Report ===")
        prompt_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 
            "prompts", 
            PROMPT_FILE
        )
        
        try:
            with open(prompt_path, "r", encoding="utf-8") as f:
                prompt_template = f.read()
        except FileNotFoundError:
            logger.error(f"Prompt file not found at {prompt_path}")
            return "Error: Prompt file missing."
            
        # Replace variables in the prompt
        prompt = prompt_template.replace("{requirements}", requirements)
        prompt = prompt.replace("{compliance_report}", compliance_report or "No compliance data available.")
        prompt = prompt.replace("{tech_stack}", tech_stack)
        
        logger.info(f"Calling LLM ({self.model}) for solution architecture generation...")
        report = invoke(prompt, model=self.model)
        
        return report

# ====================== Example Usage ======================
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))
    
    agent = A5SolutionAgent()
    
    dummy_requirements = """
    The proposed healthcare portal must allow patients to view their medical records, 
    book appointments, and pay bills online via credit card. 
    The system will be hosted on AWS. It needs to be accessible globally 
    but specifically targets users in the European Union and California.
    """
    
    dummy_compliance = """
    Compliance Validation:
    - HIPAA compliance is required for medical records.
    - GDPR compliance for EU users.
    - CCPA compliance for California users.
    - PCI-DSS for credit card payments.
    """
    
    print("Testing A5 Solution Architecture Agent...")
    print("-" * 50)
    report = agent.generate_solution(dummy_requirements, dummy_compliance)
    
    print("\n\n" + "="*50)
    print("SOLUTION ARCHITECTURE REPORT:")
    print("="*50)
    print(report)
