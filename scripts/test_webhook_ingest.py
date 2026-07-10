import json
import os
import sqlite3
import subprocess
import sys
import time
from pathlib import Path
import requests

# Ensure app is in the import path
sys.path.append(str(Path(__file__).parent.parent))


def main():
    db_path = Path("data/decision_memory.db")
    if not db_path.exists():
        print("ERROR: Database must exist to run live webhook test. Run reconstruction first.")
        sys.exit(1)

    # 1. Start uvicorn server in background
    port = 8099
    print(f"Starting uvicorn server on port {port}...")
    cmd = [sys.executable, "-m", "uvicorn", "app.main:app", "--port", str(port), "--log-level", "warning"]
    env = os.environ.copy()
    env["PYTHONPATH"] = "."
    env["FORCE_TFIDF"] = "1"
    
    server_process = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    # Wait for server boot and verify health check
    print("Waiting for FastAPI server to start...")
    ready = False
    for i in range(15):
        if server_process.poll() is not None:
            stdout, stderr = server_process.communicate()
            print(f"ERROR: Server terminated early: {stderr.decode()}")
            sys.exit(1)
        try:
            res = requests.get(f"http://localhost:{port}/api/stats", timeout=1)
            if res.status_code == 200:
                ready = True
                break
        except Exception:
            pass
        time.sleep(1)
        print(f"  - Waiting... ({i+1}s)")

    if not ready:
        print("ERROR: FastAPI server failed to respond within 15 seconds.")
        server_process.terminate()
        sys.exit(1)

    print("FastAPI Server is running in the background and ready.")

    # 2. Prepare mock push webhook payload
    # Commit message references ADR-0001 which is in the database!
    commit_sha = "aabbccddeeff0011223344556677889900112233"
    payload = {
        "repository": {"name": "atlaspay-ledger"},
        "pusher": {"name": "live-developer"},
        "commits": [
            {
                "id": commit_sha,
                "timestamp": "2026-07-10T14:30:00Z",
                "message": "Fix connection timeouts in atlaspay-ledger. Implements ADR-0001.",
                "url": f"https://github.com/Pray1503/atlaspay-ledger/commit/{commit_sha}",
                "author": {"name": "live-developer"}
            }
        ]
    }
    
    headers = {
        "X-GitHub-Event": "push",
        "Content-Type": "application/json"
    }

    try:
        # 3. Post webhook payload to FastAPI server
        url = f"http://localhost:{port}/api/webhooks/github"
        print(f"Posting mock webhook push event to {url}...")
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        
        print(f"Response Code: {response.status_code}")
        print(f"Response JSON: {response.json()}")
        
        assert response.status_code == 200, "Webhook endpoint should return 200"
        assert response.json().get("status") == "success", "Webhook result should be success"
        affected_seeds = response.json().get("affected_adr_seeds", [])
        assert any("adr-0001" in s.lower() for s in affected_seeds), "Should identify ADR-0001 as affected seed"

        # 4. Verify SQLite database changes
        print("\nVerifying database updates...")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check commit artifact exists
        commit_art_id = f"github:atlaspay-ledger:commit:{commit_sha}"
        cursor.execute("SELECT * FROM artifacts WHERE artifact_id = ?", (commit_art_id,))
        commit_row = cursor.fetchone()
        assert commit_row is not None, "New commit artifact must be stored in database"
        print(f"  - Verified Commit Artifact stored: {commit_row[0]} | Title: \"{commit_row[4]}\"")

        # Check relationship exists
        cursor.execute("SELECT * FROM relationships WHERE source_id = ?", (commit_art_id,))
        rel_row = cursor.fetchone()
        assert rel_row is not None, "Relationship link to ADR-0001 must be extracted and stored"
        print(f"  - Verified Relationship Link stored: {rel_row[3]} | Target: {rel_row[2]} | Reasoning: \"{rel_row[5]}\"")

        # Check decision details updated (evidence list must contain the new commit ID)
        from app.models.decision import Decision
        dec_id = Decision.generate_id("ADR-0001")
        cursor.execute("SELECT * FROM decisions WHERE decision_id = ?", (dec_id,))
        dec_row = cursor.fetchone()
        evidence_ids = json.loads(dec_row[12])
        assert commit_art_id in evidence_ids, "Reconstructed decision evidence list must include the new commit ID"
        print(f"  - Verified Reconstructed Decision updated. Evidence IDs: {evidence_ids}")

        # Cleanup mock test data so we don't pollute subsequent test runs
        print("Cleaning up mock test data from SQLite...")
        cursor.execute("DELETE FROM artifacts WHERE artifact_id = ?", (commit_art_id,))
        cursor.execute("DELETE FROM relationships WHERE source_id = ?", (commit_art_id,))
        conn.commit()

        conn.close()
        print("\nALL WEBHOOK LIVE INGESTION TESTS PASSED SUCCESSFULLY!")

    except Exception as e:
        print(f"\nTEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        # 5. Shutdown uvicorn server
        print("Shutting down FastAPI background server...")
        server_process.terminate()
        server_process.wait()
        print("Server shutdown completed.")


if __name__ == "__main__":
    main()
