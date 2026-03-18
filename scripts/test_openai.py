from dotenv import load_dotenv
import os
from openai import OpenAI

# Load environment variables
load_dotenv()

# Get API key
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise ValueError("API key not found. Check your .env file.")

# Initialize client
client = OpenAI(api_key=api_key)

# Simple test call
response = client.chat.completions.create(
    model="gpt-4.1-mini",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Say hello in one sentence."}
    ]
)

# Print result
print(response.choices[0].message.content)