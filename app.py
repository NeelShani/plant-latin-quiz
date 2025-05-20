import streamlit as st
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE
from PIL import Image
import io
import random

# ——— Page config & welcome ——————————————————————————
st.set_page_config(page_title="Plant Name Memory Quiz", layout="wide")
st.title("Plant Quiz")
st.markdown("### Hello Anna! Welcome to this specialized app created just for you.")

# ——— Session‐state defaults —————————————————————————
if "plants" not in st.session_state:
    st.session_state.plants = []
if "subset" not in st.session_state:
    st.session_state.subset = []
if "remaining" not in st.session_state:
    st.session_state.remaining = []
if "current_slide" not in st.session_state:
    st.session_state.current_slide = None
if "revealed" not in st.session_state:
    st.session_state.revealed = False

# ——— Upload & extract —————————————————————————————
pptx_file = st.file_uploader("Upload your PowerPoint (.pptx)", type=["pptx"])

def extract_slides(pptx_bytes):
    prs = Presentation(io.BytesIO(pptx_bytes))
    slides = []
    for slide in prs.slides:
        # grab first image
        img = None
        for shp in slide.shapes:
            if shp.shape_type in (MSO_SHAPE_TYPE.PICTURE, MSO_SHAPE_TYPE.PLACEHOLDER):
                try:
                    img = Image.open(io.BytesIO(shp.image.blob))
                    break
                except Exception:
                    pass
        # collect all text
        lines = [
            shp.text.strip()
            for shp in slide.shapes
            if hasattr(shp, "text") and shp.text.strip()
        ]
        if img and lines:
            slides.append((img, "\n".join(lines)))
    return slides

if pptx_file:
    st.session_state.plants = extract_slides(pptx_file.read())
    n = len(st.session_state.plants)
    if n == 0:
        st.error("❌ No valid slides found. Each slide needs one image + ≥1 text box.")
        st.stop()
    st.success(f"✓ Loaded {n} slides.")

    # choose whether to quiz all or a sub-range
    quiz_all = st.checkbox("Quiz **all** slides (ignore range)", value=True)
    if not quiz_all:
        start, end = st.slider("Select slide-range to quiz:", 1, n, (1, n))
    else:
        start, end = 1, n

    if st.button("Start Quiz"):
        # slice out the subset and reset state
        st.session_state.subset = st.session_state.plants[start-1:end]
        # initialize remaining indices
        st.session_state.remaining = list(range(len(st.session_state.subset)))
        random.shuffle(st.session_state.remaining)
        st.session_state.current_slide = None
        st.session_state.revealed = False
        st.experimental_rerun()

# ——— Quiz loop —————————————————————————————————————
if st.session_state.remaining:
    # if we need to pick a new slide
    if st.session_state.current_slide is None:
        st.session_state.current_slide = st.session_state.remaining.pop()
    img, text = st.session_state.subset[st.session_state.current_slide]

    st.image(img, use_column_width=True)
    st.text_input("Your guess (optional):", key="guess_input")

    # action buttons
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Reveal Answer"):
            st.session_state.revealed = True
    with c2:
        if st.button("Next"):
            st.session_state.current_slide = None
            st.session_state.revealed = False
            st.experimental_rerun()

    if st.session_state.revealed:
        st.markdown("**Answer (all text on slide):**")
        st.write(text)

elif st.session_state.subset:
    # no remaining slides
    st.info("✅ You've seen **all** slides in this range!")
    if st.button("Restart Quiz"):
        # re-initialize the deck
        st.session_state.remaining = list(range(len(st.session_state.subset)))
        random.shuffle(st.session_state.remaining)
        st.session_state.current_slide = None
        st.session_state.revealed = False
        st.experimental_rerun()

    
st.markdown("### Good luck for the exam — you can do it!❤️")