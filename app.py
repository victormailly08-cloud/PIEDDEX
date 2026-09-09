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
# FONCTIONS DE DONNÉES
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


# ============================================================
# SYSTÈME DE RARETÉ
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

    # Plus le score est élevé,
    # plus il est difficile à obtenir.
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
        return "◇"

    elif score <= 5:
        return "◆"

    elif score <= 7:
        return "✦"

    elif score == 8:
        return "✦✦"

    elif score == 9:
        return "★"

    else:
        return "✺"


def rarity_style(score):

    if score <= 3:

        return {
            "color": "#C9D2E3",
            "border": "#8996AA",
            "background": "#141922",
            "glow": "rgba(190, 205, 225, 0.22)"
        }

    elif score <= 5:

        return {
            "color": "#63E69B",
            "border": "#3FC879",
            "background": "#0D2118",
            "glow": "rgba(63, 200, 121, 0.32)"
        }

    elif score <= 7:

        return {
            "color": "#5CB7FF",
            "border": "#388FE5",
            "background": "#0C1D31",
            "glow": "rgba(56, 143, 229, 0.38)"
        }

    elif score == 8:

        return {
            "color": "#C58CFF",
            "border": "#9B57E9",
            "background": "#211038",
            "glow": "rgba(176, 92, 255, 0.48)"
        }

    elif score == 9:

        return {
            "color": "#FFD65C",
            "border": "#E7AC24",
            "background": "#332409",
            "glow": "rgba(255, 200, 61, 0.56)"
        }

    else:

        return {
            "color": "#FF78D0",
            "border": "#F348B6",
            "background": "#351126",
            "glow": "rgba(255, 82, 190, 0.68)"
        }


# ============================================================
# SUPPRESSION
# ============================================================

