import streamlit as st
import random
import os
import json
from datetime import datetime
from pathlib import Path


# ============================================================
# CONFIGURATION
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
# CSS
# ============================================================

st.markdown("""
<style>

/* ========================================
   GLOBAL
======================================== */

html, body {
    overflow-x: hidden !important;
    max-width: 100vw !important;
}

[data-testid="stAppViewContainer"] {
    overflow-x: hidden !important;
    -webkit-overflow-scrolling: touch !important;
}

[data-testid="stMain"] {
    overflow-x: hidden !important;
}

.block-container {
    max-width: 900px !important;
    padding-top: 0.5rem !important;
    padding-bottom: 8rem !important;
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


/* ========================================
   BOUTONS NORMAUX
======================================== */

.stButton > button {
    width: 100%;
    border-radius: 12px !important;
    font-weight: 800 !important;
}


/* ========================================
   TABS
======================================== */

div[data-baseweb="tab-list"] {
    gap: 5px;
}

button[data-baseweb="tab"] {
    font-weight: 800 !important;
}


/* ========================================
   UNIQUEMENT LA GRILLE DU PIEDDEX
======================================== */

@media (max-width: 700px) {

    .block-container {
        padding-left: 10px !important;
        padding-right: 10px !important;
    }


    /*
    On cible UNIQUEMENT le container
    collection_grid.
    */

    .st-key-collection_grid
    div[data-testid="stHorizontalBlock"] {

        display: grid !important;

        grid-template-columns:
            repeat(4, minmax(0, 1fr)) !important;

        gap: 6px !important;

        width: 100% !important;

        overflow: visible !important;
    }


    /*
    Les colonnes Streamlit deviennent
    simplement des cases de grille.
    */

    .st-key-collection_grid
    div[data-testid="stHorizontalBlock"]
    > div[data-testid="column"] {

        width: 100% !important;

        min-width: 0 !important;

        flex: none !important;
    }


    /*
    Miniature
    */

    .st-key-collection_grid img {

        width: 100% !important;

        height: 78px !important;

        object-fit: cover !important;

        border-radius: 8px !important;
    }


    /*
    Numéro / nom / rareté
    */

    .st-key-collection_grid p {

        font-size: 9px !important;

        line-height: 1.05 !important;

        margin-top: 1px !important;

        margin-bottom: 1px !important;

        overflow: hidden !important;

        white-space: nowrap !important;

        text-overflow: ellipsis !important;
    }


    /*
    Petit bouton VOIR
    */

    .st-key-collection_grid
    .stButton > button {

        min-height: 27px !important;

        height: 27px !important;

        font-size: 9px !important;

        padding: 0px 1px !important;

        border-radius: 7px !important;
    }

}


/* ========================================
   DESKTOP
======================================== */

@media (min-width: 701px) {

    .st-key-collection_grid img {
        width: 100% !important;
        height: 150px !important;
        object-fit: cover !important;
        border-radius: 10px !important;
    }

}

</style>
""", unsafe_allow_html=True)


# ============================================================
# DONNÉES
# ============================================================

