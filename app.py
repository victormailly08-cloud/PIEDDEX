import streamlit as st
import random
import os
import json
from datetime import datetime
from pathlib import Path

# -------------------------------------------------------
# CONFIGURATION
# -------------------------------------------------------

st.set_page_config(
    page_title="PiedDex",
    page_icon="🦶",
    layout="centered",
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


# -------------------------------------------------------
# DESIGN
# -------------------------------------------------------

st.markdown("""
<style>

/* Fond principal */
.stApp {
    background:
        radial-gradient(circle at top, #431010 0%, #160606 35%, #080808 100%);
    color: white;
}

/* Masquer éléments Streamlit */
#MainMenu {
    visibility: hidden;
}

footer {
    visibility: hidden;
}

header {
    background: transparent !important;
}

/* Conteneur */
.block-container {
    padding-top: 1rem;
    padding-bottom: 5rem;
    max-width: 700px;
}

/* Logo */
.pieddex-logo {
    text-align: center;
    font-size: 42px;
    font-weight: 900;
    letter-spacing: 3px;
    color: white;
    margin-bottom: 0;
}

.pieddex-subtitle {
    text-align: center;
    color: #ff4a4a;
    font-weight: bold;
    letter-spacing: 4px;
    font-size: 13px;
    margin-bottom: 25px;
}

/* Écran scanner */
.scanner {
    border: 4px solid #1f1f1f;
    background: linear-gradient(145deg, #222, #090909);
    border-radius: 20px;
    padding: 15px;
    box-shadow:
        0 0 0 4px #a81414,
        0 10px 30px rgba(0,0,0,0.5);
    margin-bottom: 20px;
}

/* voyant */
.light-row {
    display:flex;
    gap:8px;
    margin-bottom:15px;
}

.light-blue {
    width:22px;
    height:22px;
    border-radius:50%;
    background:#43d9ff;
    box-shadow:0 0 15px #43d9ff;
}

.light-red {
    width:10px;
    height:10px;
    border-radius:50%;
    background:#ff3333;
}

.light-yellow {
    width:10px;
    height:10px;
    border-radius:50%;
    background:#ffd633;
}

.light-green {
    width:10px;
    height:10px;
    border-radius:50%;
    background:#4dff76;
}

/* Cartes */
.specimen-card {
    background: linear-gradient(145deg, #171717, #0b0b0b);
    border: 2px solid #3b3b3b;
    border-radius: 18px;
    padding: 12px;
    margin-bottom: 20px;
    box-shadow: 0 5px 20px rgba(0,0,0,.35);
}

/* Score */
.score {
    font-size: 34px;
    font-weight: 900;
    text-align: center;
}

.rarity {
    text-align:center;
    font-size:18px;
    font-weight:800;
    letter-spacing:2px;
}

/* boutons */
.stButton > button {
    width:100%;
    border-radius:12px;
    min-height:50px;
    font-size:17px;
    font-weight:800;
    border:2px solid #ff3434;
    background:#b81818;
    color:white;
}

.stButton > button:hover {
    background:#e02626;
    border-color:#ff7373;
    color:white;
}

/* Tabs */
button[data-baseweb="tab"] {
    font-size:16px !important;
    font-weight:800 !important;
}

</style>
""", unsafe_allow_html=True)


# -------------------------------------------------------
# FONCTIONS
# -------------------------------------------------------

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
    """
    Tirage pondéré :
    les grosses raretés sont beaucoup moins fréquentes.
    """

    scores = [
        1, 2, 3,
        4, 5,
        6, 7,
        8,
        9,
        10
    ]

    weights = [
        8, 12, 15,
        15, 15,
        12, 10,
        7,
        4,
        2
    ]

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

    return "🔥"


# -------------------------------------------------------
# HEADER
# -------------------------------------------------------

st.markdown(
    '<div class="pieddex-logo">🦶 PIEDDEX</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="pieddex-subtitle">ENCYCLOPÉDIE DES SPÉCIMENS</div>',
    unsafe_allow_html=True
)


# -------------------------------------------------------
# ONGLET
# -------------------------------------------------------

tab_capture, tab_collection = st.tabs(
    ["📸 CAPTURER", "📖 MON PIEDDEX"]
)


# =======================================================
# CAPTURE
# =======================================================

with tab_capture:

    st.markdown("""
    <div class="scanner">

        <div class="light-row">
            <div class="light-blue"></div>
            <div class="light-red"></div>
            <div class="light-yellow"></div>
            <div class="light-green"></div>
        </div>

        <h3 style="text-align:center;">
            SCANNER DE SPÉCIMEN
        </h3>

        <p style="text-align:center;color:#aaa;">
            Place le spécimen dans le champ de la caméra.
        </p>

    </div>
    """, unsafe_allow_html=True)

    photo = st.camera_input(
        "📷 CAPTURER UN NOUVEAU SPÉCIMEN"
    )

    if photo:

        st.markdown("### ✅ Spécimen détecté")

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
                    "Entre d'abord un nom pour ce spécimen."
                )

            else:

                score = generate_rarity()

                rarete = rarity_name(score)

                capture_id = datetime.now().strftime(
                    "%Y%m%d_%H%M%S_%f"
                )

                filename = f"{capture_id}.jpg"

                filepath = PHOTOS_FOLDER / filename

                with open(filepath, "wb") as f:
                    f.write(photo.getbuffer())

                captures = load_captures()

                numero = len(captures) + 1

                capture = {

                    "id": capture_id,

                    "numero": numero,

                    "nom": nom.strip(),

                    "score": score,

                    "rarete": rarete,

                    "photo": str(filepath),

                    "date": datetime.now().strftime(
                        "%d/%m/%Y %H:%M"
                    )
                }

                captures.append(capture)

                save_captures(captures)

                st.markdown("---")

                st.markdown(
                    "## 🧬 ANALYSE TERMINÉE"
                )

                st.markdown(
                    f"""
                    <div class="score">
                        {score}/10
                    </div>

                    <div class="rarity">
                        {rarity_emoji(score)} {rarete}
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                st.success(
                    f"#{numero:03d} — {nom.upper()} ajouté au PiedDex !"
                )

                st.balloons()


# =======================================================
# COLLECTION
# =======================================================

with tab_collection:

    captures = load_captures()

    if len(captures) == 0:

        st.info(
            "Ton PiedDex est vide. Capture ton premier spécimen !"
        )

    else:

        st.markdown(
            f"### 🦶 {len(captures)} spécimen(s) découvert(s)"
        )

        sort_option = st.selectbox(
            "Classer les captures",
            [
                "Plus récentes",
                "Plus anciennes",
                "Rareté décroissante",
                "Rareté croissante"
            ]
        )

        if sort_option == "Plus récentes":
            captures = captures[::-1]

        elif sort_option == "Plus anciennes":
            pass

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

        st.markdown("---")

        for capture in captures:

            st.markdown(
                '<div class="specimen-card">',
                unsafe_allow_html=True
            )

            if os.path.exists(capture["photo"]):

                st.image(
                    capture["photo"],
                    use_container_width=True
                )

            st.markdown(
                f"## #{capture['numero']:03d} — {capture['nom']}"
            )

            st.markdown(
                f"""
                <div class="score">
                    {capture['score']}/10
                </div>

                <div class="rarity">
                    {rarity_emoji(capture['score'])}
                    {capture['rarete']}
                </div>
                """,
                unsafe_allow_html=True
            )

            st.caption(
                f"Capturé le {capture['date']}"
            )

            st.markdown(
                "</div>",
                unsafe_allow_html=True
            )
