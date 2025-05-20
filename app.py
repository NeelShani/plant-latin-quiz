import streamlit as st
from pptx import Presentation
from PIL import Image
import io
import random

st.set_page_config(page_title="Plant Latin Name Quiz", layout="wide")
st.title("Plant Quiz: Guess the Latin Name")
st.markdown("### Hello Anna! Welcome to this specialized app created just for you.")

# Session state init
for key in ("plants","quiz_order","subset","current_index","score","answered"):
    if key not in st.session_state:
        st.session_state[key] = [] if key=="plants" else 0

# PPTX upload
pptx_file = st.file_uploader("Upload PowerPoint (.pptx)", type=["pptx"])

def extract_plants(pptx_bytes):
    prs = Presentation(io.BytesIO(pptx_bytes))
    plants = []
    for slide in prs.slides:
        img = None
        text = ""
        # 1) find the picture (any shape with an .image)
        for shp in slide.shapes:
            if hasattr(shp, "image"):
                try:
                    blob = shp.image.blob
                    img = Image.open(io.BytesIO(blob))
                    break
                except Exception:
                    continue
        # 2) gather all text on the slide
        for shp in slide.shapes:
            if hasattr(shp, "text") and shp.text.strip():
                text += shp.text.strip() + "\n"
        # split first non-empty line by dash or comma into Czech/Latin
        lines = [ln for ln in text.splitlines() if ln.strip()]
        if img and lines:
            # assume first line is "Czech – Latin"
            parts = [p.strip() for p in lines[0].replace("–",",").split(",") if p.strip()]
            if len(parts) >= 2:
                plants.append((img, parts[0], parts[1]))
    return plants

if pptx_file:
    plants = extract_plants(pptx_file.read())
    if not plants:
        st.error("No images + names found—please check your slides contain one picture and one text box each.")
    else:
        st.session_state.plants = plants
        total = len(plants)
        start, end = st.slider("Choose plant range:", 1, total, (1, total))
        if st.button("Start Quiz"):
            subset = plants[start-1:end]
            st.session_state.subset = subset
            st.session_state.quiz_order = list(range(len(subset)))
            random.shuffle(st.session_state.quiz_order)
            st.session_state.current_index = 0
            st.session_state.score = 0
            st.session_state.answered = 0
            st.experimental_rerun()

# Quiz loop
if st.session_state.quiz_order:
    idx = st.session_state.quiz_order[st.session_state.current_index]
    img, czech, latin = st.session_state.subset[idx]

    st.image(img, use_column_width=True)
    st.subheader("Guess the **Latin name** of this plant:")
    guess = st.text_input("Your guess:", key="guess_input")

    if st.button("Submit"):
        st.markdown(f"**Czech name:** {czech}")
        st.markdown(f"**Latin name:** {latin}")

        st.session_state.answered += 1
        if guess.strip().lower() == latin.lower():
            st.success("✅ Correct!")
            st.session_state.score += 1
        else:
            st.error("❌ Incorrect.")

        if st.session_state.current_index < len(st.session_state.quiz_order) - 1:
            if st.button("Next"):
                st.session_state.current_index += 1
                st.experimental_rerun()
        else:
            st.balloons()
            st.success("### Quiz Complete!")
            st.markdown(f"**Final Score:** {st.session_state.score} / {st.session_state.answered}")
            st.markdown("### Good luck for the exam — you can do it!❤️")