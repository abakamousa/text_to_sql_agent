import os
from dotenv import load_dotenv
import logging

def load_env(env_filename: str = ".env") -> str:
    """
    Loads environment variables from the specified .env file, ensuring it's found
    even when executed from a subdirectory (like Azure Functions worker).

    Args:
        env_filename: The name of the .env file to load (default: '.env')

    Returns:
        The absolute path to the loaded .env file
    """
    # Detect project root (2 levels up from utils/)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, "..", ".."))

    # Compute full path to .env file
    env_path = os.path.join(project_root, env_filename)

    # If not found, check current working directory as fallback
    if not os.path.exists(env_path):
        alt_path = os.path.join(os.getcwd(), env_filename)
        if os.path.exists(alt_path):
            env_path = alt_path

    # Load environment variables
    load_dotenv(env_path, override=True)

    # Log debug info
    if os.path.exists(env_path):
        logging.info(f"✅ Environment loaded from: {env_path}")
    else:
        logging.warning(f"⚠️ Environment file not found: {env_path}")

    return env_path
