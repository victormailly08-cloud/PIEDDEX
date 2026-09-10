import streamlit as st
from supabase import create_client
from openai import OpenAI
from PIL import Image
import base64
import io
import json
import uuid
import time
from datetime import datetime


# ============================================================
# CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="PiedDex",
    page_icon="🦶",
    layout="wide",
    initial_sidebar_state="collapsed"
)

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

supabase = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)

OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
openai_client = OpenAI(api_key=OPENAI_API_KEY)

BUCKET_NAME = "pieddex-photos"
OPENAI_MODEL = "gpt-5.6-luna"


# ============================================================
# SESSION
# ============================================================

defaults = {
    "user_id": None,
    "user_email": None,
    "access_token": None,
    "refresh_token": None,
    "analysis_score": None,
    "analysis_name": None,
    "analysis_photo": None,
    "analysis_details": None,
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ============================================================
# STYLE GLOBAL
# ============================================================

st.markdown(
    """
<style>

/* ==========================================================
   PAGE
========================================================== */

html,
body {
    overflow-x: hidden !important;
    max-width: 100vw !important;
}

[data-testid="stAppViewContainer"] {

    overflow-x: hidden !important;
    -webkit-overflow-scrolling: touch !important;

    background:
        radial-gradient(
            circle at 50% -10%,
            #26365c 0%,
            #11182c 34%,
            #080c16 75%
        );
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


/* ==========================================================
   TITRES
========================================================== */

h1 {
    font-weight: 950 !important;
}

h2,
h3 {
    font-weight: 900 !important;
}


/* ==========================================================
   ONGLETS
========================================================== */

div[data-baseweb="tab-list"] {

    gap: 5px !important;

    padding: 4px !important;

    border-radius: 16px !important;

    background:
        rgba(13, 20, 36, 0.85) !important;

    border:
        1px solid rgba(255,255,255,0.09) !important;
}

button[data-baseweb="tab"] {

    font-weight: 850 !important;

    border-radius: 12px !important;

    min-height: 44px !important;
}


/* ==========================================================
   BOUTONS
========================================================== */

.stButton > button,
[data-testid="stFormSubmitButton"] > button {

    width: 100% !important;

    border-radius: 12px !important;

    font-weight: 850 !important;

    min-height: 42px !important;

    border:
        1px solid rgba(255,255,255,0.15) !important;

    background:
        linear-gradient(
            145deg,
            #304c82,
            #1d2e52
        ) !important;

    color: white !important;
}

.stButton > button:active {
    transform: scale(0.98);
}


/* ==========================================================
   INPUTS
========================================================== */

.stTextInput input {

    border-radius: 12px !important;

    background:
        rgba(7,12,24,0.70) !important;
}


/* ==========================================================
   MOBILE : GRILLE PIEDDEX SEULEMENT
========================================================== */

@media (max-width: 700px) {

    .block-container {

        padding-left: 9px !important;
        padding-right: 9px !important;
    }


    .st-key-collection_grid
    div[data-testid="stHorizontalBlock"] {

        display: grid !important;

        grid-template-columns:
            repeat(4, minmax(0, 1fr)) !important;

        gap: 6px !important;

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


    .st-key-collection_grid img {

        width: 100% !important;

        height: 72px !important;

        object-fit: cover !important;

        border-radius: 8px !important;
    }


    .st-key-collection_grid p {

        font-size: 9px !important;

        line-height: 1.05 !important;

        margin-top: 1px !important;
        margin-bottom: 1px !important;

        white-space: nowrap !important;

        overflow: hidden !important;

        text-overflow: ellipsis !important;
    }


    .st-key-collection_grid
    .stButton > button {

        min-height: 26px !important;

        height: 26px !important;

        font-size: 8px !important;

        padding: 0 1px !important;

        border-radius: 7px !important;
    }

}


/* ==========================================================
   DESKTOP
========================================================== */

@media (min-width: 701px) {

    .st-key-collection_grid img {

        height: 150px !important;

        width: 100% !important;

        object-fit: cover !important;

        border-radius: 10px !important;
    }
}

</style>
""",
    unsafe_allow_html=True
)


# ============================================================
# RARETÉS
# ============================================================

def clamp_score(value):
    """Force une note dans l'intervalle 0 à 10."""
    try:
        return max(0.0, min(10.0, float(value)))
    except Exception:
        return 0.0


def compress_image_for_ai(photo_bytes):
    """
    Version légère envoyée à l'IA :
    - côté max 512 px
    - JPEG qualité 72
    Cela réduit fortement les données envoyées et, avec detail='low',
    maintient le coût par analyse très bas.
    """
    image = Image.open(io.BytesIO(photo_bytes)).convert("RGB")
    image.thumbnail((512, 512))

    output = io.BytesIO()
    image.save(
        output,
        format="JPEG",
        quality=72,
        optimize=True
    )
    return output.getvalue()


def parse_json_response(text):
    cleaned = (text or "").strip()

    if cleaned.startswith("```"):
        cleaned = cleaned.replace("```json", "", 1)
        cleaned = cleaned.replace("```", "").strip()

    start = cleaned.find("{")
    end = cleaned.rfind("}")

    if start == -1 or end == -1:
        raise ValueError("Réponse IA non exploitable.")

    return json.loads(cleaned[start:end + 1])


def analyser_pied(photo_bytes):
    """
    Une seule requête IA par analyse.
    Le modèle reçoit une image compressée en basse définition,
    suffisante pour vérifier la présence d'un pied et noter les critères.
    """

    light_image = compress_image_for_ai(photo_bytes)
    image_b64 = base64.b64encode(light_image).decode("utf-8")

    prompt = """
Tu es le scanner visuel d'un jeu humoristique appelé PiedDex.

OBJECTIF 1 — VALIDATION
Vérifie d'abord que l'image montre clairement au moins un pied humain réel.
Un pied doit être suffisamment visible pour évaluer les orteils, les ongles,
la forme générale et l'état visuel. Refuse notamment :
- aucune présence de pied humain ;
- chaussure ou chaussette cachant l'essentiel du pied ;
- pied beaucoup trop petit dans l'image ;
- photo trop floue, trop sombre ou trop obstruée pour être évaluée.

Ne fais aucun diagnostic médical.
Ne déduis aucun âge, sexe, origine, identité ou information personnelle.
Évalue uniquement l'apparence visible du pied.

OBJECTIF 2 — NOTES SI LA PHOTO EST VALIDE
Attribue des notes de 0.0 à 10.0 avec une décimale :

soin_general :
impression visuelle de propreté et d'entretien.

ongles_pedicure :
coupe, régularité, propreté visuelle des ongles et pédicure visible.

harmonie :
équilibre visuel général, proportions apparentes et présentation du pied.

peau :
aspect visuel de la peau uniquement, sans interprétation médicale.

originalite :
caractère distinctif, atypique ou mémorable du spécimen.
Une note élevée signifie visuellement original, pas nécessairement plus beau.

qualite_photo :
netteté, luminosité, cadrage et visibilité suffisante pour juger le pied.

La note "esthétique" et l'"indice PiedDex" seront calculés ensuite par Python.
Ne les calcule pas toi-même.

Réponds UNIQUEMENT avec un objet JSON valide et très court.

Si invalide :
{
  "photo_valide": false,
  "raison": "raison courte",
  "soin_general": 0,
  "ongles_pedicure": 0,
  "harmonie": 0,
  "peau": 0,
  "originalite": 0,
  "qualite_photo": 0,
  "description": ""
}

Si valide :
{
  "photo_valide": true,
  "raison": "",
  "soin_general": 0.0,
  "ongles_pedicure": 0.0,
  "harmonie": 0.0,
  "peau": 0.0,
  "originalite": 0.0,
  "qualite_photo": 0.0,
  "description": "Une phrase PiedDex humoristique de moins de 18 mots."
}
"""

    response = openai_client.responses.create(
        model=OPENAI_MODEL,
        reasoning={"effort": "none"},
        text={"verbosity": "low"},
        max_output_tokens=250,
        store=False,
        input=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": prompt
                    },
                    {
                        "type": "input_image",
                        "image_url": f"data:image/jpeg;base64,{image_b64}",
                        "detail": "low"
                    }
                ]
            }
        ]
    )

    data = parse_json_response(response.output_text)

    if not bool(data.get("photo_valide", False)):
        return {
            "photo_valide": False,
            "raison": str(
                data.get(
                    "raison",
                    "Aucun pied exploitable n'a été détecté."
                )
            )
        }

    soin = clamp_score(data.get("soin_general"))
    ongles = clamp_score(data.get("ongles_pedicure"))
    harmonie = clamp_score(data.get("harmonie"))
    peau = clamp_score(data.get("peau"))
    originalite = clamp_score(data.get("originalite"))
    qualite = clamp_score(data.get("qualite_photo"))

    # Si l'IA voit bien un pied mais ne peut pas le juger correctement,
    # on préfère demander une nouvelle photo plutôt que donner une mauvaise note.
    if qualite < 4.0:
        return {
            "photo_valide": False,
            "raison": (
                "Le pied est détecté, mais la photo n'est pas assez nette "
                "ou bien cadrée. Reprends-la de plus près."
            )
        }

    # Esthétique : 4 critères visibles.
    esthetique = round(
        soin * 0.30
        + ongles * 0.25
        + harmonie * 0.25
        + peau * 0.20,
        1
    )

    # L'indice PiedDex garde l'esthétique majoritaire,
    # tout en récompensant les spécimens vraiment originaux.
    indice = round(
        esthetique * 0.70
        + originalite * 0.30,
        1
    )

    return {
        "photo_valide": True,
        "raison": "",
        "soin_general": round(soin, 1),
        "ongles_pedicure": round(ongles, 1),
        "harmonie": round(harmonie, 1),
        "peau": round(peau, 1),
        "originalite": round(originalite, 1),
        "qualite_photo": round(qualite, 1),
        "esthetique": esthetique,
        "indice_pieddex": indice,
        "description": str(data.get("description", "")).strip()
    }


