import streamlit as st
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE
from pptx.enum.fill import MSO_FILL
from PIL import Image
import io
import random

# ——— Helpers ————————————————————————————————————————————
def _find_image_blob(shape):
    """
    Recursively search this shape (or group) for any .image.blob.
    Returns raw blob bytes or None.
    """
    # top-level picture/placeholder
    if hasattr(shape, "image"):
        try:
            return shape.image.blob
        except Exception:
            pass
    # group shape: dive in
    if shape.shape_type == MSO_SHAPE_TYPE.GROUP:
        for shp in shape.shapes:
            blob = _find_image_blob(shp)
            if blob:
                return blob
    return None

def extract_slides(pptx_bytes):
    prs = Presentation(io.BytesIO(pptx_bytes))
    slides = []
    for slide in prs.slides:
        # 1) try every shape (and sub-shape) for an image blob
        img_blob = None
        for shape in slide.shapes:
            img_blob = _find_image_blob(shape)
            if img_blob:
                break

        # 2) if still none, check slide background fill
        if not img_blob:
            fill = slide.background.fill
            if fill.type == MSO_FILL.PICTURE and hasattr(fill.picture, "image"):
                img_blob = fill.picture.image.blob

        # skip slides with no image
        if not img_blob:
            continue

        # 3) load PIL image
        try:
            image = Image.open(io.BytesIO(img_blob))
        except Exception:
            continue

        # 4) gather *all* text (including in groups)
        texts = []
        def _gather_text(shp):
            if hasattr(shp, "text") and shp.text.strip():
                texts.append(shp.text.strip())
            if shp.shape_type == MSO_SHAPE_TYPE.GROUP:
                for s in shp.shapes:
                    _gather_text(s)

        for shape in slide.shapes:
            _gather_text(shape)

        if not texts:
            continue

        full_text = "\n".join(texts)
        slides.append((image, full_text))

    return slides

# ——— Streamlit UI ——————————————————————————————————————
st.set_page_config(page_title="Plant Name Memory Quiz", layout="wide")
st.title("Plant Quiz")
st.markdown("### Hello Anna! Welcome to this specialized app created just for you.")

# session state
if "plants" not in st.session_state:
    st.session_state.plants = []
if "subset" not in st.session_state:
    st.session_state.subset = []
if "remaining" not in st.session_state:
    st.session_state.remaining = []
if "current" not in st.session_state:
    st.session_state.current = None
if "revealed" not in st.session_state:
    st.session_state.revealed = False

pptx_file = st.file_uploader("Upload your PowerPoint (.pptx)", type=["pptx"])
if pptx_file:
    st.session_state.plants = extract_slides(pptx_file.read())
    total = len(st.session_state.plants)
    if total == 0:
        st.error("❌ No slides with both image & text found.")
        st.stop()
    st.success(f"✓ Loaded {total} slides.")

    quiz_all = st.checkbox("Quiz **all** slides", value=True)
    if not quiz_all:
        start, end = st.slider("Select slide range:", 1, total, (1, total))
    else:
        start, end = 1, total

    if st.button("Start Quiz"):
        st.session_state.subset = st.session_state.plants[start-1:end]
        st.session_state.remaining = list(range(len(st.session_state.subset)))
        random.shuffle(st.session_state.remaining)
        st.session_state.current = None
        st.session_state.revealed = False
        st.experimental_rerun()

# quiz loop
if st.session_state.remaining:
    if st.session_state.current is None:
        st.session_state.current = st.session_state.remaining.pop()
    img, text = st.session_state.subset[st.session_state.current]

    st.image(img, use_column_width=True)
    st.text_input("Your guess (optional):", key="guess")

    c1, c2 = st.columns(2)
    with c1:
        if st.button("Reveal Answer"):
            st.session_state.revealed = True
    with c2:
        if st.button("Next"):
            st.session_state.current = None
            st.session_state.revealed = False
            st.experimental_rerun()

    if st.session_state.revealed:
        st.markdown("**Answer (all text on slide):**")
        st.write(text)

elif st.session_state.subset:
    st.info("✅ You’ve seen all slides in this range!")
    if st.button("Restart Quiz"):
        st.session_state.remaining = list(range(len(st.session_state.subset)))
        random.shuffle(st.session_state.remaining)
        st.session_state.current = None
        st.session_state.revealed = False
        st.experimental_rerun()


    
st.markdown("### Good luck for the exam — you can do it!❤️")