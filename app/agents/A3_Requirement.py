import os
import json
import logging
import sys

# Add parent directory to path so we can import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.config import load_config
from utils.llm_engine import invoke

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)
config = load_config()
requirement_config = config.get(
    "requirement",
    {}
)

MODEL = requirement_config.get(
    "model",
    "gpt-4o"
)

PROMPT_FILE = requirement_config.get(
    "prompt_requirement_extraction",
    "A3_requirement_extraction.txt"
)

class A3RequirementAgent:

    def extract_requirements(
        self,
        report_text
    ):
        prompt_path = os.path.join(
            os.path.dirname(
                os.path.dirname(__file__)
            ),
            "prompts",
            PROMPT_FILE
        )

        with open(
            prompt_path,
            "r",
            encoding="utf-8"
        ) as f:
            template = f.read()
        prompt = template.replace(
            "{rfp_text}",
            report_text
        )
        logger.info(
            f"Calling Requirement Extraction LLM ({MODEL})..."
        )
        response = invoke(
            prompt,
            model=MODEL
        )

        return response.strip()
        
if __name__ == "__main__":

    sample_report = """
    Scope of Work:
    Assessment, Design, Implementation

    Deliverables:
    Documentation
    Training

    Timeline:
    August 2026 - December 2026
    """
    agent = A3RequirementAgent()

    result = agent.extract_requirements(
        sample_report
    )
    print(result)