def rarity_name(score):
    score = float(score)

    if score < 4.0:
        return "COMMUN"
    elif score < 6.0:
        return "PEU COMMUN"
    elif score < 7.5:
        return "RARE"
    elif score < 8.5:
        return "ÉPIQUE"
    elif score < 9.5:
        return "LÉGENDAIRE"
    return "MYTHIQUE"


def rarity_symbol(score):
    score = float(score)

    if score < 4.0:
        return "◇"
    elif score < 6.0:
        return "◆"
    elif score < 7.5:
        return "✦"
    elif score < 8.5:
        return "✦✦"
    elif score < 9.5:
        return "★"
    return "✺"


def rarity_style(score):
    score = float(score)

    if score < 4.0:
        return {
            "color": "#C7D0DF",
            "border": "#7F8A9D",
            "background": "#171C25",
            "glow": "rgba(190,205,225,0.22)"
        }
    elif score < 6.0:
        return {
            "color": "#68E29A",
            "border": "#3CBF75",
            "background": "#102319",
            "glow": "rgba(69,220,132,0.32)"
        }
    elif score < 7.5:
        return {
            "color": "#61B8FF",
            "border": "#398FE4",
            "background": "#0D2137",
            "glow": "rgba(61,165,255,0.40)"
        }
    elif score < 8.5:
        return {
            "color": "#C38AFF",
            "border": "#9B58E8",
            "background": "#24123B",
            "glow": "rgba(181,105,255,0.48)"
        }
    elif score < 9.5:
        return {
            "color": "#FFD45C",
            "border": "#DBA526",
            "background": "#34270C",
            "glow": "rgba(255,207,70,0.55)"
        }
    else:
        return {
            "color": "#FF79D2",
            "border": "#F047B6",
            "background": "#371129",
            "glow": "rgba(255,86,197,0.67)"
        }


