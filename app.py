import streamlit as st
import random
import os
import json
from datetime import datetime
from pathlib import Path

# =========================================================
# CONFIG
# =========================================================

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


# =========================================================
# CSS
# =========================================================

st.markdown("""
<style>

/* ---------------------------------------------------------
   BASE / MOBILE
--------------------------------------------------------- */

html, body {
    overscroll-behavior-y: auto !important;
    touch-action: pan-y !important;
}

[data-testid="stAppViewContainer"] {
    overflow-y: auto !important;
    -webkit-overflow-scrolling: touch !important;
    touch-action: pan-y !important;

    background:
        radial-gradient(circle at 50% -10%, #283960 0%, #111827 30%, #070a10 75%);
}

[data-testid="stMain"] {
    overflow-y: visible !important;
}

.block-container {
    padding-top: 0.5rem !important;
    padding-bottom: 7rem !important;
    max-width: 950px !important;
}

/* Streamlit UI */

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
   HEADER
--------------------------------------------------------- */

.logo {
    text-align: center;
    font-size: 38px;
    font-weight: 1000;
    letter-spacing: 3px;
    color: white;

    text-shadow:
        0 3px 0 #182744,
        0 0 18px rgba(100,180,255,.35);

    margin-top: 5px;
}

.subtitle {
    text-align: center;
    font-size: 11px;
    letter-spacing: 4px;
    font-weight: 800;
    color: #a9b9d3;
    margin-bottom: 18px;
}


/* ---------------------------------------------------------
   TABS
--------------------------------------------------------- */

div[data-baseweb="tab-list"] {
    background: rgba(8,12,20,.85);
    border: 1px solid rgba(255,255,255,.08);
    border-radius: 18px;
    padding: 5px;
    gap: 3px;
    backdrop-filter: blur(15px);
}

button[data-baseweb="tab"] {
    border-radius: 14px !important;
    color: #bdc8db !important;
    font-weight: 850 !important;
    font-size: 15px !important;
    min-height: 46px !important;
}

button[data-baseweb="tab"][aria-selected="true"] {
    background:
        linear-gradient(
            145deg,
            rgba(71,108,171,.65),
            rgba(30,57,96,.75)
        ) !important;

    color: white !important;
}


/* ---------------------------------------------------------
   SCANNER
--------------------------------------------------------- */

.scanner {
    background:
        linear-gradient(
            145deg,
            rgba(34,50,78,.97),
            rgba(11,17,29,.98)
        );

    border: 1px solid rgba(173,205,255,.25);
    border-radius: 25px;
    padding: 20px;

    box-shadow:
        inset 0 1px 0 rgba(255,255,255,.15),
        0 20px 50px rgba(0,0,0,.38);

    margin-top: 15px;
    margin-bottom: 20px;
}

.scanner-title {
    text-align: center;
    font-size: 21px;
    font-weight: 950;
    letter-spacing: 1px;
    color: #ffffff;
}

.scanner-text {
    text-align: center;
    font-size: 13px;
    color: #aebbd1;
    margin-top: 5px;
}


/* Voyants scanner */

.scanner-lights {
    text-align:center;
    margin-bottom:12px;
}

.light {
    display:inline-block;
    border-radius:50%;
    margin:0 4px;
}

.blue-light {
    width:22px;
    height:22px;
    background:#64d7ff;
    box-shadow:0 0 16px #64d7ff;
}

.red-light {
    width:10px;
    height:10px;
    background:#ff5d70;
    box-shadow:0 0 6px #ff5d70;
}

.yellow-light {
    width:10px;
    height:10px;
    background:#ffd75a;
    box-shadow:0 0 6px #ffd75a;
}

.green-light {
    width:10px;
    height:10px;
    background:#65e59a;
    box-shadow:0 0 6px #65e59a;
}


/* ---------------------------------------------------------
   BUTTONS
--------------------------------------------------------- */

.stButton > button {
    border-radius: 14px !important;
    min-height: 46px;
    font-weight: 850;
    border: 1px solid rgba(255,255,255,.15);

    background:
        linear-gradient(
            145deg,
            #4267a4,
            #253e6b
        );

    color: white;

    box-shadow:
        inset 0 1px 0 rgba(255,255,255,.18),
        0 5px 16px rgba(0,0,0,.23);
}

.stButton > button:hover {
    border-color: #93c7ff;
    transform: translateY(-1px);
}


/* ---------------------------------------------------------
   COLLECTION
--------------------------------------------------------- */

.collection-title {
    font-size: 22px;
    font-weight: 950;
    color: white;
    margin-top: 18px;
}

.counter {
    color: #a9b8cd;
    margin-bottom: 12px;
}


/* ---------------------------------------------------------
   CARD
--------------------------------------------------------- */

.card-info {
    text-align: center;

    background:
        linear-gradient(
            150deg,
            rgba(243,248,255,.14),
            rgba(123,158,215,.06)
        );

    border: 1px solid rgba(218,234,255,.25);

    border-radius: 0 0 13px 13px;

    padding: 5px 2px 6px 2px;

    margin-top: -7px;

    box-shadow:
        0 5px 15px rgba(0,0,0,.2);
}

.card-number {
    font-size: 9px;
    color: #9eacc2;
    font-weight: 800;
}

.card-name {
    font-size: 11px;
    color: white;
    font-weight: 900;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.card-rarity {
    font-size: 11px;
    font-weight: 950;
    margin-top: 1px;
}


/* ---------------------------------------------------------
   RESULT REVEAL
--------------------------------------------------------- */

.reveal {
    background:
        radial-gradient(
            circle,
            rgba(78,132,220,.28),
            rgba(11,17,29,.95) 65%
        );

    border: 1px solid rgba(158,198,255,.25);
    border-radius: 25px;
    text-align:center;
    padding: 25px 15px;

    box-shadow:
        0 0 40px rgba(77,148,255,.12);
}

.reveal-number {
    color:#91a4c1;
    font-size:13px;
    font-weight:800;
}

.reveal-name {
    color:white;
    font-size:26px;
    font-weight:1000;
}

.reveal-score {
    color:white;
    font-size:52px;
    font-weight:1000;
    line-height:1;
    margin-top:10px;
}

.reveal-rarity {
    font-size:20px;
    font-weight:950;
    letter-spacing:2px;
    margin-top:8px;
}


/* ---------------------------------------------------------
   CAMERA
--------------------------------------------------------- */

[data-testid="stCameraInput"] {
    border-radius: 20px;
}


/* ---------------------------------------------------------
   MOBILE
--------------------------------------------------------- */

@media(max-width:600px) {

    .block-container {
        padding-left: 9px !important;
        padding-right: 9px !important;
    }

    .logo {
        font-size: 32px;
    }

    .card-name {
        font-size: 9px;
    }

    .card-rarity {
        font-size: 9px;
    }

    .stButton > button {
        padding-left: 3px !important;
        padding-right: 3px !important;
    }
}

</style>
""", unsafe_allow_html=True)


