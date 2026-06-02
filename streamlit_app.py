"""
streamlit_app.py  —  Jewellery Hybrid Search UI
Run:  streamlit run streamlit_app.py
Expects the FastAPI backend at API_URL env var (default: http://localhost:8000)
"""

import io
import os
import json
import requests
import streamlit as st
from PIL import Image

#  Config 
# Reads API_URL from environment so it works both locally and inside Docker
API_BASE = os.getenv("API_URL", "http://localhost:8000")

SCRIPT_DIR    = os.path.dirname(os.path.abspath(__file__))
METADATA_PATH = os.path.join(SCRIPT_DIR, "data", "metadata_cleaned.json")

#  Page setup 
st.set_page_config(
    page_title="Jewellery Search",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="expanded",
)

#  Custom CSS 
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,600;1,300;1,400&family=DM+Sans:wght@300;400;500&display=swap');

html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }

.stApp { background-color: #0f0d0b; color: #e8ddd0; }

[data-testid="stSidebar"] {
    background-color: #161210;
    border-right: 1px solid #2a2420;
}
[data-testid="stSidebar"] * { color: #c8b9a8 !important; }

h1, h2, h3 {
    font-family: 'Cormorant Garamond', serif !important;
    font-weight: 300 !important;
    letter-spacing: 0.05em;
}

.main-title {
    font-family: 'Cormorant Garamond', serif;
    font-size: 3.2rem;
    font-weight: 300;
    letter-spacing: 0.15em;
    color: #e8ddd0;
    text-align: center;
    margin-bottom: 0.1rem;
    line-height: 1.1;
}
.main-subtitle {
    font-family: 'DM Sans', sans-serif;
    font-size: 0.75rem;
    letter-spacing: 0.35em;
    text-transform: uppercase;
    color: #8a7060;
    text-align: center;
    margin-bottom: 2rem;
}

.gold-divider {
    height: 1px;
    background: linear-gradient(90deg, transparent, #c9a96e, transparent);
    margin: 1.5rem 0;
}

.score-badge {
    display: inline-block;
    background: #c9a96e22;
    border: 1px solid #c9a96e55;
    color: #c9a96e;
    font-size: 0.7rem;
    letter-spacing: 0.1em;
    padding: 2px 8px;
    border-radius: 2px;
    font-family: 'DM Sans', sans-serif;
}

.tag {
    display: inline-block;
    background: #ffffff08;
    color: #8a7060;
    font-size: 0.65rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    padding: 2px 7px;
    border-radius: 2px;
    margin-right: 4px;
}

.stTextInput > div > div > input,
.stSelectbox > div > div {
    background-color: #1a1612 !important;
    border-color: #2a2420 !important;
    color: #e8ddd0 !important;
}

.stButton > button {
    background: linear-gradient(135deg, #c9a96e, #a07840);
    color: #0f0d0b;
    font-family: 'DM Sans', sans-serif;
    font-size: 0.75rem;
    font-weight: 500;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    border: none;
    border-radius: 2px;
    padding: 0.6rem 2rem;
    width: 100%;
    transition: opacity 0.2s;
}
.stButton > button:hover { opacity: 0.85; border: none; }

.stTabs [data-baseweb="tab-list"] {
    background-color: transparent;
    border-bottom: 1px solid #2a2420;
    gap: 0;
}
.stTabs [data-baseweb="tab"] {
    font-family: 'DM Sans', sans-serif;
    font-size: 0.72rem;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: #5a4a3a !important;
    background: transparent;
    border-bottom: 2px solid transparent;
    padding: 0.6rem 1.5rem;
}
.stTabs [aria-selected="true"] {
    color: #c9a96e !important;
    border-bottom: 2px solid #c9a96e;
    background: transparent;
}

.metric-box {
    background: #1a1612;
    border: 1px solid #2a2420;
    border-radius: 4px;
    padding: 1rem;
    text-align: center;
}
.metric-value {
    font-family: 'Cormorant Garamond', serif;
    font-size: 2rem;
    font-weight: 300;
    color: #c9a96e;
}
.metric-label {
    font-size: 0.65rem;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: #5a4a3a;
}

.no-img {
    background: #1a1612;
    border: 1px dashed #2a2420;
    border-radius: 4px;
    height: 140px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #3a2a1a;
    font-size: 1.5rem;
}

[data-testid="stFileUploader"] {
    background: #1a1612;
    border: 1px dashed #3a3028;
    border-radius: 4px;
    padding: 1rem;
}

.stAlert {
    background: #1a1612 !important;
    border-color: #2a2420 !important;
    color: #8a7060 !important;
}

.rank-num {
    font-family: 'Cormorant Garamond', serif;
    font-size: 1.4rem;
    font-weight: 300;
    color: #3a2a1a;
    line-height: 1;
}

.pagination-info {
    font-family: 'DM Sans', sans-serif;
    font-size: 0.7rem;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: #8a7060;
    text-align: center;
    margin: 0.5rem 0;
}
</style>
""", unsafe_allow_html=True)


#  Load metadata lookup 

@st.cache_data
def load_metadata_lookup(path: str) -> dict:
    """Build a dict: filename -> normalised filepath."""
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        records = json.load(f)
    lookup = {}
    for rec in records:
        fname = rec.get("filename", "")
        fpath = rec.get("filepath", "").replace("\\", os.sep)
        if fname:
            lookup[fname] = fpath
    return lookup

METADATA_LOOKUP = load_metadata_lookup(METADATA_PATH)


#  Helpers

def check_api_health(base_url: str) -> bool:
    """Return True if the API /health endpoint responds OK."""
    try:
        r = requests.get(f"{base_url}/health", timeout=5)
        return r.status_code == 200
    except Exception:
        return False


def search_unified(base_url: str, query=None, pil_img=None, top_k=10, page=1, page_size=20, category=None):
    """Call POST /search-image — the single hybrid endpoint."""
    data  = {"top_k": top_k, "page": page, "page_size": page_size}
    files = {}
    if query:
        data["query"] = query
    if category:
        data["category"] = category
    if pil_img is not None:
        buf = io.BytesIO()
        pil_img.save(buf, format="JPEG")
        buf.seek(0)
        files["file"] = ("query.jpg", buf, "image/jpeg")
    r = requests.post(
        f"{base_url}/search-image",
        data=data,
        files=files or None,
        timeout=60,
    )
    r.raise_for_status()
    return r.json()


def resolve_image_path(payload: dict):
    """
    Try multiple strategies to find the actual image path on disk.
    All relative paths are resolved against SCRIPT_DIR.
    """
    def _abs(p: str) -> str:
        p = p.replace("\\", os.sep)
        return p if os.path.isabs(p) else os.path.join(SCRIPT_DIR, p)

    # Strategy 1: filepath directly in payload
    fp = payload.get("filepath", "")
    if fp:
        for candidate in [fp, _abs(fp)]:
            if os.path.exists(candidate.replace("\\", os.sep)):
                return candidate

    # Strategy 2: look up filename in metadata JSON
    fname = payload.get("filename", "")
    if fname and fname in METADATA_LOOKUP:
        fp2 = METADATA_LOOKUP[fname]
        for candidate in [fp2, _abs(fp2)]:
            if os.path.exists(candidate):
                return candidate

    # Strategy 3: construct path from category + filename
    if fname:
        cat = payload.get("category", "")
        for rel in [
            os.path.join("data", "images", cat, fname),
            os.path.join("data", "images", fname),
            fname,
        ]:
            for candidate in [rel, _abs(rel)]:
                if os.path.exists(candidate):
                    return candidate

    return None


def load_result_image(payload: dict):
    """Resolve and open a PIL image from a result payload."""
    path = resolve_image_path(payload)
    if path:
        try:
            return Image.open(path).convert("RGB")
        except Exception:
            pass
    return None


def deduplicate_results(results: list) -> list:
    """
    Remove results that point to the same image.
    Keeps highest-scoring result; re-ranks survivors from 1.
    """
    seen_paths     = set()
    seen_filenames = set()
    unique         = []

    for item in results:
        payload  = item.get("payload") or {}
        fname    = payload.get("filename", "")
        resolved = resolve_image_path(payload) or ""

        if resolved and resolved in seen_paths:
            continue
        if fname and fname in seen_filenames:
            continue

        if resolved:
            seen_paths.add(resolved)
        if fname:
            seen_filenames.add(fname)

        unique.append(item)

    for i, item in enumerate(unique):
        item["rank"] = i + 1

    return unique


def render_results(results: list):
    if not results:
        st.markdown(
            '<div style="text-align:center;color:#5a4a3a;padding:3rem;font-size:0.8rem;'
            'letter-spacing:0.2em;text-transform:uppercase;">No results found</div>',
            unsafe_allow_html=True,
        )
        return

    cols_per_row = 4
    for row_start in range(0, len(results), cols_per_row):
        row_results = results[row_start: row_start + cols_per_row]
        cols = st.columns(cols_per_row)
        for col, item in zip(cols, row_results):
            with col:
                payload = item.get("payload") or {}

                img = load_result_image(payload)
                if img:
                    st.image(img, use_container_width=True)
                else:
                    st.markdown('<div class="no-img">💎</div>', unsafe_allow_html=True)

                score_pct = (
                    f"{item['score'] * 100:.2f}%"
                    if item["score"] < 2
                    else f"{item['score']:.4f}"
                )
                def _as_str(val, default="—") -> str:
                    if isinstance(val, list):
                        return ", ".join(str(v) for v in val) if val else default
                    return str(val) if val else default

                cat   = _as_str(payload.get("category")).title()
                metal = _as_str(payload.get("metal")).title()
                fname = payload.get("filename", str(item.get("id", "")))

                st.markdown(f"""
                <div style="margin-top:0.4rem;">
                  <span class="rank-num">#{item['rank']}</span>
                  <span class="score-badge" style="float:right;">{score_pct}</span>
                  <br>
                  <span class="tag">{cat}</span>
                  <span class="tag">{metal}</span>
                  <div style="font-size:0.6rem;color:#3a2a1a;margin-top:0.3rem;
                              word-break:break-all;">{fname}</div>
                </div>
                """, unsafe_allow_html=True)


#  Sidebar 

with st.sidebar:
    st.markdown("### 💎 Settings")
    st.markdown('<div class="gold-divider"></div>', unsafe_allow_html=True)

    # Allow the user to override the API URL at runtime
    api_url   = st.text_input("API Base URL", value=API_BASE)
    top_k     = st.slider("Results to return (total)", min_value=5, max_value=500, value=20, step=5)
    page_size = st.select_slider("Results per page", options=[10, 20, 40, 60, 100], value=20)

    st.markdown('<div class="gold-divider"></div>', unsafe_allow_html=True)
    st.markdown("### 🏷️ Filter by Category")
    category_options = ["All", "ring", "earring", "bracelet", "necklace", "pendant"]
    category_filter = st.selectbox(
        "Category",
        options=category_options,
        index=0,
        label_visibility="collapsed",
    )
    selected_category = None if category_filter == "All" else category_filter

    st.markdown('<div class="gold-divider"></div>', unsafe_allow_html=True)

    n = len(METADATA_LOOKUP)
    st.markdown(
        f'<div class="metric-box">'
        f'<div class="metric-value">{n:,}</div>'
        f'<div class="metric-label">Images in metadata</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    #  Live API status 
    is_connected  = check_api_health(api_url)
    status_color  = "#4caf50" if is_connected else "#e57373"
    status_label  = "● API CONNECTED" if is_connected else "● API UNREACHABLE"
    st.markdown(
        f'<div style="text-align:center;margin-top:0.5rem;font-size:0.65rem;'
        f'letter-spacing:0.2em;color:{status_color};">{status_label}</div>',
        unsafe_allow_html=True,
    )
    if not is_connected:
        st.warning(f"Cannot reach {api_url}. Make sure the FastAPI server is running.")

    #  Debug panel 
    st.markdown('<div class="gold-divider"></div>', unsafe_allow_html=True)
    with st.expander("🔍 Path Debug"):
        st.markdown(f"**Script dir:** `{SCRIPT_DIR}`")
        st.markdown(f"**Metadata path:** `{METADATA_PATH}`")
        st.markdown(f"**Metadata exists:** `{os.path.exists(METADATA_PATH)}`")
        img_dir = os.path.join(SCRIPT_DIR, "data", "images")
        st.markdown(f"**Images dir exists:** `{os.path.exists(img_dir)}`")
        if os.path.exists(img_dir):
            subdirs = [d for d in os.listdir(img_dir)
                       if os.path.isdir(os.path.join(img_dir, d))]
            st.markdown(f"**Subdirs:** {subdirs[:10]}")
        if METADATA_LOOKUP:
            sample_fname, sample_path = next(iter(METADATA_LOOKUP.items()))
            abs_sample = sample_path if os.path.isabs(sample_path) \
                else os.path.join(SCRIPT_DIR, sample_path)
            st.markdown(f"**Sample entry:** `{sample_fname}`")
            st.markdown(f"**Stored path:** `{sample_path}`")
            st.markdown(f"**Exists (as-is):** `{os.path.exists(sample_path)}`")
            st.markdown(f"**Exists (abs):** `{os.path.exists(abs_sample)}`")


#  Main 

st.markdown('<div class="main-title">Jewellery Search</div>', unsafe_allow_html=True)
st.markdown('<div class="main-subtitle">Semantic · Visual · Hybrid</div>', unsafe_allow_html=True)
st.markdown('<div class="gold-divider"></div>', unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

#  Search inputs 
col_input, col_btn = st.columns([5, 1])
with col_input:
    query = st.text_input(
        label="query",
        placeholder='e.g. "rose gold ring"  (optional when uploading an image)',
        label_visibility="collapsed",
    )
with col_btn:
    do_search = st.button("Search", key="search_btn")

st.markdown(
    '<div style="font-size:0.65rem;letter-spacing:0.15em;color:#5a4a3a;margin-bottom:1rem;">'
    'TRY: &nbsp; rose gold ring &nbsp;·&nbsp; pearl bracelet &nbsp;·&nbsp; diamond earring'
    '</div>',
    unsafe_allow_html=True,
)

uploaded = st.file_uploader(
    "Upload a reference image (optional — combine with text for hybrid search)",
    type=["jpg", "jpeg", "png", "webp"],
    label_visibility="visible",
)

pil_img = None
if uploaded:
    pil_img = Image.open(uploaded).convert("RGB")
    col_prev, col_info = st.columns([1, 3])
    with col_prev:
        st.image(pil_img, caption="Reference image", use_container_width=True)
    with col_info:
        mode_hint = "hybrid (text + image)" if query.strip() else "image"
        st.markdown(f"""
        <div style="padding:0.5rem 1rem;">
          <div style="font-size:0.65rem;letter-spacing:0.2em;text-transform:uppercase;
                      color:#5a4a3a;margin-bottom:0.3rem;">Reference image</div>
          <div style="font-size:0.9rem;color:#e8ddd0;">{uploaded.name}</div>
          <div style="font-size:0.7rem;color:#5a4a3a;margin-top:0.2rem;">
              {pil_img.width} × {pil_img.height} px</div>
          <div style="font-size:0.65rem;color:#c9a96e;margin-top:0.5rem;
                      letter-spacing:0.1em;">Mode: {mode_hint}</div>
        </div>
        """, unsafe_allow_html=True)

# Run search 
if do_search:
    has_text  = bool(query and query.strip())
    has_image = pil_img is not None

    if not has_text and not has_image:
        st.warning("Please enter a search query or upload an image.")
    elif not check_api_health(api_url):
        st.error(f"Cannot reach API at {api_url}. Is the FastAPI server running?")
    else:
        # Reset to page 1 on a new search
        st.session_state["current_page"]  = 1
        st.session_state["search_query"]  = query.strip() if has_text else None
        st.session_state["search_img"]    = pil_img
        st.session_state["search_top_k"]  = top_k
        st.session_state["page_size"]     = page_size
        st.session_state["api_url"]       = api_url
        st.session_state["category"]      = selected_category
        st.session_state["search_ran"]    = True

# Display results if a search has been run
if st.session_state.get("search_ran"):
    current_page   = st.session_state.get("current_page", 1)
    saved_query    = st.session_state.get("search_query")
    saved_img      = st.session_state.get("search_img")
    saved_top_k    = st.session_state.get("search_top_k", top_k)
    saved_ps       = st.session_state.get("page_size", page_size)
    saved_api_url  = st.session_state.get("api_url", api_url)
    saved_category = st.session_state.get("category")

    with st.spinner("Searching…"):
        try:
            data = search_unified(
                base_url=saved_api_url,
                query=saved_query,
                pil_img=saved_img,
                top_k=saved_top_k,
                page=current_page,
                page_size=saved_ps,
                category=saved_category,
            )
            results      = data.get("results", [])
            mode         = data.get("mode", "—").title()
            total        = data.get("total", len(results))
            total_pages  = data.get("total_pages", 1)
            resp_page    = data.get("page", current_page)

            deduped = deduplicate_results(results)
            removed = len(results) - len(deduped)

            c1, c2, c3 = st.columns(3)
            label = f"Total results"
            c1.markdown(
                f'<div class="metric-box"><div class="metric-value">{total}</div>'
                f'<div class="metric-label">{label}</div></div>',
                unsafe_allow_html=True,
            )
            c2.markdown(
                f'<div class="metric-box"><div class="metric-value">{mode}</div>'
                f'<div class="metric-label">Search mode</div></div>',
                unsafe_allow_html=True,
            )
            img_name = data.get("image_filename") or "—"
            c3.markdown(
                f'<div class="metric-box">'
                f'<div class="metric-value" style="font-size:1rem;padding-top:0.4rem;">'
                f'{img_name}</div>'
                f'<div class="metric-label">Image</div></div>',
                unsafe_allow_html=True,
            )

            st.markdown('<div class="gold-divider"></div>', unsafe_allow_html=True)

            # Pagination info
            st.markdown(
                f'<div class="pagination-info">'
                f'Page {resp_page} of {total_pages} &nbsp;·&nbsp; '
                f'Showing {len(deduped)} items'
                f'{"  (" + str(removed) + " dupes removed)" if removed else ""}'
                f'</div>',
                unsafe_allow_html=True,
            )

            render_results(deduped)

            # Pagination controls
            st.markdown('<div class="gold-divider"></div>', unsafe_allow_html=True)
            pcol1, pcol2, pcol3 = st.columns([2, 3, 2])

            with pcol1:
                if current_page > 1:
                    if st.button("← Previous", key="prev_page"):
                        st.session_state["current_page"] = current_page - 1
                        st.rerun()

            with pcol2:
                st.markdown(
                    f'<div class="pagination-info" style="margin-top:0.6rem;">'
                    f'Page {resp_page} / {total_pages}</div>',
                    unsafe_allow_html=True,
                )

            with pcol3:
                if current_page < total_pages:
                    if st.button("Next →", key="next_page"):
                        st.session_state["current_page"] = current_page + 1
                        st.rerun()

        except requests.exceptions.ConnectionError:
            st.error(f"Cannot reach API at {api_url}. Is the FastAPI server running?")
        except Exception as e:
            st.error(f"Error: {e}")