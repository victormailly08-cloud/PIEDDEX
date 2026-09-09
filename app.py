import streamlit as st
import random
import os
import json
from datetime import datetime
from pathlib import Path

# ============================================================
# CONFIG
# ============================================================

st.set_page_config(
    page_title="PiedDex",
    page_icon="🦶",
    layout="wide",
    initial_sidebar_state="collapsed"
)

DATA_FOLDER = Path("pieddex_data")
PHOTOS_FOLDER = DATA_FOLDER / "photos"
DATABASE_FILE = DATA_FOLDER / "captures.json"

DATA_FOLDER.mkdir(exist_ok=True)
PHOTOS_FOLDER.mkdir(exist_ok=True)

if not DATABASE_FILE.exists():
    with open(DATABASE_FILE, "w", encoding="utf-8") as f:
        json.dump([], f)

# ============================================================
# STYLE SIMPLE ET FIABLE
# ============================================================

st.markdown("""
<style>
.block-container {
    padding-top: 0.5rem;
    padding-bottom: 8rem;
}

#MainMenu {
    visibility: hidden;
}

footer {
    visibility: hidden;
}

header {
    background: transparent;
}

.stButton > button {
    width: 100%;
    border-radius: 12px;
    font-weight: 700;
}

div[data-baseweb="tab-list"] {
    gap: 8px;
}

button[data-baseweb="tab"] {
    font-weight: 800;
}
</style>
""", unsafe_allow_html=True)

# ============================================================
# FONCTIONS
# ============================================================