# =========================================================
# DATA
# =========================================================

def load_captures():
    try:
        with open(DATABASE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []


def save_captures(data):
    with open(DATABASE_FILE, "w", encoding="utf-8") as f:
        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=4
        )


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

    if score <= 5:
        return "PEU COMMUN"

    if score <= 7:
        return "RARE"

    if score == 8:
        return "ÉPIQUE"

    if score == 9:
        return "LÉGENDAIRE"

    return "MYTHIQUE"


def rarity_symbol(score):

    if score <= 3:
        return "◇"

    if score <= 5:
        return "◆"

    if score <= 7:
        return "✦"

    if score == 8:
        return "✦✦"

    if score == 9:
        return "★"

    return "★★★"


def rarity_color(score):

    if score <= 3:
        return "#c7ceda"

    if score <= 5:
        return "#77daa7"

    if score <= 7:
        return "#73b9ff"

    if score == 8:
        return "#c28cff"

    if score == 9:
        return "#ffd768"

    return "#ff8bc7"


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


# =========================================================
# DIALOG
# =========================================================

@st.dialog("Fiche du spécimen")
def show_specimen(capture):

    if os.path.exists(capture["photo"]):
        st.image(
            capture["photo"],
            use_container_width=True
        )

    color = rarity_color(capture["score"])

    st.markdown(
        f"""
        <div style="text-align:center">

            <div style="
                color:#93a2b8;
                font-size:13px;
                font-weight:800;
            ">
                ENTRÉE #{capture["numero"]:03d}
            </div>

            <div style="
                color:white;
                font-size:28px;
                font-weight:1000;
            ">
                {capture["nom"].upper()}
            </div>

            <div style="
                color:{color};
                font-size:45px;
                font-weight:1000;
            ">
                {capture["score"]}/10
            </div>

            <div style="
                color:{color};
                font-size:18px;
                font-weight:950;
                letter-spacing:2px;
            ">
                {rarity_symbol(capture["score"])}
                {capture["rarete"]}
            </div>

        </div>
        """,
        unsafe_allow_html=True
    )

    st.caption(
        f"Capturé le {capture['date']}"
    )

    st.markdown("---")

    if st.button(
        "🗑️ Supprimer ce spécimen",
        key=f"delete_{capture['id']}",
        use_container_width=True
    ):

        delete_capture(capture["id"])

        st.session_state["close_dialog"] = True

        st.rerun()