def delete_capture(capture_id):

    captures = load_captures()

    target = next(
        (
            capture
            for capture in captures
            if capture["id"] == capture_id
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
        capture
        for capture in captures
        if capture["id"] != capture_id
    ]

    save_captures(captures)


# ============================================================
# CSS GLOBAL
# ============================================================

st.markdown(
    """
    <style>

    /* ======================================================
       PAGE
    ====================================================== */

    html,
    body {
        overflow-x: hidden !important;
        max-width: 100vw !important;
    }

    [data-testid="stAppViewContainer"] {

        overflow-x: hidden !important;

        background:
            radial-gradient(
                circle at 50% -10%,
                #25375c 0%,
                #111725 32%,
                #090c12 70%
            );

        -webkit-overflow-scrolling: touch !important;
    }

    [data-testid="stMain"] {
        overflow-x: hidden !important;
    }

    .block-container {

        max-width: 900px !important;

        padding-top: 0.6rem !important;
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


    /* ======================================================
       TITRES
    ====================================================== */

    h1 {

        font-weight: 950 !important;

        letter-spacing: 1px !important;
    }

    h2,
    h3 {

        font-weight: 900 !important;
    }


    /* ======================================================
       ONGLETS
    ====================================================== */

    div[data-baseweb="tab-list"] {

        gap: 5px !important;

        padding: 4px !important;

        border-radius: 16px !important;

        background:
            rgba(15, 21, 33, 0.80) !important;

        border:
            1px solid rgba(255,255,255,0.08) !important;
    }

    button[data-baseweb="tab"] {

        font-weight: 850 !important;

        border-radius: 12px !important;

        min-height: 44px !important;
    }


    /* ======================================================
       BOUTONS
    ====================================================== */

    .stButton > button {

        width: 100%;

        border-radius: 11px !important;

        font-weight: 800 !important;

        transition:
            transform 0.15s ease,
            filter 0.15s ease !important;
    }

    .stButton > button:active {

        transform: scale(0.97);
    }


    /* ======================================================
       CAMÉRA
    ====================================================== */

    [data-testid="stCameraInput"] {

        border-radius: 18px !important;
    }


    /* ======================================================
       GRILLE COLLECTION MOBILE
    ====================================================== */

    @media (max-width: 700px) {

        .block-container {

            padding-left: 10px !important;
            padding-right: 10px !important;
        }


        .st-key-collection_grid
        div[data-testid="stHorizontalBlock"] {

            display: grid !important;

            grid-template-columns:
                repeat(4, minmax(0, 1fr)) !important;

            gap: 7px !important;

            width: 100% !important;

            overflow: visible !important;
        }


        .st-key-collection_grid
        div[data-testid="stHorizontalBlock"]
        > div[data-testid="column"] {

            width: 100% !important;

            min-width: 0 !important;

            flex: none !important;
        }


        /* Miniatures */

        .st-key-collection_grid img {

            width: 100% !important;

            height: 76px !important;

            object-fit: cover !important;

            border-radius: 9px !important;
        }


        /* Texte dans les mini-cartes */

        .st-key-collection_grid p {

            font-size: 9px !important;

            line-height: 1.05 !important;

            margin-top: 1px !important;
            margin-bottom: 1px !important;

            white-space: nowrap !important;

            overflow: hidden !important;

            text-overflow: ellipsis !important;
        }


        /* Bouton Voir */

        .st-key-collection_grid
        .stButton > button {

            min-height: 27px !important;

            height: 27px !important;

            padding: 0px 1px !important;

            font-size: 9px !important;

            border-radius: 7px !important;
        }

    }


    /* ======================================================
       DESKTOP
    ====================================================== */

    @media (min-width: 701px) {

        .st-key-collection_grid img {

            width: 100% !important;

            height: 150px !important;

            object-fit: cover !important;

            border-radius: 11px !important;
        }

    }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# CSS DYNAMIQUE POUR UNE CARTE
# ============================================================

def inject_card_style(capture):

    style = rarity_style(capture["score"])

    card_key = f"card_{capture['id']}"
    score_key = f"score_{capture['id']}"

    css = f"""
    <style>

    .st-key-{card_key} {{

        background:
            linear-gradient(
                145deg,
                {style["background"]},
                #090C12
            ) !important;

        border:
            1px solid {style["border"]} !important;

        border-radius:
            13px !important;

        padding:
            4px !important;

        box-shadow:
            0 0 0 1px
                color-mix(
                    in srgb,
                    {style["border"]} 25%,
                    transparent
                ),
            0 0 14px
                {style["glow"]},
            0 8px 20px
                rgba(0,0,0,0.28) !important;

        overflow:
            hidden !important;
    }}


    .st-key-{card_key} img {{

        border:
            1px solid
            color-mix(
                in srgb,
                {style["border"]} 55%,
                transparent
            ) !important;
    }}


    .st-key-{score_key} p {{

        color:
            {style["color"]} !important;

        font-weight:
            900 !important;

        text-shadow:
            0 0 8px
            {style["glow"]} !important;
    }}


    .st-key-{card_key}
    .stButton > button {{

        background:
            linear-gradient(
                145deg,
                {style["background"]},
                #10141C
            ) !important;

        border:
            1px solid
            {style["border"]} !important;

        color:
            {style["color"]} !important;

        box-shadow:
            0 0 7px
            {style["glow"]} !important;
    }}

    </style>
    """

    st.markdown(
        css,
        unsafe_allow_html=True
    )


# ============================================================
# CSS DYNAMIQUE POUR L'ANALYSE
# ============================================================

def inject_analysis_style(capture_id, score):

    style = rarity_style(score)

    analysis_key = f"analysis_{capture_id}"

    css = f"""
    <style>

    .st-key-{analysis_key} {{

        background:
            radial-gradient(
                circle at 50% 20%,
                {style["glow"]},
                transparent 45%
            ),
            linear-gradient(
                145deg,
                {style["background"]},
                #090C12
            ) !important;

        border:
            2px solid
            {style["border"]} !important;

        border-radius:
            22px !important;

        padding:
            18px !important;

        margin-top:
            12px !important;

        box-shadow:
            0 0 0 1px
                {style["border"]},
            0 0 26px
                {style["glow"]},
            0 18px 35px
                rgba(0,0,0,0.40) !important;
    }}


    .st-key-{analysis_key}
    [data-testid="stMetricValue"] {{

        color:
            {style["color"]} !important;

        font-weight:
            950 !important;

        text-shadow:
            0 0 12px
            {style["glow"]} !important;
    }}


    .st-key-{analysis_key}
    [data-testid="stMetricLabel"] {{

        color:
            #C7D1E2 !important;

        font-weight:
            800 !important;
    }}


    .st-key-{analysis_key} h3 {{

        color:
            {style["color"]} !important;

        text-shadow:
            0 0 13px
            {style["glow"]} !important;
    }}

    </style>
    """

    st.markdown(
        css,
        unsafe_allow_html=True
    )


# ============================================================
# FICHE AGRANDIE
# ============================================================

@st.dialog("Fiche du spécimen")
def show_specimen(capture):

    style = rarity_style(
        capture["score"]
    )

    popup_key = (
        f"popup_{capture['id']}"
    )

    st.markdown(
        f"""
        <style>

        .st-key-{popup_key} {{

            border:
                2px solid
                {style["border"]} !important;

            border-radius:
                18px !important;

            padding:
                10px !important;

            background:
                linear-gradient(
                    145deg,
                    {style["background"]},
                    #090C12
                ) !important;

            box-shadow:
                0 0 22px
                {style["glow"]} !important;
        }}


        .st-key-{popup_key}
        [data-testid="stMetricValue"] {{

            color:
                {style["color"]} !important;
        }}

        </style>
        """,
        unsafe_allow_html=True
    )

    with st.container(
        key=popup_key
    ):

        if os.path.exists(
            capture["photo"]
        ):

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

            delete_capture(
                capture["id"]
            )

            st.rerun()


# ============================================================
# HEADER
# ============================================================

st.title(
    "🦶 PIEDDEX"
)

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
# ONGLET CAPTURE
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
            caption="Spécimen détecté",
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

                # --------------------------------------------
                # ANALYSE
                # --------------------------------------------

                with st.spinner(
                    "Analyse du spécimen en cours..."
                ):

                    score = generate_rarity()

                    rarete = rarity_name(
                        score
                    )


                # --------------------------------------------
                # CRÉATION DE L'ID
                # --------------------------------------------

                capture_id = (
                    datetime.now()
                    .strftime(
                        "%Y%m%d_%H%M%S_%f"
                    )
                )


                # --------------------------------------------
                # ENREGISTREMENT PHOTO
                # --------------------------------------------

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


                # --------------------------------------------
                # NUMÉRO DU SPÉCIMEN
                # --------------------------------------------

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


                # --------------------------------------------
                # DONNÉES
                # --------------------------------------------

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
                        datetime.now()
                        .strftime(
                            "%d/%m/%Y à %H:%M"
                        )
                }


                captures.append(
                    capture
                )

                save_captures(
                    captures
                )


                # --------------------------------------------
                # STYLE DU RÉSULTAT
                # --------------------------------------------

                inject_analysis_style(
                    capture_id,
                    score
                )


                # --------------------------------------------
                # RÉVÉLATION
                # --------------------------------------------

                with st.container(
                    key=f"analysis_{capture_id}"
                ):

                    st.caption(
                        f"NOUVEAU SPÉCIMEN "
                        f"#{numero:03d}"
                    )

                    st.subheader(
                        f"{rarity_emoji(score)} "
                        f"{nom.upper()}"
                    )

                    st.metric(
                        "NOTE DE RARETÉ",
                        f"{score}/10"
                    )

                    st.markdown(
                        f"### {rarete}"
                    )

                    if score <= 3:

                        st.write(
                            "Un spécimen relativement "
                            "commun, mais désormais "
                            "répertorié dans ton PiedDex."
                        )

                    elif score <= 5:

                        st.write(
                            "Une capture intéressante. "
                            "Ce spécimen se distingue "
                            "déjà de la moyenne."
                        )

                    elif score <= 7:

                        st.write(
                            "Belle trouvaille ! "
                            "Ce spécimen appartient "
                            "à une catégorie rare."
                        )

                    elif score == 8:

                        st.write(
                            "⚡ Capture exceptionnelle ! "
                            "Un spécimen épique vient "
                            "d'être découvert."
                        )

                    elif score == 9:

                        st.write(
                            "✨ DÉCOUVERTE LÉGENDAIRE ! "
                            "Très peu de captures "
                            "atteignent cette rareté."
                        )

                    else:

                        st.write(
                            "🌟 SPÉCIMEN MYTHIQUE 🌟"
                        )

                        st.write(
                            "Une capture extrêmement "
                            "rare. Le sommet du PiedDex."
                        )


                # --------------------------------------------
                # EFFETS
                # --------------------------------------------

                if score >= 8:

                    st.balloons()

                elif score >= 6:

                    st.toast(
                        "✦ Nouveau spécimen rare !"
                    )


# ============================================================
# ONGLET MON PIEDDEX
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
            f"{len(captures)} spécimen(s) découvert(s)"
        )


        # ====================================================
        # TRI
        # ====================================================

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
        # GRILLE
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


                    # ----------------------------------------
                    # STYLE DE LA CARTE
                    # ----------------------------------------

                    inject_card_style(
                        capture
                    )


                    with col:

                        card_key = (
                            f"card_{capture['id']}"
                        )

                        score_key = (
                            f"score_{capture['id']}"
                        )


                        # ====================================
                        # CARTE
                        # ====================================

                        with st.container(
                            key=card_key,
                            border=True
                        ):


                            # -------------------------------
                            # PHOTO
                            # -------------------------------

                            if os.path.exists(
                                capture["photo"]
                            ):

                                st.image(
                                    capture["photo"],
                                    use_container_width=True
                                )


                            # -------------------------------
                            # NUMÉRO
                            # -------------------------------

                            st.caption(
                                f"#{capture['numero']:03d}"
                            )


                            # -------------------------------
                            # NOM
                            # -------------------------------

                            st.markdown(
                                f"**{capture['nom']}**"
                            )


                            # -------------------------------
                            # SCORE COLORÉ
                            # -------------------------------

                            with st.container(
                                key=score_key
                            ):

                                st.write(
                                    f"{rarity_emoji(capture['score'])} "
                                    f"{capture['score']}/10"
                                )


                            # -------------------------------
                            # VOIR
                            # -------------------------------

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
