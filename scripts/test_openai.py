import json
import logging
from dotenv import load_dotenv
import os
from openai import OpenAI

# Load env
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise ValueError("API key not found in .env")

# Setup logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    filename="logs/api.log",
    level=logging.INFO,
    format="%(asctime)s - %(message)s"
)

# Initialize client
client = OpenAI(api_key=api_key)


# ---------------------------
# 1. BASIC CHAT TEST
# ---------------------------
def basic_chat():
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say hello in one short sentence."}
        ]
    )

    output = response.choices[0].message.content
    print("\nBasic Chat Response:\n", output)

    logging.info(f"Basic Chat Response: {output}")


# ---------------------------
# 2. FUNCTION CALL TEST
# ---------------------------
def get_project_status(project_name: str):
    return {
        "project": project_name,
        "status": "in progress",
        "owner": "Rodney"
    }


def function_call_test():
    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_project_status",
                "description": "Get status of a project",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "project_name": {"type": "string"}
                    },
                    "required": ["project_name"]
                }
            }
        }
    ]

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "user", "content": "What is the status of the tactics-game project?"}
        ],
        tools=tools,
        tool_choice="auto"
    )

    message = response.choices[0].message

    # If model calls the function
    if message.tool_calls:
        tool_call = message.tool_calls[0]
        args = json.loads(tool_call.function.arguments)

        result = get_project_status(**args)

        print("\nFunction Call Result:\n", result)
        logging.info(f"Function Call Result: {result}")

    else:
        print("\nNo function call triggered.")
        logging.info("No function call triggered.")


# ---------------------------
# MAIN
# ---------------------------
if __name__ == "__main__":
    try:
        basic_chat()
        function_call_test()
    except Exception as e:
        print("Error:", e)
        logging.error(f"Error: {e}")