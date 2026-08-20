"""
Zomato AI Recommender — Premium Streamlit Frontend.
Design system adapted from Google Stitch prototype (docs/stitch_zomato_ai_recommender).
"""

import streamlit as st
import logging
import time

# ── Page Config (must be first Streamlit call) ──────────────────
st.set_page_config(
    page_title="Zomato AI Recommender",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="expanded",
)

from src.config import settings
from src.data.loader import DatasetLoader
from src.models.preferences import UserPreferences
from src.services.recommendation import RecommendationService

logger = logging.getLogger(__name__)

# ── Constants ───────────────────────────────────────────────────
BUDGET_MAP = {"₹": "low", "₹₹": "medium", "₹₹₹": "high"}
BUDGET_LABELS = {"low": "Budget Friendly", "medium": "Medium Budget", "high": "Premium Dining"}

# ── Cached Services ─────────────────────────────────────────────

@st.cache_resource(show_spinner=False)
def get_loader():
    return DatasetLoader()

@st.cache_resource(show_spinner=False)
def get_service():
    return RecommendationService()

@st.cache_data(show_spinner=False)
def get_cities():
    loader = get_loader()
    loader.load()
    return loader.get_cities()

@st.cache_data(show_spinner=False)
def get_cuisines():
    loader = get_loader()
    loader.load()
    return loader.get_cuisines()

@st.cache_data(show_spinner=False)
def get_restaurant_count():
    loader = get_loader()
    data = loader.load()
    return len(data)


# ── CSS Design System (from Stitch DESIGN.md) ──────────────────

