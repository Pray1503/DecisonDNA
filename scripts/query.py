import argparse
import sys
from pathlib import Path

# Ensure app is in the import path
sys.path.append(str(Path(__file__).parent.parent))

from app.core.query_agent import QueryAgent


def main():
    parser = argparse.ArgumentParser(description="Ask DecisionDNA about architecture decisions.")
    parser.add_argument("query", help="The natural language question to ask")
    
    args = parser.parse_args()

    db_path = Path("data/decision_memory.db")
    if not db_path.exists():
        print("ERROR: Decision memory database does not exist. Run reconstruct_decisions.py first.")
        sys.exit(1)

    agent = QueryAgent(db_path=db_path)
    response = agent.query(args.query)

    print("\n" + response + "\n")


if __name__ == "__main__":
    main()
