import streamlit as st
import requests
import json
import time

# API endpoint
API_URL = "http://127.0.0.1:8000/ask"
HEALTH_URL = "http://127.0.0.1:8000/health"

st.set_page_config(page_title="DecisionDNA", page_icon="ðŸ§¬", layout="wide")

st.title("DecisionDNA ðŸ§¬")
st.markdown("**Engineering decision intelligence and organizational memory system.**")

# Session state for question
if "current_question" not in st.session_state:
    st.session_state.current_question = ""

if "ask_trigger" not in st.session_state:
    st.session_state.ask_trigger = False

# Suggested Questions
st.markdown("### Suggested Questions")
col1, col2 = st.columns(2)
with col1:
    if st.button("Why does Backstage use MSW for mocking?", use_container_width=True):
        st.session_state.current_question = "Why does Backstage use MSW for mocking?"
        st.session_state.ask_trigger = True
with col2:
    if st.button("What was the decision regarding ADR008: Default Catalog File Name?", use_container_width=True):
        st.session_state.current_question = "What was the decision regarding ADR008: Default Catalog File Name?"
        st.session_state.ask_trigger = True

question_input = st.text_input("Ask a question about the repository:", value=st.session_state.current_question, key="q_input")

def ask_api(q):
    try:
        response = requests.post(API_URL, json={"question": q}, timeout=60)
        if response.status_code == 200:
            return response.json(), None
        else:
            return None, f"Error {response.status_code}: {response.text}"
    except Exception as e:
        return None, f"Connection failed: {e}. Is the FastAPI server running?"

if st.button("Ask DecisionDNA", type="primary") or st.session_state.ask_trigger:
    st.session_state.ask_trigger = False

    q_to_ask = question_input if not st.session_state.current_question else st.session_state.current_question
    # Reset for next type
    st.session_state.current_question = question_input

    if not q_to_ask.strip():
        st.warning("Please enter a question.")
    else:
        with st.spinner("Retrieving evidence and reconstructing decision..."):
            data, error = ask_api(q_to_ask)

        if error:
            st.error(error)
        elif data:
            st.success("Decision reconstructed successfully!")

            recon = data.get("reconstruction", {})
            package = data.get("package", {})
            supported = data.get("supported_artifacts", [])

            st.header("1. RECONSTRUCTED DECISION")
            st.info(recon.get("answer", ""))

            st.header("2. WHY THIS DECISION WAS MADE")
            st.write(recon.get("reasoning_summary", ""))

            st.header("3. DECISION")
            if recon.get("decision"):
                st.write(recon.get("decision"))
            else:
                st.write("*No formal decision statement identified.*")

            st.header("4. CONFIDENCE AND UNCERTAINTY")
            st.metric("Confidence", recon.get("confidence", "UNKNOWN"))
            if recon.get("uncertainty"):
                st.warning(f"Uncertainty: {recon.get('uncertainty')}")

            if recon.get("insufficient_evidence"):
                st.header("5. INSUFFICIENT EVIDENCE")
                st.error("INSUFFICIENT EVIDENCE: The system could not confidently answer the question based only on the supplied evidence.")

            if recon.get("implementation_evidence"):
                st.header("6. IMPLEMENTATION EVIDENCE")
                st.write(recon.get("implementation_evidence"))

            if recon.get("alternatives"):
                st.header("7. ALTERNATIVES")
                for alt in recon.get("alternatives"):
                    st.write(f"- {alt}")

            if recon.get("outcome"):
                st.header("8. OUTCOME")
                st.write(recon.get("outcome"))

            st.header("9. RETRIEVED DECISION EVIDENCE")

            # Map artifact IDs to data
            art_map = {a["artifact_id"]: a for a in package.get("artifacts", [])}

            # Show cards for supported artifacts
            if not supported:
                st.write("No specific artifacts cited.")
            else:
                for idx, art in enumerate(supported):
                    with st.expander(f"{art['artifact_type'].upper()} | {art['artifact_id'].split(':')[-1]}"):
                        st.markdown(f"**Title:** {art.get('title', 'Unknown')}")
                        st.markdown(f"**Reason:** {art.get('reason', 'Graph Expansion')}")
                        st.markdown(f"**URL:** [View on GitHub]({art.get('url', '#')})")

            st.header("10. EXPLICIT IMPLEMENTATION LINKS")
            rels = package.get("relationships", [])
            if not rels:
                st.write("*No explicit graph relationships were traversed.*")
            else:
                st.markdown("**(Deterministic Graph Edges)**")
                for rel in rels:
                    src_id = rel.get("source_artifact_id")
                    tgt_id = rel.get("target_artifact_id")
                    rel_type = rel.get("relationship_type")

                    src_art = art_map.get(src_id)
                    tgt_art = art_map.get(tgt_id)

                    src_label = src_id.split(":")[-1]
                    if src_art:
                        src_label = f"{src_art['artifact_type'].upper()} {src_label}"

                    tgt_label = tgt_id.split(":")[-1]
                    if tgt_art:
                        tgt_label = f"{tgt_art['artifact_type'].upper()} {tgt_label}"

                    st.code(f"{src_label}\n  â†“ {rel_type}\n{tgt_label}")