def inject_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Outfit:wght@600;700;900&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap');

    /* ── Color Tokens ─────────────────────────────── */
    :root {
        --bg-primary: #0F1117;
        --bg-surface: #11131a;
        --bg-card: #1d1f26;
        --bg-card-high: #282a31;
        --bg-card-highest: #33343c;
        --accent: #ff535a;
        --accent-soft: #ffb3b1;
        --accent-hover: #FF4154;
        --gold: #edc157;
        --gold-bright: #FFD166;
        --green: #4ae183;
        --green-container: #00a657;
        --text-primary: #e2e2ec;
        --text-secondary: #a0a8b4;
        --text-muted: #636e72;
        --border: #5b403f;
        --border-subtle: #33343c;
        --amber: #F39C12;
    }

    /* ── Global Overrides ─────────────────────────── */
    .stApp {
        background-color: var(--bg-primary) !important;
        color: var(--text-primary) !important;
        font-family: 'Inter', sans-serif !important;
    }

    section[data-testid="stSidebar"] {
        background-color: #2a2d35 !important;
        border-right: 1px solid var(--border) !important;
    }

    section[data-testid="stSidebar"] .stMarkdown,
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] .stSelectbox label,
    section[data-testid="stSidebar"] .stSlider label {
        color: #dcdde1 !important;
        font-family: 'Inter', sans-serif !important;
    }

    /* Selectbox and text inputs */
    .stSelectbox > div > div,
    .stTextArea textarea,
    .stTextInput input {
        background-color: #d1d5db !important;
        color: #1a1c24 !important;
        border-color: #9ca3af !important;
        border-radius: 10px !important;
        font-family: 'Inter', sans-serif !important;
    }

    .stSelectbox > div > div:focus-within,
    .stTextArea textarea:focus,
    .stTextInput input:focus {
        border-color: var(--accent) !important;
        box-shadow: 0 0 0 1px var(--accent) !important;
    }

    /* Placeholder text — darker on bright bg */
    .stTextArea textarea::placeholder,
    .stTextInput input::placeholder {
        color: #4b5563 !important;
        opacity: 1 !important;
    }

    /* Selectbox selected value — dark on bright bg */
    .stSelectbox [data-baseweb="select"] span,
    .stSelectbox [data-baseweb="select"] div[class*="singleValue"],
    .stSelectbox [data-baseweb="select"] div[class*="placeholder"],
    .stSelectbox svg {
        color: #1a1c24 !important;
        fill: #1a1c24 !important;
    }

    /* Dropdown menu options */
    .stSelectbox [data-baseweb="menu"],
    .stSelectbox [role="listbox"],
    .stSelectbox [data-baseweb="menu"] li,
    .stSelectbox [role="option"] {
        background-color: #d1d5db !important;
        color: #1a1c24 !important;
    }
    .stSelectbox [role="option"]:hover,
    .stSelectbox [data-baseweb="menu"] li:hover {
        background-color: var(--accent) !important;
        color: #ffffff !important;
    }

    /* Radio buttons (Budget selector) */
    .stRadio > div {
        background-color: transparent !important;
    }
    .stRadio label,
    .stRadio [data-baseweb="radio"] label,
    .stRadio span {
        color: #ffffff !important;
    }

    /* Slider */
    .stSlider > div > div > div > div {
        background-color: var(--gold) !important;
    }

    /* Hide Streamlit branding */
    #MainMenu, header[data-testid="stHeader"], footer {
        visibility: hidden !important;
    }

    div[data-testid="stDecoration"] {
        display: none !important;
    }

    /* ── Custom Components ────────────────────────── */

    .app-header {
        text-align: center;
        padding: 32px 16px 8px;
    }
    .app-header h1 {
        font-family: 'Outfit', sans-serif;
        font-size: 42px;
        font-weight: 900;
        color: var(--text-primary);
        margin-bottom: 4px;
        letter-spacing: -0.02em;
    }
    .app-header .tagline {
        font-family: 'Inter', sans-serif;
        font-size: 18px;
        color: var(--text-secondary);
        margin-bottom: 12px;
    }
    .stats-badge {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        background: var(--bg-card);
        padding: 6px 16px;
        border-radius: 100px;
        border: 1px solid var(--border-subtle);
        font-size: 12px;
        color: var(--text-secondary);
    }
    .stats-badge .powered {
        color: var(--gold);
        font-weight: 600;
    }

    /* Summary banner */
    .summary-banner {
        background: rgba(29, 31, 38, 0.7);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid var(--border-subtle);
        border-radius: 16px;
        padding: 20px 24px;
        text-align: center;
        margin: 16px 0 24px;
        position: relative;
        overflow: hidden;
    }
    .summary-banner::before {
        content: "";
        position: absolute;
        inset: -1px;
        border-radius: inherit;
        background: linear-gradient(135deg, var(--accent), #906d00);
        z-index: -1;
        opacity: 0.4;
    }
    .summary-banner p {
        font-style: italic;
        color: var(--text-secondary);
        font-size: 16px;
        line-height: 24px;
        margin: 0;
    }
    .summary-banner strong {
        color: var(--text-primary);
        font-style: normal;
    }

    /* Relaxation alert */
    .relax-alert {
        background: rgba(243, 156, 18, 0.1);
        border: 1px solid rgba(243, 156, 18, 0.3);
        border-radius: 12px;
        padding: 12px 16px;
        margin: 8px 0 16px;
        font-size: 14px;
        color: var(--amber);
    }

    /* Fallback notice */
    .fallback-notice {
        background: rgba(29, 31, 38, 0.5);
        border: 1px solid var(--border-subtle);
        border-radius: 12px;
        padding: 12px 16px;
        margin: 8px 0 16px;
        font-size: 13px;
        color: var(--text-secondary);
        text-align: center;
    }

    /* Restaurant Card */
    @keyframes fadeUp {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }

    .restaurant-card {
        background: var(--bg-card);
        border: 1px solid var(--border-subtle);
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 16px;
        position: relative;
        transition: transform 0.3s ease, box-shadow 0.3s ease, border-color 0.3s ease;
        animation: fadeUp 0.6s cubic-bezier(0.16, 1, 0.3, 1) forwards;
        opacity: 0;
    }
    .restaurant-card:nth-child(1) { animation-delay: 0.1s; }
    .restaurant-card:nth-child(2) { animation-delay: 0.2s; }
    .restaurant-card:nth-child(3) { animation-delay: 0.3s; }
    .restaurant-card:nth-child(4) { animation-delay: 0.4s; }
    .restaurant-card:nth-child(5) { animation-delay: 0.5s; }

    .restaurant-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 20px 40px rgba(0,0,0,0.4);
        border-color: var(--border);
    }

    .card-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        margin-bottom: 4px;
    }

    .card-name {
        font-family: 'Outfit', sans-serif;
        font-size: 24px;
        font-weight: 600;
        color: var(--text-primary);
        margin: 0;
        line-height: 32px;
    }

    .card-cost {
        font-size: 14px;
        font-weight: 600;
        color: var(--text-secondary);
        background: var(--bg-card-high);
        padding: 4px 12px;
        border-radius: 8px;
        white-space: nowrap;
    }

    .card-location {
        font-size: 14px;
        color: var(--text-secondary);
        margin-bottom: 12px;
        display: flex;
        align-items: center;
        gap: 4px;
    }

    .card-rating-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 16px;
    }

    .rank-badge {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 36px;
        height: 36px;
        background: linear-gradient(135deg, #906d00, var(--gold));
        color: #11131a;
        font-weight: 700;
        font-size: 14px;
        border-radius: 50%;
        border: 2px solid var(--gold);
        box-shadow: 0 0 12px rgba(237, 193, 87, 0.3);
    }

    .rating-badge {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        background: rgba(17, 19, 26, 0.8);
        backdrop-filter: blur(8px);
        padding: 4px 12px;
        border-radius: 8px;
        border: 1px solid rgba(237, 193, 87, 0.3);
        font-size: 14px;
        font-weight: 700;
        color: var(--gold);
    }

    .cuisine-pills {
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
        margin-bottom: 16px;
    }
    .cuisine-pill {
        background: var(--bg-card-high);
        color: var(--text-secondary);
        padding: 4px 12px;
        border-radius: 100px;
        font-size: 12px;
        font-weight: 500;
        border: 1px solid var(--border-subtle);
    }

    .ai-reason {
        background: var(--bg-card-high);
        border: 1px solid var(--border-subtle);
        border-radius: 12px;
        padding: 14px 16px;
        position: relative;
        overflow: hidden;
    }
    .ai-reason::before {
        content: "";
        position: absolute;
        left: 0;
        top: 0;
        bottom: 0;
        width: 3px;
        background: var(--accent);
    }
    .ai-reason .ai-label {
        font-size: 11px;
        font-weight: 700;
        color: var(--accent);
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 6px;
    }
    .ai-reason .ai-text {
        font-size: 14px;
        line-height: 22px;
        color: var(--text-secondary);
        margin: 0;
    }

    /* Welcome hero */
    .welcome-hero {
        text-align: center;
        padding: 80px 20px;
    }
    .welcome-hero .emojis {
        font-size: 64px;
        margin-bottom: 24px;
        letter-spacing: 16px;
    }
    .welcome-hero h2 {
        font-family: 'Outfit', sans-serif;
        font-size: 36px;
        font-weight: 700;
        color: var(--text-primary);
        margin-bottom: 8px;
    }
    .welcome-hero p {
        font-size: 16px;
        color: var(--text-secondary);
    }

    /* Empty state */
    .empty-state {
        text-align: center;
        padding: 60px 20px;
    }
    .empty-state .emoji {
        font-size: 72px;
        margin-bottom: 16px;
    }
    .empty-state h3 {
        font-family: 'Outfit', sans-serif;
        font-size: 24px;
        font-weight: 600;
        color: var(--text-primary);
        margin-bottom: 8px;
    }
    .empty-state p {
        color: var(--text-secondary);
        font-size: 15px;
    }

    /* Footer */
    .app-footer {
        border-top: 1px solid var(--border-subtle);
        padding: 24px 16px;
        text-align: center;
        margin-top: 32px;
    }
    .app-footer .brand {
        font-family: 'Outfit', sans-serif;
        font-weight: 700;
        font-size: 14px;
        color: var(--text-primary);
        margin-bottom: 8px;
    }
    .app-footer .meta {
        font-size: 12px;
        color: var(--text-secondary);
    }

    /* Budget pills */
    .budget-pills {
        display: flex;
        gap: 8px;
    }
    .budget-pill {
        flex: 1;
        padding: 8px 0;
        border-radius: 10px;
        border: 1px solid var(--border);
        background: transparent;
        color: var(--text-secondary);
        font-weight: 600;
        font-size: 14px;
        cursor: pointer;
        text-align: center;
        transition: all 0.2s ease;
    }
    .budget-pill.active {
        background: var(--accent) !important;
        color: #fff !important;
        border-color: var(--accent) !important;
        font-weight: 700;
        box-shadow: 0 0 20px rgba(255,83,90,0.2);
    }

    /* Status badge */
    .status-badge {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 6px;
        font-size: 12px;
        padding: 4px 0;
    }
    .status-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        display: inline-block;
    }
    .status-dot.green { background: var(--green); box-shadow: 0 0 6px var(--green); }
    .status-dot.amber { background: var(--amber); box-shadow: 0 0 6px var(--amber); }

    /* Sidebar brand */
    .sidebar-brand h1 {
        font-family: 'Outfit', sans-serif;
        font-size: 22px;
        font-weight: 700;
        color: var(--accent-soft);
        margin-bottom: 0;
    }
    .sidebar-brand p {
        font-size: 12px;
        color: var(--text-secondary);
        margin-top: 2px;
    }

    /* Streamlit button override */
    .stButton > button {
        width: 100%;
        background: var(--accent) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 12px 24px !important;
        font-family: 'Outfit', sans-serif !important;
        font-weight: 700 !important;
        font-size: 16px !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 0 20px rgba(255,83,90,0.2) !important;
    }
    .stButton > button:hover {
        background: var(--accent-hover) !important;
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(255,83,90,0.3) !important;
    }
    .stButton > button:active {
        transform: scale(0.97);
    }

    /* Rating display in sidebar */
    .rating-display {
        font-weight: 700;
        color: var(--gold);
    }

    /* Spinner override */
    .stSpinner > div {
        border-top-color: var(--accent) !important;
    }
    </style>
    """, unsafe_allow_html=True)


# ── Helper Functions ────────────────────────────────────────────

def render_stars(rating: float) -> str:
    """Generate HTML star rating display."""
    full = int(rating)
    half = 1 if (rating - full) >= 0.3 else 0
    empty = 5 - full - half
    stars = "★" * full + ("½" if half else "") + "☆" * empty
    return f'<span style="color: var(--gold); letter-spacing: 2px;">{stars}</span>'


def render_card(rec, index: int) -> str:
    """Render a single restaurant recommendation card."""
    # Parse cuisines
    cuisines = [c.strip() for c in (rec.cuisine or "").split(",") if c.strip()]
    cuisine_pills = "".join(
        f'<span class="cuisine-pill">{c}</span>' for c in cuisines[:5]
    )

    stars_html = render_stars(rec.rating)

    return f"""
    <div class="restaurant-card" style="animation-delay: {0.1 * (index + 1)}s;">
        <div class="card-rating-row">
            <div class="rank-badge">#{rec.rank}</div>
            <div class="rating-badge">
                {rec.rating:.1f} ★
            </div>
        </div>
        <div class="card-header">
            <h3 class="card-name">{rec.restaurant_name}</h3>
            <span class="card-cost">{rec.estimated_cost}</span>
        </div>
        <div class="card-location">📍 {rec.explanation.split(' in ')[-1].split(' that ')[0].split(',')[0] if ' in ' in rec.explanation else ''}</div>
        <div class="cuisine-pills">{cuisine_pills}</div>
        <div class="ai-reason">
            <div class="ai-label">✨ AI Reason</div>
            <p class="ai-text">{rec.explanation}</p>
        </div>
    </div>
    """


# ── Sidebar ─────────────────────────────────────────────────────

def render_sidebar():
    with st.sidebar:
        st.markdown("""
        <div class="sidebar-brand">
            <h1>Foodie Elite</h1>
            <p>AI Gourmet Guide</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("### 🍽️ Your Preferences")

        # Location
        cities = get_cities()
        location = st.selectbox(
            "Location",
            options=cities,
            index=cities.index("Bangalore") if "Bangalore" in cities else 0,
            key="location_select",
        )

        # Budget numeric slider
        budget_value = st.slider(
            "Budget (₹ for two)",
            min_value=500,
            max_value=20000,
            value=1500,
            step=500,
            format="₹%d",
            key="budget_slider",
        )
        # Map numeric value to budget tier
        if budget_value <= 500:
            budget = "low"
        elif budget_value <= 1500:
            budget = "medium"
        else:
            budget = "high"

        # Cuisine
        cuisines = get_cuisines()
        cuisine_options = ["Any"] + cuisines
        cuisine_selection = st.selectbox(
            "Cuisine",
            options=cuisine_options,
            index=0,
            key="cuisine_select",
        )
        cuisine = None if cuisine_selection == "Any" else cuisine_selection

        # Rating slider
        min_rating = st.slider(
            "Minimum Rating",
            min_value=0.0,
            max_value=5.0,
            value=4.0,
            step=0.5,
            format="%.1f",
            key="rating_slider",
        )

        # Additional preferences
        additional = st.text_area(
            "Additional Preferences",
            placeholder="e.g. rooftop seating, family-friendly, live music",
            height=68,
            key="additional_prefs",
        )

        # Submit button
        submitted = st.button("🔍 Get Recommendations", key="submit_btn", use_container_width=True)

        # Status badge
        is_ai = settings.is_groq_configured
        dot_class = "green" if is_ai else "amber"
        status_text = "AI Powered" if is_ai else "Smart Fallback"
        st.markdown(f"""
        <div class="status-badge">
            <span class="status-dot {dot_class}"></span>
            <span style="color: {'var(--green)' if is_ai else 'var(--amber)'};">{status_text}</span>
        </div>
        """, unsafe_allow_html=True)

        return submitted, location, budget, cuisine, min_rating, additional or None


