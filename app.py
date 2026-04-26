# --- 🤖 START THE ENGINE ---
st.title("🤖 CitaGuard: HF-Native Research Engine")

# 1. CREATE THE MISSING VARIABLE
# This is the 'text_input' that was causing the NameError
text_input = st.text_area(
    "Paste Literature Review Segment", 
    height=250, 
    placeholder="Paste your paragraph here (e.g., 'The TOEFL ITP... (Rogers, 2011)')",
    key="user_lit_review"
)

# 2. ONLY RUN IF THERE IS TEXT
if text_input:
    st.subheader("📑 OpenAlex Evidence Cards (2026)")
    
    # Now 'text_input' exists and can be split
    sentences = re.split(r'(?<=[.!?]) +', text_input)
    audit_data = []

    for sent in sentences:
        if len(sent.strip()) < 10: continue
        
        # OpenAlex Semantic Search
        oa_url = f"https://api.openalex.org/works?search.semantic={sent}&filter=from_publication_date:2022-01-01"
        
        try:
            res = requests.get(oa_url).json()
            results = res.get('results', [])
            
            if results:
                paper = results[0]
                # Reconstruct Abstract
                index = paper.get('abstract_inverted_index', {})
                if index:
                    words = sorted([(pos, word) for word, positions in index.items() for pos in positions])
                    evidence = " ".join([w[1] for w in words])[:600] + "..."
                else:
                    evidence = "Snippet: " + paper.get('display_name')

                auth = paper['authorships'][0]['author']['display_name'] if paper['authorships'] else "Scholar"
                year = paper['publication_year']
                
                audit_data.append({
                    "original": sent,
                    "new_cite": f"{auth} ({year})",
                    "evidence": evidence,
                    "doi": paper.get('doi', '#')
                })
                
                with st.expander(f"✅ Found: {auth} ({year})"):
                    st.info(f"**Evidence:** {evidence}")
            else:
                st.warning(f"🔍 No match found for: {sent[:40]}...")
        except:
            continue

    # --- PHASE 2: DEEPSEEK REASONING ---
    if audit_data:
        st.divider()
        st.subheader("🧠 DeepSeek-V4-Pro Synthesis")
        # (Rest of your DeepSeek logic goes here...)
