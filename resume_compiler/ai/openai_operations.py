import logging
import os
from openai import OpenAI
from dotenv import load_dotenv
from multiprocessing import Pool
from functools import partial
from ai.ai_helper_functions import load_prompts
from ai.openai_operations import analyze_description
from config.settings import load_config

logger = logging.getLogger(__name__)

load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")

prompts = load_prompts()

if not openai_api_key:
    raise ValueError("OpenAI API key is not set in the environment variables")

def create_chat_completion(system_prompt: str, user_prompt: str, model='gpt-4o-mini', temperature=0.5) -> str:
    """Create a chat completion using OpenAI."""
    client = OpenAI(api_key=openai_api_key)
    messages = [
        {"role": "system", "content": prompts[system_prompt]},
        {"role": "user", "content": user_prompt}
    ]

    try:
        response = client.chat.completions.create(model=model, messages=messages, temperature=temperature)
        return response.choices[0].message.content
    except Exception as e:
        logger.error("Error creating chat completion:", e)
        raise

def analyze_description(description: str, prompt: str) -> str:
    """Analyze a job description using a given prompt."""
    return create_chat_completion(prompt, description, temperature=0.4)

def skills_analysis(job_descriptions: dict) -> str:
    """Analyze a job descriptions using a given prompt in parallel."""
    analyze_with_prompt = partial(analyze_description, prompt="skills_analysis")
    with Pool() as pool:
        results = pool.map(analyze_with_prompt, job_descriptions.values())
    
    return results