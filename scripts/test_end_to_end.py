import os
import sqlite3
import sys
from pathlib import Path

# Ensure app is in the import path
sys.path.append(str(Path(__file__).parent.parent))

from app.core.query_agent import QueryAgent


def check_sqlite_counts(db_path: Path):
    print("\n--- Verifying SQLite Database Counts ---")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM artifacts")
    art_count = cursor.fetchone()[0]
    print(f"Artifacts in database: {art_count}")

    cursor.execute("SELECT COUNT(*) FROM relationships")
    rel_count = cursor.fetchone()[0]
    print(f"Relationships in database: {rel_count}")

    cursor.execute("SELECT COUNT(*) FROM decisions")
    dec_count = cursor.fetchone()[0]
    print(f"Reconstructed decisions in database: {dec_count}")

    conn.close()

    assert art_count == 27528, f"Expected 27528 artifacts, found {art_count}"
    assert rel_count == 43142, f"Expected 43142 relationships, found {rel_count}"
    assert dec_count == 500, f"Expected 500 decisions, found {dec_count}"
    print("SUCCESS: SQLite counts verified.")


def test_query_sqs(agent: QueryAgent):
    print("\n--- Test Query 1: Why did atlaspay-ledger choose AWS SQS? ---")
    query = "Why did atlaspay-ledger choose AWS SQS?"
    response = agent.query(query)
    
    print("Response:")
    print("-" * 50)
    print(response[:800] + "\n...")
    print("-" * 50)
    
    assert "reconstructed decision" in response.lower(), "Should return a reconstructed decision"
    assert "aws sqs" in response.lower(), "Should mention AWS SQS in choice details"
    assert "adr-0001" in response.lower(), "Should trace grounding to ADR-0001"
    print("SUCCESS: AWS SQS query verified.")


def test_query_redis_incident(agent: QueryAgent):
    print("\n--- Test Query 2: What incident was caused by Redis cache? ---")
    query = "What incident was caused by Redis cache?"
    response = agent.query(query)
    
    print("Response:")
    print("-" * 50)
    print(response[:800] + "\n...")
    print("-" * 50)
    
    assert "reconstructed decision" in response.lower(), "Should return matching decisions"
    assert "redis" in response.lower(), "Should mention Redis"
    assert "inc-" in response.lower(), "Should trace to associated incidents (INC-xxxx)"
    print("SUCCESS: Redis incident query verified.")


def test_query_unknown(agent: QueryAgent):
    print("\n--- Test Query 3: Why did backstage choose Luxon? ---")
    query = "Why did backstage choose Luxon?"
    response = agent.query(query)
    
    print("Response:")
    print("-" * 50)
    print(response)
    print("-" * 50)
    
    assert "no structured decisions" in response.lower(), "Should handle unknown queries gracefully"
    print("SUCCESS: Unknown query verification checked.")


def main():
    db_path = Path("data/decision_memory.db")
    
    # We set FORCE_TFIDF=1 to ensure execution runs locally and instantly
    os.environ["FORCE_TFIDF"] = "1"

    # Step 1: Check if decision reconstruction runs successfully
    print("Running decision reconstruction script...")
    import subprocess
    cmd = [sys.executable, "scripts/reconstruct_decisions.py"]
    env = os.environ.copy()
    env["PYTHONPATH"] = "."
    env["GITHUB_TOKEN"] = "mock_token"
    
    result = subprocess.run(cmd, env=env, capture_output=True, text=True)
    print(result.stdout)
    if result.returncode != 0:
        print(f"ERROR: Reconstruction script failed: {result.stderr}")
        sys.exit(1)

    # Step 2: Check SQLite counts
    check_sqlite_counts(db_path)

    # Step 3: Test Query Agent
    print("\nInitializing QueryAgent...")
    agent = QueryAgent(db_path=db_path)

    test_query_sqs(agent)
    test_query_redis_incident(agent)
    test_query_unknown(agent)

    print("\nALL RECONSTRUCTION, STORAGE, AND QUERY TESTS PASSED SUCCESSFULLY!")


if __name__ == "__main__":
    main()