def display_score(value):
    try:
        return f"{float(value):.1f}"
    except Exception:
        return "0.0"


def capture_index(capture):
    """
    Compatibilité avec les anciennes captures :
    si indice_pieddex n'existe pas encore, on reprend score.
    """
    value = capture.get("indice_pieddex")
    if value is None:
        value = capture.get("score", 0)
    return float(value or 0)


# ============================================================
# SESSION SUPABASE
# ============================================================

def save_auth_session(response):

    if not response:
        return False

    session = getattr(response, "session", None)
    user = getattr(response, "user", None)

    if session:

        st.session_state.access_token = session.access_token
        st.session_state.refresh_token = session.refresh_token

        if getattr(session, "user", None):
            user = session.user

    if user:

        st.session_state.user_id = str(user.id)
        st.session_state.user_email = user.email

    return bool(st.session_state.user_id)


def restore_auth_session():

    if (
        not st.session_state.access_token
        or not st.session_state.refresh_token
    ):
        return

    try:

        response = supabase.auth.set_session(
            st.session_state.access_token,
            st.session_state.refresh_token
        )

        save_auth_session(response)

    except Exception:

        st.session_state.user_id = None
        st.session_state.user_email = None
        st.session_state.access_token = None
        st.session_state.refresh_token = None


restore_auth_session()


