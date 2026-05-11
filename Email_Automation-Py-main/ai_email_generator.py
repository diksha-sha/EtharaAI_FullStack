import os
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# OpenRouter API Key from environment variable
API_KEY = os.getenv("OPENROUTER_API_KEY")
if not API_KEY:
    print(
        "WARNING: OPENROUTER_API_KEY is not set. Create a .env file and add OPENROUTER_API_KEY=<your_key> or set the environment variable."
    )


def generate_email(data, prompt_template=None):
    if not API_KEY:
        raise RuntimeError(
            "OPENROUTER_API_KEY is not configured. Please add it to .env or the environment."
        )

    """
    Generate an email using the OpenRouter AI API.

    Args:
        data: Dictionary containing recipient details (name, email, company, requirement)
        prompt_template: Optional custom prompt template. If not provided, uses default.

    Returns:
        Generated email body string
    """

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    name = str(data.get("name", "") or "").strip()
    if not name or name.lower() in ["nan", "none"]:
        name = "Sir/Madam"
    greeting = f"Dear {name}"

    email_addr = data.get("email", "")
    company = data.get("company", "")
    requirement_data = data.get("requirement", "")

    if prompt_template is None:
        prompt_template = """You are writing the BODY of a professional B2B recruitment email.

IMPORTANT RULES:
- Do NOT write the greeting.
- Do NOT write "Dear".
- Do NOT include "Best Regards" or signature.
- Do NOT include subject.
- Do NOT include headings, markdown, or bullet points.
- Do NOT add explanations.

Write only the email body in natural paragraph format.

Context:
The sender is Hansraj Ventures Private Limited, a recruitment and staffing company that provides skilled professionals.

The email should:
- Briefly acknowledge the hiring requirement
- Mention Hansraj Ventures staffing capability
- Mention hiring models (Contract / Contract-to-hire / Full-time)
- Mention candidate screening process
- Request a short meeting
- Mention company profile attachment

Company: {company}

Hiring Requirement:
{requirement}
"""

    prompt_text = prompt_template.format(
        name=name,
        email=email_addr,
        company=company,
        requirement=requirement_data,
    )

    payload = {
        "model": "meta-llama/llama-3.1-8b-instruct",
        "messages": [
            {
                "role": "system",
                "content": "You are a professional business email writer who writes B2B recruitment proposal emails."
            },
            {
                "role": "user",
                "content": prompt_text
            }
        ],
        "max_tokens": 600
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()

        result = response.json()
        choices = result.get("choices")
        if not choices or not isinstance(choices, list) or not choices[0].get("message"):
            raise RuntimeError("OpenRouter returned an unexpected response structure.")

        email_text = choices[0]["message"]["content"].strip()
        return f"{greeting}\n\n{email_text}"

    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"OpenRouter request failed: {str(e)}")
    except ValueError as e:
        raise RuntimeError(f"OpenRouter returned invalid JSON: {str(e)}")