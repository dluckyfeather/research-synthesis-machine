import streamlit as st
import requests
import re
import os
from huggingface_hub import InferenceClient

st.set_page_config(page_title="CitaGuard Q1-Engine", layout="wide")

# UI Styling
st.markdown("""<style>.proof-box {background-color: #f0f2f6; border-left: 5px solid #2ecc71; padding: 15px; margin-bottom: 10px;}</style>""", unsafe_allow_html=True)

st.title("🤖 CitaGuard: HF-Native Research Engine")

with st.sidebar:
    st.header("⚙️ Machine Settings")
    # MANUAL TOKEN BYPASS
    user_token = st.text_input("HF Token (Paste here if secret fails)", type="password")
    
    # Logic to choose the token
    hf_token = user_token if user_token else os.environ.get("HF_TOKEN")
    
    obj = st.sidebar.text_area("Research Objective", "Analyze psychometric validity.")
    model_id = st.text_input("Model ID", "meta-llama/Meta-Llama-3-8B-Instruct")

text_input = st.text_area("Paste Literature Review Segment", height=250)

if st.button("EXECUTE SYNTHESIS"):
    if not hf_token:
        st.error("🔑 Token Required: Paste your HF Write Token in the sidebar to begin.")
    else:
        # Initialize Client with the found token
        client = InferenceClient(model_id, token=hf_token)
        
        # --- PHASE 1: API AUDIT ---
        citations = re.findall(r'\(([^)]+),?\s(\d{4})\)', text_input)
        audit_report = ""
        
        st.subheader("🔍 Integrity Audit")
        for author, year in citations:
            query = f"{author} {year}"
            try:
                res = requests.get(f"https://api.crossref.org/works?query.bibliographic={query}&rows=1").json()
                items = res.get('message', {}).get('items', [])
                if items:
                    title = items[0].get('title', ['Unknown'])[0]
                    audit_report += f"- VERIFIED: {author} ({year}) matches '{title}'\n"
                    st.markdown(f'<div class="proof-box">🟢 <b>{author} ({year})</b>: {title}</div>', unsafe_allow_html=True)
                else:
                    audit_report += f"- WARNING: {author} ({year}) could not be verified.\n"
                    st.error(f"🔴 Possible Hallucination: {author} ({year})")
            except:
                st.warning(f"Connection issue verifying {author}")

        # --- PHASE 2: NEURAL SYNTHESIS ---
        st.divider()
        st.subheader("🧠 Q1 Neural Rewrite")
        
        with st.spinner("Synthesizing through Hugging Face Inference Layers..."):
            # Llama-3 Prompt Format
            prompt = f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\nYou are a Q1 Academic Editor. Objective: {obj}. Audit Report: {audit_report}. Rewrite the text for high-impact flow.<|eot_id|><|start_header_id|>user<|end_header_id|>\n\n{text_input}<|eot_id|><|start_header_id|>assistant<|end_header_id|>"
            
            try:
                response = client.text_generation(
                    prompt,
                    max_new_tokens=1000,
                    temperature=0.2
                )
                st.success("Synthesis Complete")
                st.write(response)
                st.download_button("Download Q1 Manuscript", response, "Q1_Revised.txt")
            except Exception as e:
                st.error(f"Brain Error: {e}. Try clicking again in 10 seconds.")