# ============================================================
# SUPABASE : CAPTURES
# ============================================================

def get_captures():

    if not st.session_state.user_id:
        return []

    try:

        response = (
            supabase
            .table("captures")
            .select("*")
            .eq(
                "user_id",
                st.session_state.user_id
            )
            .order(
                "date_capture",
                desc=True
            )
            .execute()
        )

        return response.data or []

    except Exception as e:

        st.error(
            f"Impossible de charger ton PiedDex : {e}"
        )

        return []


def get_next_number():

    captures = get_captures()

    numbers = []

    for capture in captures:

        try:
            numbers.append(
                int(capture.get("numero", 0))
            )
        except:
            pass

    return max(numbers, default=0) + 1


def create_signed_photo_url(photo_path):

    if not photo_path:
        return None

    try:

        response = (
            supabase
            .storage
            .from_(BUCKET_NAME)
            .create_signed_url(
                photo_path,
                3600
            )
        )

        if isinstance(response, dict):

            return (
                response.get("signedURL")
                or response.get("signedUrl")
                or response.get("signed_url")
            )

        return None

    except Exception:

        return None


def save_capture(photo_bytes, name, analysis):

    user_id = st.session_state.user_id

    if not user_id:
        raise Exception("Utilisateur non connecté.")

    capture_uuid = uuid.uuid4().hex

    filename = (
        datetime.now().strftime("%Y%m%d_%H%M%S")
        + "_"
        + capture_uuid[:8]
        + ".jpg"
    )

    photo_path = f"{user_id}/{filename}"

    # On conserve la photo originale dans Supabase.
    (
        supabase
        .storage
        .from_(BUCKET_NAME)
        .upload(
            path=photo_path,
            file=photo_bytes,
            file_options={
                "content-type": "image/jpeg",
                "upsert": "false"
            }
        )
    )

    number = get_next_number()

    indice = float(analysis["indice_pieddex"])
    rarete = rarity_name(indice)

    # score reste un entier pour compatibilité avec ta colonne actuelle.
    # indice_pieddex garde la vraie note décimale (ex. 8.1).
    score_legacy = int(round(indice))

    try:
        (
            supabase
            .table("captures")
            .insert({
                "user_id": user_id,
                "numero": number,
                "nom": name,
                "score": score_legacy,
                "rarete": rarete,
                "photo_path": photo_path,
                "esthetique": analysis["esthetique"],
                "originalite": analysis["originalite"],
                "indice_pieddex": indice,
                "soin_general": analysis["soin_general"],
                "ongles_pedicure": analysis["ongles_pedicure"],
                "harmonie": analysis["harmonie"],
                "peau": analysis["peau"],
                "qualite_photo": analysis["qualite_photo"],
                "description": analysis["description"]
            })
            .execute()
        )

    except Exception:
        try:
            (
                supabase
                .storage
                .from_(BUCKET_NAME)
                .remove([photo_path])
            )
        except Exception:
            pass
        raise

def delete_capture(capture):

    capture_id = capture.get("id")
    photo_path = capture.get("photo_path")

    # --------------------------------------------------------
    # SUPPRESSION TABLE
    # --------------------------------------------------------

    (
        supabase
        .table("captures")
        .delete()
        .eq(
            "id",
            capture_id
        )
        .execute()
    )

    # --------------------------------------------------------
    # SUPPRESSION PHOTO
    # --------------------------------------------------------

    if photo_path:

        try:

            (
                supabase
                .storage
                .from_(BUCKET_NAME)
                .remove([
                    photo_path
                ])
            )

        except:
            pass


