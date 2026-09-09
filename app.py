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
# STYLE
# ============================================================

st.markdown("""
<style>

/* ---------------------------------------------------------
   GLOBAL
--------------------------------------------------------- */

html, body {
    overscroll-behavior-y: auto !important;
    touch-action: pan-y !important;
}

[data-testid="stAppViewContainer"] {
    overflow-y: auto !important;
    -webkit-overflow-scrolling: touch !important;
}

.block-container {
    padding-top: 0.5rem !important;
    padding-bottom: 8rem !important;
    max-width: 900px !important;
}

#MainMenu {
    visibility: hidden;
}

footer {
    visibility: hidden;
}

header {
    background: transparent !important;
}


/* ---------------------------------------------------------
   BOUTONS
--------------------------------------------------------- */

.stButton > button {
    width: 100%;
    border-radius: 12px !important;
    font-weight: 800 !important;
}


/* ---------------------------------------------------------
   TABS
--------------------------------------------------------- */

div[data-baseweb="tab-list"] {
    gap: 6px;
}

button[data-baseweb="tab"] {
    font-weight: 800 !important;
}


/* ---------------------------------------------------------
   MOBILE : FORCER 4 CARTES PAR LIGNE
--------------------------------------------------------- */

@media (max-width: 700px) {

    .block-container {
        padding-left: 8px !important;
        padding-right: 8px !important;
    }

    div[data-testid="stHorizontalBlock"] {
        flex-wrap: nowrap !important;
        gap: 4px !important;
        align-items: flex-start !important;
    }

    div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {
        width: 25% !important;
        flex: 1 1 25% !important;
        min-width: 0 !important;
    }

    div[data-testid="stHorizontalBlock"] img {
        width: 100% !important;
        height: 78px !important;
        object-fit: cover !important;
        border-radius: 8px !important;
    }

    div[data-testid="stHorizontalBlock"] p {
        font-size: 9px !important;
        line-height: 1.05 !important;
        margin-top: 1px !important;
        margin-bottom: 1px !important;
        overflow: hidden !important;
        white-space: nowrap !important;
        text-overflow: ellipsis !important;
    }

    div[data-testid="stHorizontalBlock"] .stButton button {
        min-height: 25px !important;
        height: 25px !important;
        padding: 0 !important;
        font-size: 8px !important;
        border-radius: 6px !important;
    }

}


/* ---------------------------------------------------------
   DESKTOP
--------------------------------------------------------- */

@media (min-width: 701px) {

    div[data-testid="stHorizontalBlock"] img {
        max-height: 180px !important;
        object-fit: cover !important;
        border-radius: 10px !important;
    }

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
        json.dump(
            captures,
            f,
            ensure_ascii=False,
            indent=4
        )


def generate_rarity():
    scores = [1,2,3,4,5,6,7,8,9,10]
    weights = [8,11,14,15,15,13,10,7,4,1]

    return random.choices(
        scores,
        weights=weights,
        k=1
    )[0]


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
        (
            c for c in captures
            if c["id"] == capture_id
        ),
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
# POPUP / ZOOM
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

    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            "Rareté",
            f"{capture['score']}/10"
        )

    with col2:
        st.metric(
            "Classe",
            capture["rarete"]
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
    [
        "📸 CAPTURER",
        "📚 MON PIEDDEX"
    ]
)


# ============================================================
# ONGLET CAPTURE
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
                    [
                        c.get("numero", 0)
                        for c in captures
                    ],
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
# ONGLET PIEDDEX
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

        st.divider()

        # ====================================================
        # 4 PETITES CARTES PAR LIGNE
        # ====================================================

        for i in range(0, len(captures), 4):

            row = captures[i:i + 4]

            cols = st.columns(
                4,
                gap="small"
            )

            for index, col in enumerate(cols):

                if index >= len(row):
                    continue

                capture = row[index]

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

                    st.caption(
                        f"{rarity_emoji(capture['score'])} "
                        f"{capture['score']}/10"
                    )

                    if st.button(
                        "Voir",
                        key=f"view_{capture['id']}",
                        use_container_width=True
                    ):
                        show_specimen(capture)
