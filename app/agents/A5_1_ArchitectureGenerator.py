"""
A5_1_ArchitectureGenerator.py
─────────────────────────────────────────────────────────────────────────────
Architecture Generator Agent  (Architecture-Only Build)

Takes outputs from A5 (Solution) agent, generates a focused 5-slide
Architecture Deliverable Deck, and renders an HTML/CSS architecture
diagram to PNG using wkhtmltoimage.

  Slide 1  → Title Slide
  Slide 2  → Problem & Objectives
  Slide 3  → Architecture Diagram (HTML/CSS → PNG)
  Slide 4  → Component & Tech Stack
  Slide 5  → Deployment & Security
"""

import os
import json
import logging
import tempfile
from typing import Dict, Any
from datetime import datetime

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.utils.llm_engine import invoke
from app.utils.config import load_config

config = load_config()
architecture_config = config.get("architecture_service", {})

MODEL = architecture_config.get("model", "gpt-4o")
PROMPT_BUILDER = architecture_config.get("prompt_presentation_builder", "A5_1_presentation_builder.txt")
PROMPT_DIAGRAM_BUILDER = architecture_config.get("prompt_diagram_builder", "A5_1_diagram_html_builder.txt")

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)


class A5_1ArchitectureGeneratorAgent:
    """
    Generates a focused 5-slide Architecture Deliverable Deck.
    """

    def __init__(self, model=MODEL):
        self.model = model

    def _load_prompt(self, filename: str) -> str:
        path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "prompts", filename
        )
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    def _call_llm_json(self, prompt: str, fallback: dict) -> dict:
        """Call LLM and parse the result as JSON. Returns fallback on failure."""
        try:
            response = invoke(prompt, model=self.model)
            # Strip markdown fences if present
            text = response.strip()
            if text.startswith("```"):
                lines = text.splitlines()
                if lines[0].strip().startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].strip().startswith("```"):
                    lines = lines[:-1]
                text = "\n".join(lines)
            # Try to find JSON object in the response
            start_idx = text.find("{")
            end_idx = text.rfind("}")
            if start_idx != -1 and end_idx != -1:
                text = text[start_idx:end_idx + 1]
            return json.loads(text)
        except json.JSONDecodeError as e:
            logger.warning(f"LLM JSON parsing failed: {e}. Using fallback.")
            return fallback
        except Exception as e:
            logger.warning(f"LLM call failed: {e}. Using fallback.")
            return fallback
            
    def _generate_openai_image(self, image_prompt: str, output_dir: str) -> str:
        """Generates architecture diagram PNG using OpenAI DALL-E image generation."""
        logger.info("=== Generating Architecture Diagram from OpenAI Image Generation ===")
        
        img_path = os.path.join(output_dir, "architecture_diagram.png")
        
        try:
            from openai import OpenAI
            import base64
            
            # Using standard API key from environment
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            
            logger.info("Calling OpenAI Image Generation API...")
            response = client.images.generate(
                model="gpt-image-2",  # Restored exact model string provided by user
                prompt=image_prompt,
                size="1024x768",
                quality="high"
                # Using standard generation; if their endpoint doesn't support response_format="b64_json",
                # it defaults to URL. BUT their example code expected base64:
                # "image_base64 = response.data[0].b64_json"
                # Let's see if we can use the URL fallback if b64 is missing.
            )
            
            # Their custom endpoint might return b64_json by default or URL by default
            if hasattr(response.data[0], 'b64_json') and response.data[0].b64_json:
                import base64
                img_data = base64.b64decode(response.data[0].b64_json)
            else:
                image_url = response.data[0].url
                import requests
                img_data = requests.get(image_url).content
                
            with open(img_path, "wb") as f:
                f.write(img_data)
                
            if os.path.exists(img_path) and os.path.getsize(img_path) > 500:
                logger.info(f"✓ Diagram generated via OpenAI and saved to {img_path}")
                return img_path
            else:
                logger.error("OpenAI produced empty or tiny image file")
                
        except Exception as e:
            logger.error(f"OpenAI Image Generation failed: {e}")
        
        return None

    def generate_ppt_structure(self, solution_architecture: str, output_dir: str = None) -> Dict[str, Any]:
        """
        Orchestrates all phases and returns the 5-slide architecture deck JSON.
        """
        logger.info("=" * 80)
        logger.info("A5.1 ARCHITECTURE GENERATOR AGENT — 5-Slide Deck Generation")
        logger.info("=" * 80)

        # Determine output directory for diagram
        if output_dir is None:
            output_dir = tempfile.mkdtemp()
        os.makedirs(output_dir, exist_ok=True)

        try:
            template = self._load_prompt(PROMPT_BUILDER)
            prompt = template.replace("{solution_architecture}", solution_architecture)
        except FileNotFoundError:
            logger.warning("Prompt file not found, using basic inline prompt.")
            prompt = f"Generate a 5-slide presentation JSON for this architecture: {solution_architecture}"

        try:
            diagram_template = self._load_prompt(PROMPT_DIAGRAM_BUILDER)
            diagram_prompt = diagram_template.replace("{solution_architecture}", solution_architecture)
        except FileNotFoundError:
            logger.warning("Diagram prompt file not found, using basic inline prompt.")
            diagram_prompt = f"Generate HTML diagram code in JSON format for this architecture: {solution_architecture}"

        # Fallback JSON structure
        fallback_json = {
            "presentation": {
                "title": "Architecture Proposal",
                "client": "Client",
                "date": datetime.now().strftime("%B %Y"),
                "slides": [
                    {
                        "slide_number": 1,
                        "title": "Title Slide",
                        "type": "title_slide",
                        "content": {
                            "project_title": "Architecture Proposal",
                            "client_name": "Client",
                            "subtitle": "Solution Architecture & Technical Proposal",
                            "date": datetime.now().strftime("%B %Y")
                        }
                    },
                    {
                        "slide_number": 2,
                        "title": "Problem & Objectives",
                        "type": "text_bullets",
                        "content": {
                            "bullets": [
                                "CURRENT CHALLENGES",
                                "- Identify core issues",
                                "- Define pain points",
                                "STRATEGIC OBJECTIVES",
                                "- Define objectives",
                                "- Propose solution",
                                "EXPECTED OUTCOMES",
                                "- Measurable improvements"
                            ]
                        }
                    },
                    {
                        "slide_number": 3,
                        "title": "Architecture Overview",
                        "type": "architecture_diagram",
                        "content": {
                            "caption": "High-level overview of the proposed solution architecture."
                        }
                    },
                    {
                        "slide_number": 4,
                        "title": "Component & Tech Stack",
                        "type": "table",
                        "content": {
                            "headers": ["Layer", "Key Components", "Technology Choices", "Purpose"],
                            "rows": [["Backend", "API Services", "Python, Node.js", "Core logic"]]
                        }
                    },
                    {
                        "slide_number": 5,
                        "title": "Deployment & Security",
                        "type": "component_detail",
                        "content": {
                            "description": "Infrastructure setup, environments, and security highlights",
                            "components": [{"name": "Security", "description": "OAuth2", "layer": "Security"}],
                            "benefits": ["Secure by design"]
                        }
                    }
                ]
            },
            "diagram_html": "<html><body><h1>Architecture Diagram</h1></body></html>"
        }

        # 1. Call LLM to get PPT structure
        logger.info("Calling LLM for PPT structure...")
        result_data = self._call_llm_json(prompt, fallback_json)
        presentation_data = result_data.get("presentation", fallback_json["presentation"])

        # 2. Call LLM to get Image Prompt
        logger.info("Calling LLM for Image Generation Prompt...")
        diagram_fallback = {"image_prompt": fallback_json["diagram_html"]}
        diagram_result = self._call_llm_json(diagram_prompt, diagram_fallback)
        image_prompt = diagram_result.get("image_prompt", "A detailed architecture diagram")
        
        # 2. Render Image → PNG
        diagram_path = self._generate_openai_image(image_prompt, output_dir)
        
        # 3. Inject image path into the presentation JSON (Slide 3)
        for slide in presentation_data.get("slides", []):
            if slide.get("type") == "architecture_diagram":
                slide["content"]["diagram_path"] = diagram_path
                
        logger.info(f"✓ Architecture deck assembled: {len(presentation_data.get('slides', []))} slides")
        return {"presentation": presentation_data}

# ── Example Usage ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))

    agent = A5_1ArchitectureGeneratorAgent()
    dummy_solution = "Microservices architecture on AWS. Python backend, React frontend."
    result = agent.generate_ppt_structure(
        solution_architecture=dummy_solution,
        output_dir="output"
    )
    with open("output/ppt_structure.json", "w") as f:
        json.dump(result, f, indent=2)
    print(f"✓ Generated slides")