# ============================================================
# CSS DYNAMIQUE DES CARTES
# ============================================================

def inject_card_style(capture):

    style = rarity_style(
        capture_index(capture)
    )

    key = (
        f"card_{capture['id']}"
    )

    st.markdown(
        f"""
<style>

.st-key-{key} {{

    background:
        linear-gradient(
            145deg,
            {style["background"]},
            #090C12
        ) !important;

    border:
        1px solid
        {style["border"]} !important;

    border-radius:
        12px !important;

    padding:
        4px !important;

    box-shadow:
        0 0 12px
        {style["glow"]},
        0 7px 16px
        rgba(0,0,0,0.32) !important;
}}

.st-key-{key}
.stButton > button {{

    border-color:
        {style["border"]} !important;

    color:
        {style["color"]} !important;

    background:
        {style["background"]} !important;
}}

</style>
""",
        unsafe_allow_html=True
    )


def inject_analysis_style(score):

    style = rarity_style(score)

    st.markdown(
        f"""
<style>

.st-key-analysis_result {{

    background:
        radial-gradient(
            circle at 50% 10%,
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

    box-shadow:
        0 0 26px
        {style["glow"]},
        0 15px 30px
        rgba(0,0,0,0.40) !important;
}}


.st-key-analysis_result
[data-testid="stMetricValue"] {{

    color:
        {style["color"]} !important;

    font-weight:
        950 !important;

    text-shadow:
        0 0 13px
        {style["glow"]} !important;
}}


.st-key-analysis_result h3 {{

    color:
        {style["color"]} !important;
}}

</style>
""",
        unsafe_allow_html=True
    )


# ============================================================
# POPUP SPECIMEN
# ============================================================

@st.dialog(
    "Fiche du spécimen",
    width="large"
)
def show_specimen(capture):

    score = capture_index(capture)
    photo_url = create_signed_photo_url(
        capture.get("photo_path")
    )

    if photo_url:
        st.image(
            photo_url,
            width="stretch"
        )

    st.markdown(
        f"### #{int(capture.get('numero', 0)):03d} — "
        f"{capture.get('nom', 'Sans nom')}"
    )

    c1, c2, c3 = st.columns(3)

    with c1:
        st.metric(
            "Esthétique",
            f"{display_score(capture.get('esthetique', score))}/10"
        )

    with c2:
        st.metric(
            "Originalité",
            f"{display_score(capture.get('originalite', 0))}/10"
        )

    with c3:
        st.metric(
            "Indice PiedDex",
            f"{display_score(score)}/10"
        )

    st.markdown(
        f"### {rarity_symbol(score)} {rarity_name(score)}"
    )

    if capture.get("description"):
        st.info(capture["description"])

    detailed_values = [
        ("Soin général", capture.get("soin_general")),
        ("Ongles / pédicure", capture.get("ongles_pedicure")),
        ("Harmonie", capture.get("harmonie")),
        ("Peau", capture.get("peau")),
        ("Qualité photo", capture.get("qualite_photo")),
    ]

    if any(value is not None for _, value in detailed_values):
        st.write("#### Détail de l'analyse")

        for label, value in detailed_values:
            if value is not None:
                st.progress(
                    float(value) / 10,
                    text=f"{label} — {display_score(value)}/10"
                )

    date_capture = str(
        capture.get("date_capture", "")
    )

    if date_capture:
        st.caption(
            f"Capturé le {date_capture[:10]}"
        )

    st.divider()
    st.warning("La suppression est définitive.")

    if st.button(
        "🗑️ Supprimer ce spécimen",
        key=f"delete_{capture['id']}",
        width="stretch"
    ):
        try:
            delete_capture(capture)
            st.success("Spécimen supprimé.")
            time.sleep(0.5)
            st.rerun()

        except Exception as e:
            st.error(
                f"Suppression impossible : {e}"
            )