# ── Main Content ────────────────────────────────────────────────

def render_header():
    """Render the main content header with title and stats."""
    count = get_restaurant_count()
    cities_count = len(get_cities())

    st.markdown(f"""
    <div class="app-header">
        <h1>🍽️ Zomato AI Recommender</h1>
        <p class="tagline">Discover your next favourite restaurant</p>
        <div class="stats-badge">
            <span>{count:,} restaurants • {cities_count} localities</span>
            <span style="color: var(--border-subtle);">•</span>
            <span class="powered">🧠 Powered by Groq LLaMA 3 70B</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_welcome():
    """Render the welcome hero state (before first search)."""
    st.markdown("""
    <div class="welcome-hero">
        <div class="emojis">🍕 🍜 🍛 🥘</div>
        <h2>What are you craving today?</h2>
        <p>Fill in your preferences on the left and hit Recommend</p>
    </div>
    """, unsafe_allow_html=True)


def render_empty(location: str):
    """Render empty state when no results found."""
    st.markdown(f"""
    <div class="empty-state">
        <div class="emoji">🍽️</div>
        <h3>No restaurants found</h3>
        <p>No restaurants matched <strong>'{location}'</strong>. Try a different location or broaden your filters.</p>
    </div>
    """, unsafe_allow_html=True)


def render_results(response, preferences):
    """Render the full results panel."""
    # Summary banner
    summary_text = response.summary or ""
    st.markdown(f"""
    <div class="summary-banner">
        <p>"{summary_text}"</p>
    </div>
    """, unsafe_allow_html=True)

    # Relaxation alert
    if response.filters_relaxed:
        relaxed = ", ".join(response.filters_relaxed)
        st.markdown(f"""
        <div class="relax-alert">
            ⚠️ We relaxed <strong>{relaxed}</strong> filters to find more options for you
        </div>
        """, unsafe_allow_html=True)

    # Fallback notice
    if response.is_fallback:
        st.markdown("""
        <div class="fallback-notice">
            ℹ️ AI ranking unavailable — showing top-rated matches sorted by rating &amp; popularity
        </div>
        """, unsafe_allow_html=True)

    # Restaurant cards
    cards_html = ""
    for i, rec in enumerate(response.recommendations):
        cards_html += render_card(rec, i)

    # Streamlit's markdown parser often breaks if there are newlines between HTML blocks,
    # causing it to render raw text instead of actual HTML. Removing newlines fixes this.
    clean_html = cards_html.replace('\n', '')
    st.markdown(f'<div class="results-container">{clean_html}</div>', unsafe_allow_html=True)


def render_footer():
    """Render the app footer."""
    count = get_restaurant_count()
    st.markdown(f"""
    <div class="app-footer">
        <div class="brand">Zomato AI Recommender</div>
        <div class="meta">
            {count:,} restaurants • {len(get_cities())} localities • {len(get_cuisines())} cuisines<br/>
            Powered by Groq LLaMA 3 70B + Zomato Dataset
        </div>
    </div>
    """, unsafe_allow_html=True)


# ── Main App ────────────────────────────────────────────────────

def main():
    inject_css()

    # Sidebar
    submitted, location, budget, cuisine, min_rating, additional = render_sidebar()

    # Main content
    render_header()

    # State management
    if "results" not in st.session_state:
        st.session_state.results = None
        st.session_state.last_prefs = None

    if submitted:
        try:
            prefs = UserPreferences(
                location=location,
                budget=budget,
                cuisine=cuisine,
                min_rating=min_rating,
                additional_preferences=additional,
            )

            with st.spinner("Finding the best restaurants for you..."):
                service = get_service()
                t0 = time.perf_counter()
                response = service.recommend(prefs, target_count=5)
                elapsed = (time.perf_counter() - t0) * 1000

            st.session_state.results = response
            st.session_state.last_prefs = prefs
            logger.info(f"[UI] Results returned in {elapsed:.0f}ms")

        except ValueError as e:
            st.error(f"⚠️ Invalid input: {e}")
            st.session_state.results = None
        except Exception as e:
            st.error(f"❌ Something went wrong: {e}")
            logger.exception("Unexpected error in UI")
            st.session_state.results = None

    # Render content based on state
    if st.session_state.results is not None:
        response = st.session_state.results
        prefs = st.session_state.last_prefs

        if len(response.recommendations) == 0:
            render_empty(prefs.location if prefs else "Unknown")
        else:
            render_results(response, prefs)
    else:
        render_welcome()

    render_footer()


if __name__ == "__main__":
    main()
