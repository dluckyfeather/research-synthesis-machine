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
        
        # --- PHASE 1: GROUNDED EVIDENCE DISCOVERY ---
        import datetime
        current_year = datetime.datetime.now().year
        cutoff_year = current_year - 4
        
        sentences = re.split(r'(?<=[.!?]) +', text_input)
        audit_data = [] 

        for sent in sentences:
            cit_match = re.search(r'\(([^)]+),?\s(\d{4})\)', sent)
            if cit_match:
                auth, year = cit_match.groups()
                # Use 'query.bibliographic' for higher precision matching
                search_query = f"{sent[:50]}"
                discovery_url = f"https://api.crossref.org/works?query.bibliographic={search_query}&filter=from-pub-date:{cutoff_year}-01-01&rows=1"
                
                try:
                    res = requests.get(discovery_url).json()
                    item = res.get('message', {}).get('items', [{}])[0]
                    
                    if item:
                        # Extracting the Grounding Quote
                        raw_abstract = item.get('abstract', "No snippet available—verify via link.")
                        # Clean up XML tags often found in Crossref abstracts
                        clean_quote = re.sub('<[^<]+?>', '', raw_abstract)[:300] + "..."
                        
                        new_auth = item.get('author', [{'family': 'Scholar'}])[0].get('family')
                        new_year = item.get('created', {}).get('date-parts', [[2025]])[0][0]
                        doi = item.get('URL', '#')
                        title = item.get('title', ['Unknown'])[0]

                        audit_data.append({
                            "claim": sent,
                            "quote": clean_quote,
                            "new_cite": f"{new_auth} ({new_year})",
                            "link": doi,
                            "title": title
                        })
                        
                        # UI: NotebookLM Style Source Card
                        with st.container():
                            st.markdown(f"**Source Evidence for:** '{sent[:40]}...'")
                            st.caption(f"📄 {title}")
                            st.info(f"“{clean_quote}”")
                            st.markdown(f"[View Full Article]({doi})")
                except: continue

        # --- PHASE 2: EVIDENCE-BASED SYNTHESIS ---
        if audit_data:
            st.divider()
            # Feeding the QUOTES into the LLM so it doesn't hallucinate
            context_for_ai = "\n".join([f"CLAIM: {d['claim']} | QUOTE: {d['quote']} | NEW: {d['new_cite']}" for d in audit_data])
            
            prompt = f"""
            SYSTEM: You are a Grounded Academic Editor. 
            EVIDENCE: {context_for_ai}
            
            TASK:
            1. Create a Table: [Original Claim] | [Actual Quote from Source] | [Correction].
            2. Rewrite the text. You must ONLY use facts found in the 'QUOTE' section of the EVIDENCE. 
            3. If the Quote does not support the Claim, delete the Claim.
            """
            # ... (Rest of chat completion call)