# ============================================================
# AUTHENTIFICATION
# ============================================================

def authentication_screen():

    st.title(
        "🦶 PIEDDEX"
    )

    st.caption(
        "Connecte-toi pour accéder à ton PiedDex personnel."
    )

    login_tab, register_tab = st.tabs(
        [
            "🔐 Connexion",
            "✨ Créer un compte"
        ]
    )


    # ========================================================
    # LOGIN
    # ========================================================

    with login_tab:

        with st.form(
            "login_form"
        ):

            email = st.text_input(
                "Email",
                placeholder="toi@email.fr"
            )

            password = st.text_input(
                "Mot de passe",
                type="password"
            )

            submit_login = (
                st.form_submit_button(
                    "SE CONNECTER",
                    width="stretch"
                )
            )

        if submit_login:

            if not email or not password:

                st.warning(
                    "Entre ton email et ton mot de passe."
                )

            else:

                try:

                    response = (
                        supabase.auth
                        .sign_in_with_password({
                            "email":
                                email.strip(),

                            "password":
                                password
                        })
                    )

                    save_auth_session(
                        response
                    )

                    st.success(
                        "Connexion réussie."
                    )

                    time.sleep(0.4)

                    st.rerun()

                except Exception:

                    st.error(
                        "Connexion impossible. "
                        "Vérifie ton email et ton mot de passe."
                    )


    # ========================================================
    # INSCRIPTION
    # ========================================================

    with register_tab:

        with st.form(
            "register_form"
        ):

            email_register = st.text_input(
                "Email",
                key="register_email"
            )

            password_register = st.text_input(
                "Mot de passe",
                type="password",
                key="register_password"
            )

            password_confirm = st.text_input(
                "Confirme le mot de passe",
                type="password",
                key="register_password_confirm"
            )

            submit_register = (
                st.form_submit_button(
                    "CRÉER MON COMPTE",
                    width="stretch"
                )
            )

        if submit_register:

            if (
                not email_register
                or not password_register
            ):

                st.warning(
                    "Remplis tous les champs."
                )

            elif len(
                password_register
            ) < 6:

                st.warning(
                    "Le mot de passe doit avoir "
                    "au moins 6 caractères."
                )

            elif (
                password_register
                != password_confirm
            ):

                st.warning(
                    "Les mots de passe ne correspondent pas."
                )

            else:

                try:

                    response = (
                        supabase.auth
                        .sign_up({
                            "email":
                                email_register.strip(),

                            "password":
                                password_register
                        })
                    )

                    if save_auth_session(
                        response
                    ):

                        st.success(
                            "Compte créé."
                        )

                        time.sleep(0.5)

                        st.rerun()

                    else:

                        st.success(
                            "Compte créé. "
                            "Vérifie ton email avant "
                            "de te connecter si la "
                            "confirmation email est activée."
                        )

                except Exception as e:

                    st.error(
                        f"Création du compte impossible : {e}"
                    )


# ============================================================
# SI PAS CONNECTÉ
# ============================================================

if not st.session_state.user_id:

    authentication_screen()

    st.stop()


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
# UTILISATEUR + DECONNEXION
# ============================================================

user_col, logout_col = st.columns(
    [3, 1]
)

with user_col:

    st.caption(
        f"🟢 {st.session_state.user_email}"
    )

with logout_col:

    if st.button(
        "Déconnexion",
        width="stretch"
    ):

        try:
            supabase.auth.sign_out()
        except:
            pass

        for key in defaults:
            st.session_state[key] = defaults[key]

        st.rerun()


# ============================================================
# ONGLETS
# ============================================================

