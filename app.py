import streamlit as st
import random
import os
import json
import base64
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
# CSS GLOBAL
# ============================================================

st.markdown("""
<style>

html, body {
    overscroll-behavior-y: auto !important;
    touch-action: pan-y !important;
}

[data-testid="stAppViewContainer"] {
    background:
        radial-gradient(circle at top, #28395f 0%, #111725 35%, #07090d 75%);
    color: white;
    overflow-y: auto !important;
    -webkit-overflow-scrolling: touch !important;
}

[data-testid="stMain"] {
    overflow-y: visible !important;
}

.block-container {
    padding-top: 0.4rem !important;
    padding-bottom: 8rem !important;
    max-width: 900px !important;
}

#MainMenu, footer {
    visibility: hidden;
}

header {
    background: transparent !important;
}

/* HEADER */
.app-title {
    text-align:center;
    font-size:34px;
    font-weight:1000;
    letter-spacing:3px;
    margin-top:4px;
}

.app-subtitle {
    text-align:center;
    font-size:11px;
    letter-spacing:4px;
    color:#9cb0ce;
    margin-bottom:16px;
}

/* TABS */
div[data-baseweb="tab-list"] {
    background:#0f1724;
    padding:4px;
    border-radius:16px;
    border:1px solid rgba(255,255,255,.08);
}

button[data-baseweb="tab"] {
    font-weight:900 !important;
    color:#b9c5d7 !important;
    border-radius:12px !important;
    min-height:44px !important;
}

button[data-baseweb="tab"][aria-selected="true"] {
    background:linear-gradient(145deg,#436cae,#253d69) !important;
    color:white !important;
}

/* CAMERA / INPUT */
[data-testid="stCameraInput"] {
    border-radius:18px;
}

.stButton > button {
    border-radius:14px !important;
    min-height:46px;
    font-weight:900;
    color:white;
    background:linear-gradient(145deg,#426da9,#253d66);
    border:1px solid rgba(255,255,255,.15);
}

/* MOBILE */
@media(max-width:600px) {
    .block-container {
        padding-left:10px !important;
        padding-right:10px !important;
    }
}

</style>
""", unsafe_allow_html=True)


# ============================================================
# DATA
# ============================================================

