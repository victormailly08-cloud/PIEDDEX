import streamlit as st

st.set_page_config(
    page_title="PiedDex",
    page_icon="🦶",
    layout="centered"
)

st.title("🔴 PIEDDEX")

st.write("Bienvenue dans ton PiedDex !")

photo = st.camera_input("📸 Capturer un spécimen")

if photo:
    st.image(photo)

    nom = st.text_input("Nom du spécimen")

    if st.button("🔍 ANALYSER"):
        st.success(f"🦶 {nom} a été découvert !")
