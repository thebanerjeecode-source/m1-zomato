import os
import streamlit as st
from pathlib import Path

# Load environment variables
def _load_dotenv():
    env_path = Path(".env")
    if env_path.exists():
        for raw_line in env_path.read_text().splitlines():
            raw_line = raw_line.strip()
            if raw_line and not raw_line.startswith("#") and "=" in raw_line:
                k, v = raw_line.split("=", 1)
                os.environ[k] = v

_load_dotenv()

# Configure GROQ LLM environment
def _configure_groq_env():
    _load_dotenv()
    api_key = os.environ.get("GROQ_API_KEY")
    model = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")
    if not api_key:
        return False, None
    os.environ["PHASE3_LLM_BASE_URL"] = "https://api.groq.com/openai/v1"
    os.environ["PHASE3_LLM_API_KEY"] = api_key
    os.environ["PHASE3_LLM_MODEL"] = model
    return True, model

# Import phase functions
from phase2.retrieval import build_shortlist
from phase2.schemas import BudgetLevel as Phase2BudgetLevel
from phase2.schemas import Preferences as Phase2Preferences
from phase3.ranker import rank_with_llm
from phase3.schemas import Phase2Shortlist as Phase3Shortlist

st.set_page_config(page_title="CraveAI", page_icon="🍽️", layout="centered")

st.title("CraveAI 🍽️")
st.markdown("Discover the perfect dining experience tailored to your taste.")

# Form inputs
with st.form("preferences_form"):
    col1, col2 = st.columns(2)
    with col1:
        location = st.text_input("Location", placeholder="e.g. Bellandur")
        budget = st.selectbox("Budget Level", ["low", "medium", "high"], index=1)
    with col2:
        cuisine = st.text_input("Cuisine", placeholder="e.g. North Indian")
        min_rating = st.number_input("Min Rating", min_value=0.0, max_value=5.0, value=0.0, step=0.1)
    
    additional_preferences = st.text_area("Additional Preferences", placeholder="e.g. rooftop seating, quiet ambiance")
    
    submitted = st.form_submit_button("Get Recommendations")

if submitted:
    if not location or not cuisine:
        st.error("Please provide both Location and Cuisine.")
    else:
        with st.spinner("Finding the best restaurants for you..."):
            ready, model = _configure_groq_env()
            
            parquet_path = os.environ.get("PHASE1_PARQUET_PATH", "phase1/artifacts/zomato_clean.parquet")
            
            p2_prefs = Phase2Preferences(
                location=location,
                cuisine=cuisine,
                budget=Phase2BudgetLevel(budget),
                min_rating=min_rating,
                top_k=50,
                location_match="contains",
            )
            
            shortlist_resp = build_shortlist(Path(parquet_path), p2_prefs)
            
            p3_shortlist = Phase3Shortlist.model_validate(shortlist_resp.model_dump())
            ranked = rank_with_llm(p3_shortlist, source_path="streamlit:phase2_shortlist", top_n=5)
            
            used_llm = ranked.used_llm and ready
            
            warnings = []
            warnings.extend(shortlist_resp.warnings)
            warnings.extend(ranked.warnings)
            
            if warnings:
                st.info(f"**Note:** Used LLM: {'Yes' if used_llm else 'No'} | Model: {model if ready else 'N/A'}")
                for w in warnings:
                    st.warning(w)
            else:
                st.info(f"**Note:** Used LLM: {'Yes' if used_llm else 'No'} | Model: {model if ready else 'N/A'}")
            
            if not ranked.ranked:
                st.error("No restaurants found matching your criteria. Try relaxing your filters.")
            else:
                for idx, rec in enumerate(ranked.ranked):
                    with st.container():
                        st.subheader(f"#{rec.get('rank', idx + 1)} {rec.get('name', 'Unknown')}")
                        cols = st.columns(2)
                        with cols[0]:
                            st.write(f"**Rating:** {rec.get('rating') or 'N/A'} ⭐")
                            st.write(f"**Cost:** ₹{rec.get('cost') or 'N/A'} for two")
                        with cols[1]:
                            st.write(f"**Location:** {rec.get('location') or 'Unknown'}")
                            st.write(f"**Cuisines:** {', '.join(rec.get('cuisines', []))}")
                        
                        st.write(f"**Why we recommend this:** {rec.get('explanation', 'Matches your criteria.')}")
                        st.divider()
