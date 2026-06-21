import os
import yaml
from dotenv import load_dotenv

def load_config(config_name="params.yml"):
    # Load environment variables from .env if present
    load_dotenv()
    
    # Calculate the project root assuming this file is in app/utils/
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    config_path = os.path.join(base_dir, "config", config_name)
    
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found at: {config_path}")
        
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
        
    return config or {}
