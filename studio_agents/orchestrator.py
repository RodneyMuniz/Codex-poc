import asyncio
from dotenv import load_dotenv
from agents import Agent, Runner

load_dotenv()

orchestrator = Agent(
    name="Program Orchestrator",
    instructions="""
You are a Program Orchestrator for a multi-agent system.

Your role:
- Understand the user's objective
- Break it into clear steps
- Decide what should be done next
- Keep responses structured and actionable

Rules:
- Be concise
- Think step-by-step
- Do NOT execute everything at once
- Always suggest the next action
"""
)

async def main():
    user_input = input("Enter your request: ")
    result = await Runner.run(orchestrator, user_input)

    print("\n--- Orchestrator Output ---\n")
    print(result.final_output)

if __name__ == "__main__":
    asyncio.run(main())