def load_captures():
    try:
        with open(DATABASE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []


def save_captures(data):
    with open(DATABASE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def generate_rarity():
    scores = [1,2,3,4,5,6,7,8,9,10]
    weights = [8,11,14,15,15,13,10,7,4,1]
    return random.choices(scores, weights=weights, k=1)[0]


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


def rarity_color(score):
    if score <= 3:
        return "#c8cfd9"
    if score <= 5:
        return "#78d5a2"
    if score <= 7:
        return "#70b9ff"
    if score == 8:
        return "#bb88ff"
    if score == 9:
        return "#ffd45f"
    return "#ff89c4"


def delete_capture(capture_id):
    captures = load_captures()

    target = next(
        (c for c in captures if c["id"] == capture_id),
        None
    )

    if target:
        path = target.get("photo")
        if path and os.path.exists(path):
            try:
                os.remove(path)
            except:
                pass

    captures = [c for c in captures if c["id"] != capture_id]
    save_captures(captures)


def image_to_base64(path):
    if not os.path.exists(path):
        return ""

    with open(path, "rb") as image_file:
        encoded = base64.b64encode(image_file.read()).decode()

    return f"data:image/jpeg;base64,{encoded}"


# ============================================================
# MODAL
# ============================================================

@st.dialog("Spécimen")
def show_specimen(capture):

    st.image(capture["photo"], use_container_width=True)

    color = rarity_color(capture["score"])

    st.markdown(
        f"""
        <div style="text-align:center">

            <div style="
                color:#8ea1bd;
                font-size:12px;
                font-weight:800;
                letter-spacing:2px;
            ">
                ENTRÉE #{capture["numero"]:03d}
            </div>

            <div style="
                font-size:28px;
                font-weight:1000;
                margin-top:4px;
            ">
                {capture["nom"].upper()}
            </div>

            <div style="
                color:{color};
                font-size:48px;
                font-weight:1000;
                margin-top:6px;
            ">
                {capture["score"]}/10
            </div>

            <div style="
                color:{color};
                font-size:17px;
                font-weight:900;
                letter-spacing:2px;
            ">
                {capture["rarete"]}
            </div>

        </div>
        """,
        unsafe_allow_html=True
    )

    st.caption(f"Capturé le {capture['date']}")

    st.markdown("---")

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

st.markdown(
    '<div class="app-title">PIEDDEX</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="app-subtitle">COLLECTION DE SPÉCIMENS</div>',
    unsafe_allow_html=True
)


# ============================================================
# TABS
# ============================================================

tab_capture, tab_collection = st.tabs(
    ["📸 CAPTURER", "📚 MON PIEDDEX"]
)


# ============================================================
# CAPTURE
# ============================================================

with tab_capture:

    st.subheader("Scanner de spécimen")

    st.info(
        "Place le pied dans le champ de la caméra puis prends la photo."
    )

    photo = st.camera_input("📷 Prendre une photo")

    if photo:

        nom = st.text_input(
            "Nom du spécimen",
            placeholder="Ex : Piedouille"
        )

        if st.button(
            "🔍 ANALYSER LE SPÉCIMEN",
            use_container_width=True
        ):

            if not nom.strip():
                st.warning("Entre un nom avant l'analyse.")

            else:

                score = generate_rarity()
                rarete = rarity_name(score)

                capture_id = datetime.now().strftime(
                    "%Y%m%d_%H%M%S_%f"
                )

                filepath = PHOTOS_FOLDER / f"{capture_id}.jpg"

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
                    "date": datetime.now().strftime("%d/%m/%Y à %H:%M")
                }

                captures.append(capture)
                save_captures(captures)

                color = rarity_color(score)

                st.success("Analyse terminée")

                st.markdown(
                    f"""
                    <div style="
                        background:linear-gradient(145deg,#172033,#0b1018);
                        border:1px solid rgba(255,255,255,.12);
                        border-radius:22px;
                        padding:22px;
                        text-align:center;
                        margin-top:10px;
                    ">

                        <div style="
                            color:#8ea1bd;
                            font-size:12px;
                            font-weight:800;
                            letter-spacing:2px;
                        ">
                            NOUVEAU SPÉCIMEN #{numero:03d}
                        </div>

                        <div style="
                            color:white;
                            font-size:28px;
                            font-weight:1000;
                            margin-top:4px;
                        ">
                            {nom.upper()}
                        </div>

                        <div style="
                            color:{color};
                            font-size:52px;
                            font-weight:1000;
                            margin-top:8px;
                        ">
                            {score}/10
                        </div>

                        <div style="
                            color:{color};
                            font-size:18px;
                            font-weight:900;
                        ">
                            {rarete}
                        </div>

                    </div>
                    """,
                    unsafe_allow_html=True
                )

                if score >= 9:
                    st.balloons()


# ============================================================
# COLLECTION
# ============================================================

with tab_collection:

    captures = load_captures()

    if not captures:
        st.info("Aucun spécimen dans ton PiedDex pour le moment.")

    else:

        st.markdown("## Ma collection")
        st.caption(f"{len(captures)} spécimen(s) découvert(s)")

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
        rows = [
            captures[i:i+4]
            for i in range(0, len(captures), 4)
        ]

        for row in rows:

            cols = st.columns(4, gap="small")

            for col, capture in zip(cols, row):

                with col:

                    image64 = image_to_base64(capture["photo"])
                    color = rarity_color(capture["score"])

                    # Petite carte carrée
                    st.markdown(
                        f"""
                        <div style="
                            background:
                                linear-gradient(
                                    145deg,
                                    rgba(255,255,255,.10),
                                    rgba(255,255,255,.03)
                                );
                            border:1px solid rgba(255,255,255,.16);
                            border-radius:12px;
                            overflow:hidden;
                            box-shadow:0 5px 14px rgba(0,0,0,.25);
                        ">

                            <div style="
                                aspect-ratio:1/1;
                                overflow:hidden;
                                background:#10141b;
                            ">
                                <img
                                    src="{image64}"
                                    style="
                                        width:100%;
                                        height:100%;
                                        object-fit:cover;
                                    "
                                >
                            </div>

                            <div style="
                                padding:5px 3px;
                                text-align:center;
                            ">

                                <div style="
                                    font-size:8px;
                                    color:#8698b3;
                                    font-weight:800;
                                ">
                                    #{capture["numero"]:03d}
                                </div>

                                <div style="
                                    font-size:9px;
                                    color:white;
                                    font-weight:900;
                                    white-space:nowrap;
                                    overflow:hidden;
                                    text-overflow:ellipsis;
                                ">
                                    {capture["nom"].upper()}
                                </div>

                                <div style="
                                    font-size:9px;
                                    color:{color};
                                    font-weight:900;
                                ">
                                    {capture["score"]}/10
                                </div>

                            </div>

                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                    if st.button(
                        "Voir",
                        key=f"open_{capture['id']}",
                        use_container_width=True
                    ):
                        show_specimen(capture)
