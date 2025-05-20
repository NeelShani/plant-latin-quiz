import streamlit as st
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE
from PIL import Image
import io, random

st.set_page_config(page_title="Plant Name Memory Quiz", layout="wide")
st.title("Plant Quiz")
st.markdown("### Hello Anna! Welcome to this specialized app created just for you.")

# ─── Session-state defaults ─────────────────────────────────────
session_defaults = {
    "plants":     [],   # list of (PIL.Image, full_text)
    "subset":     [],   # filtered range
    "remaining":  [],   # indices yet to show
    "current":    None, # the index we're showing now
    "revealed":   False,
}
for k, v in session_defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ─── Helpers ────────────────────────────────────────────────────
def extract_slides(pptx_bytes):
    prs = Presentation(io.BytesIO(pptx_bytes))
    slides = []
    for slide in prs.slides:
        # 1) find first image or placeholder-with-image
        img = None
        for shp in slide.shapes:
            if shp.shape_type in (MSO_SHAPE_TYPE.PICTURE, MSO_SHAPE_TYPE.PLACEHOLDER):
                try:
                    blob = shp.image.blob
                    img = Image.open(io.BytesIO(blob))
                    break
                except Exception:
                    pass
        # 2) gather every non-empty text box
        lines = [
            shp.text.strip()
            for shp in slide.shapes
            if hasattr(shp, "text") and shp.text.strip()
        ]
        if img and lines:
            full = "\n".join(lines)
            slides.append((img, full))
    return slides

def start_quiz():
    # slice out the chosen subset
    quiz_all = st.session_state.quiz_all
    n = len(st.session_state.plants)
    if quiz_all:
        s, e = 1, n
    else:
        s, e = st.session_state.range_start, st.session_state.range_end

    sub = st.session_state.plants[s-1 : e]
    st.session_state.subset = sub
    st.session_state.remaining = list(range(len(sub)))
    random.shuffle(st.session_state.remaining)
    st.session_state.current = None
    st.session_state.revealed = False

def next_slide():
    st.session_state.current = None
    st.session_state.revealed = False

def restart_quiz():
    st.session_state.remaining = list(range(len(st.session_state.subset)))
    random.shuffle(st.session_state.remaining)
    st.session_state.current = None
    st.session_state.revealed = False

# ─── Upload & Setup ─────────────────────────────────────────────
pptx_file = st.file_uploader("Upload your PowerPoint (.pptx)", type=["pptx"])
if pptx_file:
    st.session_state.plants = extract_slides(pptx_file.read())
    total = len(st.session_state.plants)
    if total == 0:
        st.error("❌ No valid slides found. Make sure each slide has exactly one image + at least one text box.")
        st.stop()
    st.success(f"✓ Loaded {total} slides.")

    # All-slides vs Range
    st.session_state.quiz_all = st.checkbox("Quiz **all** slides (ignore range)", value=True)
    if not st.session_state.quiz_all:
        st.session_state.range_start, st.session_state.range_end = st.slider(
            "Select slide‐range to quiz:",
            1, total,
            (1, total)
        )

    st.button("Start Quiz", on_click=start_quiz)

# ─── Quiz Loop ───────────────────────────────────────────────────
if st.session_state.remaining:
    # pick a slide if we don't have one yet
    if st.session_state.current is None:
        st.session_state.current = st.session_state.remaining.pop()
    img, text = st.session_state.subset[st.session_state.current]

    st.image(img, use_raw_width=True, use_column_width=True)
    st.text_input("Your guess (optional):", key="guess_input")

    # Reveal / Next
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Reveal Answer"):
            st.session_state.revealed = True
    with col2:
        if st.button("Next", on_click=next_slide):
            pass

    if st.session_state.revealed:
        st.markdown("**Answer (all text on slide):**")
        st.write(text)

elif st.session_state.subset:
    st.info("✅ You've seen **all** slides in this range!")
    st.button("Restart Quiz", on_click=restart_quiz)

st.markdown("### Good luck for the exam — you can do it! ❤️")
