import streamlit as st
import requests
import re
import os
from huggingface_hub import InferenceClient

# Initialize the 'Brain' using the internal HF Token
# It will look for the secret you added to the Space settings
hf_token = os.environ.get("HF_TOKEN")
client = InferenceClient("meta-llama/Meta-Llama-3-8B-Instruct", token=hf_token)

st.set_page_config(page_title="CitaGuard Q1-Engine", layout="wide")

st.markdown("""<style>.proof-box {background-color: #f0f2f6; border-left: 5px solid #2ecc71; padding: 15px; margin-bottom: 10px;}</style>""", unsafe_allow_html=True)

st.title("🤖 CitaGuard: HF-Native Research Engine")

with st.sidebar:
    st.header("⚙️ Machine Settings")
    obj = st.text_area("Research Objective", "Analyze the psychometric validity of listening tests.")
    # You can change the model ID here if you want to try different "brains"
    model_id = st.text_input("Model ID", "meta-llama/Meta-Llama-3-8B-Instruct")

text_input = st.text_area("Paste Literature Review Segment", height=250)

if st.button("EXECUTE SYNTHESIS"):
    if not hf_token:
        st.error("HF_TOKEN Missing! Go to Space Settings -> Secrets and add your Hugging Face Write Token as 'HF_TOKEN'.")
    else:
        # --- PHASE 1: API AUDIT (The Fact Checker) ---
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

        # --- PHASE 2: NEURAL SYNTHESIS (The LLM) ---
        st.divider()
        st.subheader("🧠 Q1 Neural Rewrite")
        
        with st.spinner("Synthesizing through Hugging Face Inference Layers..."):
            prompt = f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\nYou are a Q1 Academic Editor. Objective: {obj}. Audit Report: {audit_report}<|eot_id|><|start_header_id|>user<|end_header_id|>\n\nRewrite this text for high-impact flow and interconnectedness. Fix any outdated citations: {text_input}<|eot_id|><|start_header_id|>assistant<|end_header_id|>"
            
            try:
                response = client.text_generation(
                    prompt,
                    max_new_tokens=1000,
                    temperature=0.2,
                    repetition_penalty=1.2
                )
                
                st.success("Synthesis Complete")
                st.write(response)
                st.download_button("Download Q1 Manuscript", response, "Q1_Revised.txt")
            except Exception as e:
                st.error(f"Inference Error: {e}. The model might be loading or the API might be busy. Try again in 30 seconds.")
