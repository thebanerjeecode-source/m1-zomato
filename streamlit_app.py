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

st.set_page_config(page_title="CraveAI", page_icon="🍽️", layout="centered", initial_sidebar_state="collapsed")

# Custom CSS for premium typography and components
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=Inter:wght@400;500;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    h1, h2, h3, .app-title {
        font-family: 'Outfit', sans-serif;
        font-weight: 800;
    }
    
    .app-title {
        font-size: 3.5rem;
        background: linear-gradient(135deg, #FF6B6B 0%, #FF8E53 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0rem;
        padding-bottom: 0;
        text-align: center;
    }
    
    .app-subtitle {
        text-align: center;
        font-size: 1.1rem;
        color: #666;
        margin-bottom: 2rem;
        font-weight: 400;
    }

    .rec-card {
        background-color: #ffffff;
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 20px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.05);
        border: 1px solid #f0f0f0;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    
    .rec-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 15px 35px rgba(0,0,0,0.1);
    }
    
    .rec-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        border-bottom: 1px solid #f0f0f0;
        padding-bottom: 16px;
        margin-bottom: 16px;
    }
    
    .rec-title-wrapper {
        display: flex;
        align-items: center;
        gap: 12px;
    }
    
    .rec-rank {
        background: #FF6B6B;
        color: white;
        width: 32px;
        height: 32px;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 50%;
        font-weight: bold;
        font-family: 'Outfit', sans-serif;
        font-size: 1.1rem;
    }
    
    .rec-name {
        font-size: 1.5rem;
        font-weight: 700;
        color: #1a1a1a;
        margin: 0;
        font-family: 'Outfit', sans-serif;
    }
    
    .rec-rating {
        background: #4CAF50;
        color: white;
        padding: 6px 12px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.95rem;
        display: flex;
        align-items: center;
        gap: 4px;
    }
    
    .rec-meta {
        display: flex;
        gap: 20px;
        color: #555;
        font-size: 0.95rem;
        margin-bottom: 16px;
    }
    
    .rec-meta span {
        display: flex;
        align-items: center;
        gap: 6px;
    }
    
    .cuisine-tags {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin-bottom: 16px;
    }
    
    .cuisine-tag {
        background: #f8f9fa;
        color: #555;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 0.85rem;
        font-weight: 500;
        border: 1px solid #e9ecef;
    }
    
    .rec-explanation {
        background: #fff9f9;
        padding: 16px;
        border-radius: 12px;
        color: #444;
        font-size: 0.95rem;
        line-height: 1.6;
        border-left: 4px solid #FF6B6B;
    }
    
    .rec-explanation-title {
        font-weight: 600;
        color: #FF6B6B;
        margin-bottom: 8px;
        display: flex;
        align-items: center;
        gap: 6px;
    }
    
    /* Override Streamlit Dark Mode to keep cards looking good */
    @media (prefers-color-scheme: dark) {
        .rec-card {
            background-color: #1e1e1e;
            border-color: #333;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        }
        .rec-name { color: #f0f0f0; }
        .rec-header { border-bottom-color: #333; }
        .rec-meta { color: #aaa; }
        .cuisine-tag { background: #2d2d2d; color: #ccc; border-color: #444; }
        .rec-explanation { background: #2a2020; color: #ddd; }
        .app-subtitle { color: #aaa; }
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="app-title">CraveAI</h1>', unsafe_allow_html=True)
st.markdown('<p class="app-subtitle">Discover the perfect dining experience tailored to your taste</p>', unsafe_allow_html=True)

# Form inputs
with st.container():
    with st.form("preferences_form", border=True):
        st.markdown("### 🎯 Tell us what you're craving")
        col1, col2 = st.columns(2)
        with col1:
            location = st.text_input("📍 Location", placeholder="e.g. Bellandur")
            budget = st.selectbox("💰 Budget Level", ["low", "medium", "high"], index=1)
        with col2:
            cuisine = st.text_input("🍜 Cuisine", placeholder="e.g. North Indian")
            min_rating = st.slider("⭐ Minimum Rating", min_value=0.0, max_value=5.0, value=0.0, step=0.1)
        
        additional_preferences = st.text_area("✨ Additional Preferences", placeholder="e.g. rooftop seating, quiet ambiance, romantic")
        
        submitted = st.form_submit_button("Discover Restaurants", use_container_width=True)

if submitted:
    if not location or not cuisine:
        st.error("Please provide both Location and Cuisine.")
    else:
        with st.spinner("AI is analyzing local restaurants to find your perfect match..."):
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
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            if warnings:
                with st.expander("System Notices", expanded=False):
                    for w in warnings:
                        st.info(w)
            
            if not ranked.ranked:
                st.error("No restaurants found matching your criteria. Try relaxing your filters.")
            else:
                st.success(f"✨ Found {len(ranked.ranked)} perfect matches for you!")
                
                for idx, rec in enumerate(ranked.ranked):
                    name = rec.get('name', 'Unknown')
                    rating = rec.get('rating')
                    rating_str = f"{rating} ★" if rating else "New"
                    cost = rec.get('cost')
                    cost_str = f"₹{cost} for two" if cost else "Cost N/A"
                    loc = rec.get('location', 'Unknown')
                    cuisines = rec.get('cuisines', [])
                    explanation = rec.get('explanation', 'Matches your criteria.')
                    
                    cuisines_html = "".join([f'<span class="cuisine-tag">{c}</span>' for c in cuisines])
                    
                    card_html = f"""
                    <div class="rec-card">
                        <div class="rec-header">
                            <div class="rec-title-wrapper">
                                <div class="rec-rank">{idx + 1}</div>
                                <h3 class="rec-name">{name}</h3>
                            </div>
                            <div class="rec-rating">{rating_str}</div>
                        </div>
                        
                        <div class="rec-meta">
                            <span>📍 {loc}</span>
                            <span>💰 {cost_str}</span>
                        </div>
                        
                        <div class="cuisine-tags">
                            {cuisines_html}
                        </div>
                        
                        <div class="rec-explanation">
                            <div class="rec-explanation-title">✨ Why we recommend this</div>
                            {explanation}
                        </div>
                    </div>
                    """
                    st.markdown(card_html, unsafe_allow_html=True)
                
                st.caption(f"Recommendations powered by **{model if ready else 'Deterministic Search'}**")
