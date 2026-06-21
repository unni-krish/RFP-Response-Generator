"""
llm_engine.py
─────────────────────────────────────────────────────────────────────────────
Simple & Smart LLM Engine with Global Configuration
"""

import os
import logging
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)


# ========================== GLOBAL CONFIGURATION ==========================

# Default Models
DEFAULT_GPT_MODEL = "gpt-4o"
DEFAULT_CLAUDE_MODEL = "claude-sonnet-4"

# You can change these anytime:
# DEFAULT_GPT_MODEL = "gpt-4o-mini"
# DEFAULT_CLAUDE_MODEL = "claude-3-5-sonnet-20240620"

# Overall Default (used when no model is passed)
DEFAULT_MODEL = DEFAULT_GPT_MODEL

# =========================================================================


def get_provider_and_model(model_name: str):
    """Simple logic: Detect provider based on keywords in model name."""
    if not model_name:
        raise ValueError("Model name cannot be empty")
    
    model_lower = model_name.lower().strip()
    
    # Claude → Anthropic
    if "claude" in model_lower:
        return "anthropic", model_name
    
    # GPT or O-series → OpenAI
    elif "gpt" in model_lower or "o1" in model_lower or "o3" in model_lower:
        return "openai", model_name
    
    # Additional smart fallbacks
    elif any(x in model_lower for x in ["sonnet", "opus", "haiku"]):
        return "anthropic", model_name
    elif any(x in model_lower for x in ["turbo", "preview", "mini", "4o"]):
        return "openai", model_name
    
    else:
        raise ValueError(
            f"Unknown model: '{model_name}'\n"
            f"Tip: Use models containing 'claude', 'gpt', or 'o1/o3'"
        )


def get_model_instance(model_name: str):
    """Return correct model instance and provider name."""
    provider, actual_model = get_provider_and_model(model_name)
    
    if provider == "openai":
        return ChatOpenAI(
            model=actual_model,
            api_key=os.getenv("OPENAI_API_KEY"),
        ), "GPT"
    else:
        return ChatAnthropic(
            model=actual_model,
            api_key=os.getenv("ANTHROPIC_API_KEY"),
        ), "Claude"


def invoke(prompt: str | list, model: str = None) -> str:
    """
    Call LLM with given model name and automatic fallback.
    
    Args:
        prompt: The prompt to send (string for text, list of dicts for multimodal)
        model: Model name (optional). If None, uses DEFAULT_MODEL
    """
    # Use default model if none provided
    if model is None or model.strip() == "":
        model = DEFAULT_MODEL

    try:
        primary_model, primary_name = get_model_instance(model)
    except ValueError as e:
        logger.error(e)
        raise

    # Set fallback model
    if primary_name == "GPT":
        fallback_model_name = DEFAULT_CLAUDE_MODEL
        fallback_name = "Claude"
    else:
        fallback_model_name = DEFAULT_GPT_MODEL
        fallback_name = "GPT"

    fallback_model, _ = get_model_instance(fallback_model_name)

    messages = [HumanMessage(content=prompt)]

    # Try Primary
    try:
        logger.info(f"Calling {primary_name} → {model}")
        response = primary_model.invoke(messages)
        return response.content
    except Exception as e:
        logger.warning(f"{primary_name} failed: {e}. Falling back to {fallback_name}...")

    # Try Fallback
    try:
        response = fallback_model.invoke(messages)
        return response.content
    except Exception as e:
        logger.error(f"Both providers failed: {e}")
        raise


# ====================== Example Usage ======================
if __name__ == "__main__":
    # Using default model
    print("=== Default Model ===")
    print(invoke("Hello, tell me a joke!"))
    
    # Using specific models
    print("\n=== GPT Model ===")
    print(invoke("Explain AI in one sentence", model="gpt-4o-mini"))
    
    print("\n=== Claude Model ===")
    print(invoke("Explain AI in one sentence", model="claude-sonnet-4"))
    
    print("\n=== Full Claude Name ===")
    print(invoke("What is the capital of France?", model="claude-3-5-sonnet-20240620"))