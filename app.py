import streamlit as st
import requests
import re
from huggingface_hub import InferenceClient

# --- ⚙️ MACHINE SETTINGS (SIDEBAR) ---
st.sidebar.header("⚙️ Machine Settings")

# 1. Handle the Token
hf_token = None
try:
    if "HF_TOKEN" in st.secrets:
        hf_token = st.secrets["HF_TOKEN"]
except Exception:
    hf_token = None

# If secret is missing, show manual input with a UNIQUE KEY
if not hf_token:
    hf_token = st.sidebar.text_input(
        "HF Token (Required)", 
        type="password", 
        key="hf_token_input" # Unique ID
    )
else:
    st.sidebar.success("✅ HF_TOKEN loaded from Secrets")

# 2. Handle the Model ID with a UNIQUE KEY
model_id = st.sidebar.text_input(
    "Model ID", 
    value="deepseek-ai/DeepSeek-V4-Pro", 
    key="model_id_input" # Unique ID
)

# --- 🚀 INITIALIZE CLIENT ---
if hf_token:
    client = InferenceClient(api_key=hf_token)
else:
    st.warning("⚠️ Waiting for HF Token in the sidebar...")
    st.stop()

# --- 🤖 START THE ENGINE ---
st.title("🤖 CitaGuard: HF-Native Research Engine")
# Set Model ID (You can also put this in secrets if you want to change models remotely)
model_id = st.sidebar.text_input("Model ID", value="deepseek-ai/DeepSeek-V4-Pro")
# --- PHASE 1: OPENALEX GROUNDING ---
st.subheader("📑 OpenAlex Evidence Cards (2026)")
sentences = re.split(r'(?<=[.!?]) +', text_input)
audit_data = []

for sent in sentences:
    if len(sent.strip()) < 10: continue
    
    # Use search.semantic for better conceptual matching
    # Email is required by OpenAlex for the 'polite' pool (faster results)
    oa_url = f"https://api.openalex.org/works?search.semantic={sent}&filter=from_publication_date:2022-01-01&mailto=your-email@example.com"
    
    try:
        res = requests.get(oa_url).json()
        results = res.get('results', [])
        
        if results:
            paper = results[0]
            # Reconstruct the Abstract (The "NotebookLM" part)
            index = paper.get('abstract_inverted_index', {})
            if index:
                # Rebuild text from the word-position map
                words = sorted([(pos, word) for word, positions in index.items() for pos in positions])
                evidence = " ".join([w[1] for w in words])[:600] + "..."
            else:
                evidence = "No abstract available. Context: " + paper.get('display_name', 'Research Paper')

            auth = paper['authorships'][0]['author']['display_name'] if paper['authorships'] else "Scholar"
            year = paper['publication_year']
            
            audit_data.append({
                "original": sent,
                "new_cite": f"{auth} ({year})",
                "evidence": evidence,
                "doi": paper.get('doi', '#')
            })
            
            # Show the evidence card immediately so you know it's working
            with st.expander(f"✅ Found Source: {auth} ({year})"):
                st.markdown(f"**[{paper['display_name']}]({paper.get('doi', '#')})**")
                st.info(f"**Evidence Quote:** {evidence}")
        else:
            st.warning(f"🔍 No 2022-2026 match for: {sent[:40]}...")
            
    except Exception as e:
        st.error(f"OpenAlex Error: {e}")

# --- PHASE 2: DEEPSEEK REASONING ---
if audit_data:
    st.divider()
    st.subheader("🧠 DeepSeek-V4-Pro Synthesis")
    
    # Structure the evidence context for DeepSeek
    context = "\n".join([f"CLAIM: {d['original']}\nSOURCE: {d['new_cite']}\nEVIDENCE: {d['evidence']}" for d in audit_data])
    
    with st.spinner("DeepSeek is analyzing the evidence..."):
        try:
            # DeepSeek-V4-Pro excels with structured instructions
            prompt = f"""
            You are a Q1 Academic Forensic AI. 
            Update the manuscript using ONLY the provided <evidence>.
            
            <evidence>
            {context}
            </evidence>
            
            TASK:
            1. DELTA REPORT: A table showing [Old Claim] | [New Fact from Evidence] | [Source Link].
            2. REWRITE: A high-impact academic paragraph.
            3. REJECTION: If evidence doesn't support the claim, delete the claim.
            """
            
            response = client.chat.completions.create(
                model=model_id,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2500
            )
            
            st.markdown(response.choices[0].message.content)
        except Exception as e:
            st.error(f"DeepSeek Synthesis Failed: {e}")
            st.info("Check if your HF Token has access to the DeepSeek-V4-Pro model.")
else:
    st.info("Paste your text above and ensure 'Research Objective' is set to start the audit.")