def load_captures():

    try:

        with open(
            DATABASE_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            return json.load(f)

    except:

        return []


def save_captures(captures):

    with open(
        DATABASE_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            captures,
            f,
            ensure_ascii=False,
            indent=4
        )


# ============================================================
# RARETÉ
# ============================================================

def generate_rarity():

    scores = [
        1, 2, 3,
        4, 5,
        6, 7,
        8,
        9,
        10
    ]

    weights = [
        8, 11, 14,
        15, 15,
        13, 10,
        7,
        4,
        1
    ]

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


# ============================================================
# SUPPRESSION
# ============================================================

def delete_capture(capture_id):

    captures = load_captures()

    target = next(
        (
            c
            for c in captures
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

        c

        for c in captures

        if c["id"] != capture_id

    ]

    save_captures(captures)


# ============================================================
# FICHE AGRANDIE
# ============================================================

@st.dialog("Fiche du spécimen")
def show_specimen(capture):

    if os.path.exists(capture["photo"]):

        st.image(
            capture["photo"],
            use_container_width=True
        )


    st.markdown(
        f"### #{capture['numero']:03d} — "
        f"{capture['nom']}"
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
# TITRE
# ============================================================

st.title("🦶 PIEDDEX")

st.caption(
    "Collection personnelle de spécimens"
)


# ============================================================
# ONGLETS
# ============================================================

tab_capture, tab_collection = st.tabs(
    [
        "📸 CAPTURER",
        "📚 MON PIEDDEX"
    ]
)


# ============================================================
# CAPTURE
# ============================================================

with tab_capture:

    st.subheader(
        "Scanner de spécimen"
    )


    st.info(
        "Prends une photo du pied, "
        "donne-lui un nom puis lance l'analyse."
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


                capture_id = (
                    datetime.now()
                    .strftime(
                        "%Y%m%d_%H%M%S_%f"
                    )
                )


                filepath = (
                    PHOTOS_FOLDER /
                    f"{capture_id}.jpg"
                )


                with open(
                    filepath,
                    "wb"
                ) as f:

                    f.write(
                        photo.getbuffer()
                    )


                captures = load_captures()


                numero = max(
                    [
                        c.get(
                            "numero",
                            0
                        )
                        for c in captures
                    ],
                    default=0
                ) + 1


                capture = {

                    "id":
                        capture_id,

                    "numero":
                        numero,

                    "nom":
                        nom.strip(),

                    "score":
                        score,

                    "rarete":
                        rarete,

                    "photo":
                        str(filepath),

                    "date":
                        datetime.now().strftime(
                            "%d/%m/%Y à %H:%M"
                        )
                }


                captures.append(
                    capture
                )


                save_captures(
                    captures
                )


                st.success(
                    f"Nouveau spécimen : "
                    f"#{numero:03d} — "
                    f"{nom.upper()}"
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
# MON PIEDDEX
# ============================================================

with tab_collection:


    captures = load_captures()


    if not captures:


        st.info(
            "Ton PiedDex est vide pour le moment."
        )


    else:


        st.subheader(
            "Ma collection"
        )


        st.caption(
            f"{len(captures)} "
            f"spécimen(s) découvert(s)"
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
                key=lambda x:
                    x["score"],
                reverse=True
            )


        elif sort_option == "Rareté croissante":

            captures = sorted(
                captures,
                key=lambda x:
                    x["score"]
            )


        st.divider()


        # ====================================================
        # CONTAINER SPÉCIAL COLLECTION
        # ====================================================

        with st.container(
            key="collection_grid"
        ):


            for i in range(
                0,
                len(captures),
                4
            ):


                row = captures[
                    i:i + 4
                ]


                cols = st.columns(
                    4,
                    gap="small"
                )


                for index, col in enumerate(
                    cols
                ):


                    if index >= len(row):
                        continue


                    capture = row[index]


                    with col:


                        # ---------------------------
                        # PHOTO MINIATURE
                        # ---------------------------

                        if os.path.exists(
                            capture["photo"]
                        ):


                            st.image(
                                capture["photo"],
                                use_container_width=True
                            )


                        # ---------------------------
                        # NUMÉRO
                        # ---------------------------

                        st.caption(
                            f"#{capture['numero']:03d}"
                        )


                        # ---------------------------
                        # NOM
                        # ---------------------------

                        st.markdown(
                            f"**{capture['nom']}**"
                        )


                        # ---------------------------
                        # RARETÉ
                        # ---------------------------

                        st.caption(
                            f"{rarity_emoji(capture['score'])} "
                            f"{capture['score']}/10"
                        )


                        # ---------------------------
                        # VOIR
                        # ---------------------------

                        if st.button(
                            "Voir",
                            key=(
                                f"view_"
                                f"{capture['id']}"
                            ),
                            use_container_width=True
                        ):


                            show_specimen(
                                capture
                            )