tab_capture, tab_collection, tab_profile = st.tabs(
    [
        "📸 CAPTURER",
        "📚 MON PIEDDEX",
        "👤 PROFIL"
    ]
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
            caption="Spécimen détecté",
            width="stretch"
        )

        nom = st.text_input(
            "Nom du spécimen",
            placeholder="Ex : Piedouille"
        )

        if st.button(
            "🔍 ANALYSER LE SPÉCIMEN",
            width="stretch"
        ):

            if not nom.strip():
                st.warning(
                    "Entre d'abord le nom du spécimen."
                )

            else:
                try:
                    with st.spinner(
                        "🔬 Analyse visuelle réelle du spécimen..."
                    ):
                        analysis = analyser_pied(
                            photo.getvalue()
                        )

                    if not analysis.get("photo_valide"):
                        st.session_state.analysis_score = None
                        st.session_state.analysis_name = None
                        st.session_state.analysis_photo = None
                        st.session_state.analysis_details = None

                        st.error(
                            "❌ Capture refusée : "
                            + analysis.get(
                                "raison",
                                "Aucun pied exploitable détecté."
                            )
                        )

                    else:
                        st.session_state.analysis_score = (
                            analysis["indice_pieddex"]
                        )
                        st.session_state.analysis_name = nom.strip()
                        st.session_state.analysis_photo = photo.getvalue()
                        st.session_state.analysis_details = analysis

                except Exception as e:
                    st.error(
                        "L'analyse IA a échoué. "
                        f"Détail : {e}"
                    )

        # ====================================================
        # RESULTAT ANALYSE
        # ====================================================

        if (
            st.session_state.analysis_score is not None
            and st.session_state.analysis_photo is not None
            and st.session_state.analysis_details is not None
        ):

            score = float(
                st.session_state.analysis_score
            )
            name = st.session_state.analysis_name
            analysis = st.session_state.analysis_details

            inject_analysis_style(score)

            with st.container(
                key="analysis_result"
            ):

                st.caption("ANALYSE TERMINÉE")

                st.subheader(
                    f"{rarity_symbol(score)} {name.upper()}"
                )

                a1, a2 = st.columns(2)

                with a1:
                    st.metric(
                        "Esthétique",
                        f"{analysis['esthetique']:.1f}/10"
                    )

                with a2:
                    st.metric(
                        "Originalité",
                        f"{analysis['originalite']:.1f}/10"
                    )

                st.metric(
                    "INDICE PIEDDEX",
                    f"{score:.1f}/10"
                )

                st.markdown(
                    f"### {rarity_symbol(score)} {rarity_name(score)}"
                )

                if analysis.get("description"):
                    st.info(
                        analysis["description"]
                    )

                st.write("#### Analyse détaillée")

                st.progress(
                    analysis["soin_general"] / 10,
                    text=(
                        "Soin général — "
                        f"{analysis['soin_general']:.1f}/10"
                    )
                )

                st.progress(
                    analysis["ongles_pedicure"] / 10,
                    text=(
                        "Ongles / pédicure — "
                        f"{analysis['ongles_pedicure']:.1f}/10"
                    )
                )

                st.progress(
                    analysis["harmonie"] / 10,
                    text=(
                        "Harmonie — "
                        f"{analysis['harmonie']:.1f}/10"
                    )
                )

                st.progress(
                    analysis["peau"] / 10,
                    text=(
                        "Aspect de la peau — "
                        f"{analysis['peau']:.1f}/10"
                    )
                )

                st.caption(
                    "Qualité de la photo : "
                    f"{analysis['qualite_photo']:.1f}/10"
                )

                if st.button(
                    "💾 AJOUTER À MON PIEDDEX",
                    type="primary",
                    width="stretch"
                ):
                    try:
                        with st.spinner(
                            "Enregistrement..."
                        ):
                            save_capture(
                                st.session_state.analysis_photo,
                                st.session_state.analysis_name,
                                st.session_state.analysis_details
                            )

                        if score >= 9.5:
                            st.balloons()

                        st.session_state.analysis_score = None
                        st.session_state.analysis_name = None
                        st.session_state.analysis_photo = None
                        st.session_state.analysis_details = None

                        st.success(
                            "✨ Spécimen ajouté au PiedDex !"
                        )

                        time.sleep(0.6)
                        st.rerun()

                    except Exception as e:
                        st.error(
                            f"Impossible d'enregistrer : {e}"
                        )


# ============================================================
# MON PIEDDEX
# ============================================================

