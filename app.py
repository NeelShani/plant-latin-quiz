import streamlit as st
from pptx import Presentation
from PIL import Image
import io
import random

st.set_page_config(page_title="Plant Latin Name Quiz", layout="wide")

# Welcome message
st.title("Plant Quiz: Guess the Latin Name")
st.markdown("### Hello Anna! Welcome to this specialized app created just for you.")

# Initialize session state
for key in ["plants", "quiz_order", "current_index", "score", "total", "answered"]:
    if key not in st.session_state:
        st.session_state[key] = None if key == "plants" else 0

# Upload PowerPoint
pptx_file = st.file_uploader("Upload PowerPoint (.pptx)", type=["pptx"])

def extract_plants(pptx_bytes):
    prs = Presentation(io.BytesIO(pptx_bytes))
    extracted = []
    for slide in prs.slides:
        image = None
        text = ""
        for shape in slide.shapes:
            if shape.shape_type == 13:  # picture
                image_stream = shape.image.blob
                image = Image.open(io.BytesIO(image_stream))
            elif hasattr(shape, "text"):
                text += shape.text + " "
        parts = text.strip().replace("\n", ",").split(",")
        if image and len(parts) >= 2:
            czech = parts[0].strip()
            latin = parts[1].strip()
            extracted.append((image, czech, latin))
    return extracted

if pptx_file:
    st.session_state.plants = extract_plants(pptx_file.read())

    if not st.session_state.plants:
        st.warning("No valid slides found.")
    else:
        total = len(st.session_state.plants)
        range_start, range_end = st.slider("Choose plant range:", 1, total, (1, total))

        if st.button("Start Quiz"):
            subset = st.session_state.plants[range_start - 1 : range_end]
            st.session_state.quiz_order = list(range(len(subset)))
            random.shuffle(st.session_state.quiz_order)
            st.session_state.subset = subset
            st.session_state.current_index = 0
            st.session_state.score = 0
            st.session_state.answered = 0
            st.experimental_rerun()

if st.session_state.quiz_order:
    idx = st.session_state.quiz_order[st.session_state.current_index]
    plant_image, czech_name, latin_name = st.session_state.subset[idx]

    st.image(plant_image, use_column_width=True)
    st.subheader("Guess the **Latin name** of this plant:")
    user_guess = st.text_input("Your guess:", key="guess_input")

    if st.button("Submit"):
        st.markdown(f"**Czech name:** {czech_name}")
        st.markdown(f"**Latin name:** {latin_name}")

        st.session_state.answered += 1
        if user_guess.strip().lower() == latin_name.lower():
            st.success("Correct!")
            st.session_state.score += 1
        else:
            st.error("Incorrect.")

        if st.session_state.current_index < len(st.session_state.quiz_order) - 1:
            if st.button("Next"):
                st.session_state.current_index += 1
                st.experimental_rerun()
        else:
            st.success("Quiz Complete!")
            st.markdown(f"### Final Score: {st.session_state.score} / {st.session_state.answered}")
            st.balloons()
            st.markdown("### Good luck for the exam — you can do it!❤️")