def load_captures():
    try:
        with open(DATABASE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

def save_captures(captures):
    with open(DATABASE_FILE, "w", encoding="utf-8") as f:
        json.dump(captures, f, ensure_ascii=False, indent=4)

def generate_rarity():
    scores = [1,2,3,4,5,6,7,8,9,10]
    weights = [8,11,14,15,15,13,10,7,4,1]
    return random.choices(scores, weights=weights, k=1)[0]

def rarity_name(score):
    if score <= 3:
        return "COMMUN"
    elif score <= 5:
        return "PEU COMMUN"
    elif score <= 7:
        return "RARE"
    elif score == 8:
        return "ÉPIQUE"
    elif score == 9:
        return "LÉGENDAIRE"
    else:
        return "MYTHIQUE"

def rarity_emoji(score):
    if score <= 3:
        return "⚪"
    elif score <= 5:
        return "🟢"
    elif score <= 7:
        return "🔵"
    elif score == 8:
        return "🟣"
    elif score == 9:
        return "🟡"
    else:
        return "🔥"

def delete_capture(capture_id):
    captures = load_captures()

    target = next(
        (c for c in captures if c["id"] == capture_id),
        None
    )

    if target:
        photo_path = target.get("photo")

        if photo_path and os.path.exists(photo_path):
            try:
                os.remove(photo_path)
            except:
                pass

    captures = [
        c for c in captures
        if c["id"] != capture_id
    ]

    save_captures(captures)

# ============================================================
# DIALOGUE PHOTO
# ============================================================

@st.dialog("Fiche du spécimen")
def show_specimen(capture):

    if os.path.exists(capture["photo"]):
        st.image(
            capture["photo"],
            use_container_width=True
        )

    st.markdown(
        f"### #{capture['numero']:03d} — {capture['nom']}"
    )

    st.metric(
        "Rareté",
        f"{capture['score']}/10"
    )

    st.write(
        f"{rarity_emoji(capture['score'])} "
        f"**{capture['rarete']}**"
    )

    st.caption(
        f"Capturé le {capture['date']}"
    )

    st.divider()

    if st.button(
        "🗑️ Supprimer ce spécimen",
        key=f"delete_{capture['id']}",
        use_container_width=True
    ):
        delete_capture(capture["id"])
        st.rerun()

# ============================================================
# HEADER
# ============================================================

st.title("🦶 PIEDDEX")
st.caption("Collection personnelle de spécimens")

# ============================================================
# TABS
# ============================================================

tab_capture, tab_collection = st.tabs(
    ["📸 CAPTURER", "📚 MON PIEDDEX"]
)

# ============================================================
# CAPTURER
# ============================================================

with tab_capture:

    st.subheader("Scanner de spécimen")

    st.info(
        "Prends une photo du pied, donne-lui un nom puis lance l'analyse."
    )

    photo = st.camera_input(
        "📷 Prendre une photo"
    )

    if photo:

        st.image(
            photo,
            caption="Aperçu",
            use_container_width=True
        )

        nom = st.text_input(
            "Nom du spécimen",
            placeholder="Ex : Piedouille"
        )

        if st.button(
            "🔍 ANALYSER LE SPÉCIMEN",
            use_container_width=True
        ):

            if not nom.strip():

                st.warning(
                    "Entre d'abord le nom du spécimen."
                )

            else:

                score = generate_rarity()
                rarete = rarity_name(score)

                capture_id = datetime.now().strftime(
                    "%Y%m%d_%H%M%S_%f"
                )

                filepath = (
                    PHOTOS_FOLDER /
                    f"{capture_id}.jpg"
                )

                with open(filepath, "wb") as f:
                    f.write(photo.getbuffer())

                captures = load_captures()

                numero = max(
                    [c.get("numero", 0) for c in captures],
                    default=0
                ) + 1

                capture = {
                    "id": capture_id,
                    "numero": numero,
                    "nom": nom.strip(),
                    "score": score,
                    "rarete": rarete,
                    "photo": str(filepath),
                    "date": datetime.now().strftime(
                        "%d/%m/%Y à %H:%M"
                    )
                }

                captures.append(capture)
                save_captures(captures)

                st.success(
                    f"Nouveau spécimen : "
                    f"#{numero:03d} — {nom.upper()}"
                )

                col1, col2 = st.columns(2)

                with col1:
                    st.metric(
                        "Note",
                        f"{score}/10"
                    )

                with col2:
                    st.metric(
                        "Catégorie",
                        rarete
                    )

                st.write(
                    f"{rarity_emoji(score)} "
                    f"**{rarete}**"
                )

                if score >= 9:
                    st.balloons()

# ============================================================
# PIEDDEX
# ============================================================

with tab_collection:

    captures = load_captures()

    if not captures:

        st.info(
            "Ton PiedDex est vide pour le moment."
        )

    else:

        st.subheader("Ma collection")

        st.caption(
            f"{len(captures)} spécimen(s) découvert(s)"
        )

        sort_option = st.selectbox(
            "Trier",
            [
                "Plus récentes",
                "Plus anciennes",
                "Rareté décroissante",
                "Rareté croissante"
            ]
        )

        if sort_option == "Plus récentes":
            captures = captures[::-1]

        elif sort_option == "Rareté décroissante":
            captures = sorted(
                captures,
                key=lambda x: x["score"],
                reverse=True
            )

        elif sort_option == "Rareté croissante":
            captures = sorted(
                captures,
                key=lambda x: x["score"]
            )

        # 4 cartes par ligne
        for i in range(0, len(captures), 4):

            row = captures[i:i+4]

            cols = st.columns(4)

            for col, capture in zip(cols, row):

                with col:

                    if os.path.exists(capture["photo"]):
                        st.image(
                            capture["photo"],
                            use_container_width=True
                        )

                    st.caption(
                        f"#{capture['numero']:03d}"
                    )

                    st.markdown(
                        f"**{capture['nom']}**"
                    )

                    st.write(
                        f"{rarity_emoji(capture['score'])} "
                        f"{capture['score']}/10"
                    )

                    if st.button(
                        "Voir",
                        key=f"view_{capture['id']}",
                        use_container_width=True
                    ):
                        show_specimen(capture)
