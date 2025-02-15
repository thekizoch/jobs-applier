# llm_integration.py

import openai
# If you plan to support more providers, import them conditionally.
from .logs import get_logger

logger = get_logger(__name__)

def generate_cover_letter(job_title: str, company_name: str, job_description: str, user_background: str) -> str:
    """
    Leverage an LLM (e.g., OpenAI GPT) to generate a short cover letter.
    """
    # For demo, we’ll assume OpenAI. In a real scenario, check config for other providers.
    try:
        prompt = (
            f"You are a professional resume writer. "
            f"Please write a concise, tailored cover letter for the position: '{job_title}' at '{company_name}'. "
            f"Job Description: {job_description}. "
            f"My background: {user_background}. "
            f"Output a professional cover letter with a friendly tone."
        )

        response = openai.Completion.create(
            model="text-davinci-003",
            prompt=prompt,
            max_tokens=250,
            temperature=0.7
        )

        cover_letter = response.choices[0].text.strip()
        return cover_letter
    except Exception as e:
        logger.error(f"Error generating cover letter: {e}")
        return (
            "Dear Hiring Manager,\n\n"
            "I am excited to apply for this position. "
            "Thank you for your consideration.\n\nBest Regards,\n[Your Name]"
        )
