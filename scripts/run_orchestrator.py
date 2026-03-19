from studio_agents.orchestrator import ProgramOrchestrator


def main() -> None:
    orchestrator = ProgramOrchestrator()
    user_input = input("Enter your request: ").strip()

    if not user_input:
        print("No input provided.")
        return

    result = orchestrator.plan(user_input)
    print("\n--- Orchestrator Result ---\n")
    print(result)


if __name__ == "__main__":
    main()