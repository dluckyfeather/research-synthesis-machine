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
        
        # --- PHASE 1: OPENALEX PRECISION DISCOVERY ---
        import datetime
        current_year = datetime.datetime.now().year
        cutoff_year = current_year - 4
        
        sentences = re.split(r'(?<=[.!?]) +', text_input)
        audit_data = [] 

        st.subheader(f"📑 OpenAlex Evidence Cards ({current_year})")

        for sent in sentences:
            cit_match = re.search(r'\(([^)]+),?\s(\d{4})\)', sent)
            if cit_match:
                auth, year = cit_match.groups()
                
                # OpenAlex Search (We use semantic search for better grounding)
                # Adding mailto is 'polite' and gets you faster speeds
                clean_query = sent.replace('"', '').replace('(', '').replace(')', '')
                oa_url = f"https://api.openalex.org/works?search.semantic={clean_query}&filter=from_publication_date:{cutoff_year}-01-01&mailto=your-email@example.com"
                
                try:
                    res = requests.get(oa_url).json()
                    if res.get('results'):
                        paper = res['results'][0]
                        new_auth = paper['authorships'][0]['author']['display_name'] if paper['authorships'] else "Scholar"
                        new_year = paper['publication_year']
                        new_title = paper['display_name']
                        new_doi = paper.get('doi', '#')
                        
                        # OpenAlex abstracts are 'inverted'. We must reconstruct them.
                        inverted_index = paper.get('abstract_inverted_index', {})
                        if inverted_index:
                            # Simple reconstruction logic
                            word_index = [(pos, word) for word, positions in inverted_index.items() for pos in positions]
                            word_index.sort()
                            evidence_quote = " ".join([w[1] for w in word_index])[:500] + "..."
                        else:
                            evidence_quote = "Abstract not available for this record."

                        audit_data.append({
                            "original_sent": sent,
                            "new_cite": f"{new_auth} ({new_year})",
                            "evidence": evidence_quote,
                            "title": new_title,
                            "link": new_doi
                        })
                        
                        with st.expander(f"📌 Evidence: {new_auth} ({new_year})"):
                            st.markdown(f"**[{new_title}]({new_doi})**")
                            st.info(f"“{evidence_quote}”")
                except: continue

        # --- PHASE 2: DEEPSEEK REASONING (2026-STRICT) ---
        if audit_data:
            st.divider()
            evidence_context = "\n".join([
                f"CLAIM: {d['original_sent']}\nSOURCE: {d['new_cite']}\nEVIDENCE: {d['evidence']}" 
                for d in audit_data
            ])

            with st.spinner("DeepSeek-V4-Pro is auditing the manuscript..."):
                prompt = f"""
                You are a Forensic Research Integrity AI. 
                Use these <GROUNDED_SOURCES> to correct the user's text.
                
                <GROUNDED_SOURCES>
                {evidence_context}
                </GROUNDED_SOURCES>
                
                TASK:
                1. DELTA TABLE: Original Claim | Evidence Fact | Source Link.
                2. Q1 REWRITE: Rewrite the text to match the EVIDENCE. 
                3. REJECTION RULE: If the evidence is irrelevant to the claim (e.g. claim is grammar, source is medicine), delete the claim.
                """
                
                response = client.chat.completions.create(
                    model="deepseek-ai/DeepSeek-V4-Pro",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=2000,
                    temperature=0.1
                )
                st.markdown(response.choices[0].message.content)