# =========================================================
# HEADER
# =========================================================

st.markdown(
    '<div class="logo">PIEDDEX</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">COLLECTION DE SPÉCIMENS</div>',
    unsafe_allow_html=True
)


# =========================================================
# TABS
# =========================================================

tab_capture, tab_collection = st.tabs(
    [
        "📸 CAPTURER",
        "📚 MON PIEDDEX"
    ]
)


# =========================================================
# CAPTURE
# =========================================================

with tab_capture:

    # Scanner corrigé : HTML très simple
    st.markdown(
        """
        <div class="scanner">

            <div class="scanner-lights">
                <span class="light blue-light"></span>
                <span class="light red-light"></span>
                <span class="light yellow-light"></span>
                <span class="light green-light"></span>
            </div>

            <div class="scanner-title">
                SCANNER DE SPÉCIMEN
            </div>

            <div class="scanner-text">
                Place le spécimen dans le champ de la caméra
            </div>

        </div>
        """,
        unsafe_allow_html=True
    )

    photo = st.camera_input(
        "📷 Prendre une photo"
    )

    if photo:

        st.markdown("### Spécimen détecté")

        nom = st.text_input(
            "Nom du spécimen",
            placeholder="Ex : Piedouille"
        )

        if st.button(
            "🔍 ANALYSER",
            use_container_width=True
        ):

            if not nom.strip():

                st.warning(
                    "Entre le nom du spécimen."
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

                numero = (
                    max(
                        [
                            c.get("numero", 0)
                            for c in captures
                        ],
                        default=0
                    )
                    + 1
                )

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

                color = rarity_color(score)

                st.markdown(
                    f"""
                    <div class="reveal">

                        <div class="reveal-number">
                            NOUVEAU SPÉCIMEN
                            #{numero:03d}
                        </div>

                        <div class="reveal-name">
                            {nom.upper()}
                        </div>

                        <div
                            class="reveal-score"
                            style="color:{color}"
                        >
                            {score}/10
                        </div>

                        <div
                            class="reveal-rarity"
                            style="color:{color}"
                        >
                            {rarity_symbol(score)}
                            {rarete}
                        </div>

                    </div>
                    """,
                    unsafe_allow_html=True
                )

                if score >= 9:
                    st.balloons()


# =========================================================
# COLLECTION
# =========================================================

with tab_collection:

    captures = load_captures()

    if not captures:

        st.info(
            "Aucun spécimen capturé pour le moment."
        )

    else:

        st.markdown(
            '<div class="collection-title">Ma collection</div>',
            unsafe_allow_html=True
        )

        st.markdown(
            f"""
            <div class="counter">
                {len(captures)} spécimen(s) découvert(s)
            </div>
            """,
            unsafe_allow_html=True
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


        # -------------------------------------------------
        # GRILLE 4 PAR LIGNE
        # -------------------------------------------------

        for i in range(0, len(captures), 4):

            row = captures[i:i + 4]

            cols = st.columns(
                4,
                gap="small"
            )

            for col, capture in zip(cols, row):

                with col:

                    if os.path.exists(capture["photo"]):

                        st.image(
                            capture["photo"],
                            use_container_width=True
                        )

                    color = rarity_color(
                        capture["score"]
                    )

                    st.markdown(
                        f"""
                        <div class="card-info">

                            <div class="card-number">
                                #{capture["numero"]:03d}
                            </div>

                            <div class="card-name">
                                {capture["nom"].upper()}
                            </div>

                            <div
                                class="card-rarity"
                                style="color:{color}"
                            >
                                {capture["score"]}/10
                                {rarity_symbol(capture["score"])}
                            </div>

                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                    if st.button(
                        "VOIR",
                        key=f"view_{capture['id']}",
                        use_container_width=True
                    ):

                        show_specimen(capture)