with tab_collection:

    captures = get_captures()

    st.subheader("Ma collection")
    st.caption(
        f"{len(captures)} spécimen(s) découvert(s)"
    )

    if not captures:
        st.info(
            "Ton PiedDex est vide pour le moment."
        )

    else:
        sort_option = st.selectbox(
            "Trier",
            [
                "Plus récentes",
                "Plus anciennes",
                "Rareté décroissante",
                "Rareté croissante"
            ]
        )

        if sort_option == "Plus anciennes":
            captures = list(
                reversed(captures)
            )

        elif sort_option == "Rareté décroissante":
            captures = sorted(
                captures,
                key=capture_index,
                reverse=True
            )

        elif sort_option == "Rareté croissante":
            captures = sorted(
                captures,
                key=capture_index
            )

        st.divider()

        # ====================================================
        # GRILLE 4 PAR LIGNE
        # ====================================================

        with st.container(
            key="collection_grid"
        ):

            for i in range(
                0,
                len(captures),
                4
            ):

                row = captures[i:i + 4]

                cols = st.columns(
                    4,
                    gap="small"
                )

                for index, col in enumerate(cols):

                    if index >= len(row):
                        continue

                    capture = row[index]
                    score = capture_index(capture)

                    inject_card_style(capture)

                    with col:

                        card_key = (
                            f"card_{capture['id']}"
                        )

                        with st.container(
                            key=card_key,
                            border=True
                        ):

                            photo_url = (
                                create_signed_photo_url(
                                    capture.get(
                                        "photo_path"
                                    )
                                )
                            )

                            if photo_url:
                                st.image(
                                    photo_url,
                                    width="stretch"
                                )

                            st.caption(
                                f"#{int(capture.get('numero', 0)):03d}"
                            )

                            st.markdown(
                                f"**{capture.get('nom', 'Sans nom')}**"
                            )

                            st.markdown(
                                f"**{rarity_symbol(score)} "
                                f"{score:.1f}/10**"
                            )

                            if st.button(
                                "Voir",
                                key=f"view_{capture['id']}",
                                width="stretch"
                            ):
                                show_specimen(
                                    capture
                                )


# ============================================================
# PROFIL
# ============================================================

with tab_profile:

    captures = get_captures()

    st.subheader("👤 Mon profil")

    st.write(
        f"**Compte :** {st.session_state.user_email}"
    )

    total = len(captures)

    if captures:
        scores = [
            capture_index(capture)
            for capture in captures
        ]

        best_score = max(scores)
        average_score = (
            sum(scores) / len(scores)
        )
    else:
        best_score = 0
        average_score = 0

    c1, c2, c3 = st.columns(3)

    with c1:
        st.metric(
            "Captures",
            total
        )

    with c2:
        st.metric(
            "Moyenne",
            f"{average_score:.1f}/10"
        )

    with c3:
        st.metric(
            "Record",
            f"{best_score:.1f}/10"
        )

    st.divider()

    common_count = sum(
        1 for c in captures
        if capture_index(c) < 4.0
    )

    uncommon_count = sum(
        1 for c in captures
        if 4.0 <= capture_index(c) < 6.0
    )

    rare_count = sum(
        1 for c in captures
        if 6.0 <= capture_index(c) < 7.5
    )

    epic_count = sum(
        1 for c in captures
        if 7.5 <= capture_index(c) < 8.5
    )

    legendary_count = sum(
        1 for c in captures
        if 8.5 <= capture_index(c) < 9.5
    )

    mythic_count = sum(
        1 for c in captures
        if capture_index(c) >= 9.5
    )

    st.write(
        f"◇ **Communs :** {common_count}"
    )

    st.write(
        f"◆ **Peu communs :** {uncommon_count}"
    )

    st.write(
        f"✦ **Rares :** {rare_count}"
    )

    st.write(
        f"💜 **Épiques :** {epic_count}"
    )

    st.write(
        f"⭐ **Légendaires :** {legendary_count}"
    )

    st.write(
        f"🌟 **Mythiques :** {mythic_count}"
    )

    st.divider()

    if st.button(
        "🚪 SE DÉCONNECTER",
        key="logout_profile",
        width="stretch"
    ):

        try:
            supabase.auth.sign_out()
        except Exception:
            pass

        for key in defaults:
            st.session_state[key] = defaults[key]

        st.rerun()
