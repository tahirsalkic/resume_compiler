import logging
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from openai import OpenAI
from dotenv import load_dotenv
from ai.ai_helper_functions import load_prompts

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
        logger.error("Error creating chat completion:", exc_info=True)
        raise

def analyze_description(description: str, prompt: str) -> str:
    """Analyze a job description using a given prompt."""
    return create_chat_completion(prompt, description, temperature=0.4)

def pick_a_hat(role: str) -> str:
    """Choose the closest profile using a given prompt."""
    return create_chat_completion('pick_a_hat', role, temperature=0.4)

def skills_analysis(job_descriptions: dict) -> list:
    """Analyze job descriptions using a given prompt in parallel."""
    job_skills = {}
    with ThreadPoolExecutor() as executor:
        future_to_key = {executor.submit(analyze_description, desc, "skills_analysis"): key for key, desc in job_descriptions.items()}
        for future in as_completed(future_to_key):
            try:
                result = future.result()
                key = future_to_key[future]
                job_skills[key] = result
            except Exception as e:
                logger.error("Job analysis failed.", exc_info=True)

        return job_skills