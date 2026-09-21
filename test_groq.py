from groq import Groq
from dotenv import load_dotenv
import os

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise ValueError("GROQ_API_KEY not found in .env")

client = Groq(api_key=api_key)

MODEL_NAME = "qwen/qwen3.8-27b"

response = client.chat.completions.create(
    model=MODEL_NAME,
    messages=[
        {
            "role": "user",
            "content": "Explain UPI fraud detection in one sentence."
        }
    ],
    temperature=0
)

print(response.choices[0].message.content)