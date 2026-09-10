import streamlit as st
from supabase import create_client
from openai import OpenAI
from PIL import Image, ImageOps
import base64
import io
import json
import re
import time
import uuid
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
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
openai_client = OpenAI(api_key=OPENAI_API_KEY)

BUCKET_NAME = "pieddex-photos"
VISION_MODEL = "gpt-5.6-luna"


# ============================================================
# SESSION
# ============================================================

defaults = {
    "user_id": None,
    "user_email": None,
    "access_token": None,
    "refresh_token": None,
    "analysis_name": None,
    "analysis_photo": None,
    "analysis_data": None,
    "analysis_error": None,
    "profile_pseudo": None,
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
html, body {
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

#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
header { background: transparent !important; }

h1 { font-weight: 950 !important; }
h2, h3 { font-weight: 900 !important; }

div[data-baseweb="tab-list"] {
    gap: 5px !important;
    padding: 4px !important;
    border-radius: 16px !important;
    background: rgba(13, 20, 36, 0.85) !important;
    border: 1px solid rgba(255,255,255,0.09) !important;
}

button[data-baseweb="tab"] {
    font-weight: 850 !important;
    border-radius: 12px !important;
    min-height: 44px !important;
}

.stButton > button,
[data-testid="stFormSubmitButton"] > button {
    width: 100% !important;
    border-radius: 12px !important;
    font-weight: 850 !important;
    min-height: 42px !important;
    border: 1px solid rgba(255,255,255,0.15) !important;
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

.stTextInput input {
    border-radius: 12px !important;
    background: rgba(7,12,24,0.70) !important;
}

.st-key-analysis_result {
    border-radius: 20px !important;
    padding: 16px !important;
}

/* Seulement la grille du PiedDex sur mobile */
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

    .st-key-collection_grid .stButton > button {
        min-height: 26px !important;
        height: 26px !important;
        font-size: 8px !important;
        padding: 0 1px !important;
        border-radius: 7px !important;
    }
}

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
# OUTILS DE NOTATION
# ============================================================

def clamp_score(value):
    try:
        return round(max(0.0, min(10.0, float(value))), 1)
    except (TypeError, ValueError):
        return 0.0


def capture_index(capture):
    """Nouvelle note décimale si disponible, sinon ancienne colonne score."""
    value = capture.get("indice_pieddex")
    if value is None:
        value = capture.get("score", 0)
    return clamp_score(value)


def calculate_esthetic(data):
    """
    Esthétique :
    30 % soin général
    30 % ongles / pédicure
    25 % harmonie visuelle
    15 % aspect visible de la peau
    """
    soin = clamp_score(data["soin_general"])
    ongles = clamp_score(data["ongles_pedicure"])
    harmonie = clamp_score(data["harmonie"])
    peau = clamp_score(data["peau"])

    esthetique = (
        soin * 0.30
        + ongles * 0.30
        + harmonie * 0.25
        + peau * 0.15
    )

    # Plafonds anti-inflation
    if min(soin, ongles, harmonie, peau) < 4.0:
        esthetique = min(esthetique, 6.4)

    if ongles < 5.0 or soin < 5.0:
        esthetique = min(esthetique, 7.0)

    high_criteria = sum(
        score >= 8.5
        for score in [soin, ongles, harmonie, peau]
    )
    if high_criteria < 3:
        esthetique = min(esthetique, 8.4)

    return round(esthetique, 1)


def calculate_index(esthetique, originalite):
    return round(
        clamp_score(esthetique) * 0.70
        + clamp_score(originalite) * 0.30,
        1
    )


def rarity_name(indice, analysis=None):
    """
    Barème volontairement strict.
    """
    indice = clamp_score(indice)

    if indice < 6.0:
        return "COMMUN"

    if indice < 7.0:
        return "PEU COMMUN"

    if indice < 7.8:
        return "RARE"

    if indice < 8.5:
        return "ÉPIQUE"

    if indice < 9.2:
        if analysis:
            esth = clamp_score(analysis.get("esthetique", 0))
            orig = clamp_score(analysis.get("originalite", 0))
            if esth < 8.2 and orig < 9.0:
                return "ÉPIQUE"
        return "LÉGENDAIRE"

    if analysis:
        esth = clamp_score(analysis.get("esthetique", 0))
        orig = clamp_score(analysis.get("originalite", 0))
        minimum_visual = min(
            clamp_score(analysis.get("soin_general", 0)),
            clamp_score(analysis.get("ongles_pedicure", 0)),
            clamp_score(analysis.get("harmonie", 0)),
            clamp_score(analysis.get("peau", 0)),
        )
        if esth < 9.0 or orig < 9.0 or minimum_visual < 8.3:
            return "LÉGENDAIRE"

    return "MYTHIQUE"


def rarity_symbol_from_name(name):
    return {
        "COMMUN": "◇",
        "PEU COMMUN": "◆",
        "RARE": "✦",
        "ÉPIQUE": "✦✦",
        "LÉGENDAIRE": "★",
        "MYTHIQUE": "✺",
    }.get(name, "◇")


def rarity_symbol(indice, analysis=None):
    return rarity_symbol_from_name(
        rarity_name(indice, analysis)
    )


def rarity_style(indice, analysis=None):
    rarete = rarity_name(indice, analysis)

    styles = {
        "COMMUN": {
            "color": "#C7D0DF",
            "border": "#7F8A9D",
            "background": "#171C25",
            "glow": "rgba(190,205,225,0.22)",
        },
        "PEU COMMUN": {
            "color": "#68E29A",
            "border": "#3CBF75",
            "background": "#102319",
            "glow": "rgba(69,220,132,0.32)",
        },
        "RARE": {
            "color": "#61B8FF",
            "border": "#398FE4",
            "background": "#0D2137",
            "glow": "rgba(61,165,255,0.40)",
        },
        "ÉPIQUE": {
            "color": "#C38AFF",
            "border": "#9B58E8",
            "background": "#24123B",
            "glow": "rgba(181,105,255,0.48)",
        },
        "LÉGENDAIRE": {
            "color": "#FFD45C",
            "border": "#DBA526",
            "background": "#34270C",
            "glow": "rgba(255,207,70,0.55)",
        },
        "MYTHIQUE": {
            "color": "#FF79D2",
            "border": "#F047B6",
            "background": "#371129",
            "glow": "rgba(255,86,197,0.67)",
        },
    }

    return styles[rarete]


# ============================================================
# ANALYSE IA — COÛT MINIMAL
# ============================================================

def prepare_image_for_ai(photo_bytes):
    """
    Réduction forte avant l'appel API :
    orientation corrigée, RGB, max 512x512, JPEG qualité 70.
    """
    image = Image.open(io.BytesIO(photo_bytes))
    image = ImageOps.exif_transpose(image).convert("RGB")
    image.thumbnail((512, 512))

    buffer = io.BytesIO()
    image.save(
        buffer,
        format="JPEG",
        quality=70,
        optimize=True
    )
    return buffer.getvalue()


def parse_json_response(text):
    text = (text or "").strip()

    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.I)
        text = re.sub(r"\s*```$", "", text)

    return json.loads(text)


def analyse_pied(photo_bytes):
    """
    Un seul appel vision.
    L'IA note les critères ; Python calcule la note finale.
    """
    compressed = prepare_image_for_ai(photo_bytes)
    encoded = base64.b64encode(compressed).decode("utf-8")

    prompt = """
Tu es le scanner visuel d'un jeu humoristique appelé PiedDex.

TA MISSION EST STRICTE ET EN DEUX TEMPS.

1) VALIDATION DE LA PHOTO
Vérifie si l'image montre clairement au moins un pied humain réel, découvert,
suffisamment grand dans l'image et suffisamment net pour être évalué.

Retourne photo_valide=false si :
- aucun pied humain n'est visible ;
- on voit seulement une chaussure ou une chaussette qui cache le pied ;
- le pied est trop petit, trop flou, trop sombre ou largement masqué ;
- l'image ne permet pas de juger les critères visuels.

Si aucun pied n'est détecté, type_refus doit être "pas_de_pied".
Si un pied existe mais que la photo est inexploitable, type_refus doit être
"mauvaise_photo".

2) NOTATION SI LA PHOTO EST VALIDE
Note UNIQUEMENT ce qui est réellement visible, sans diagnostic médical,
sans déduire l'âge, l'identité, l'origine, le sexe ou toute autre information
personnelle.

Attribue une note de 0.0 à 10.0 à :
- soin_general : impression visuelle de propreté et de soin ;
- ongles_pedicure : coupe, régularité, entretien et présentation visible des ongles ;
- harmonie : équilibre visuel du pied et des orteils, régularité d'ensemble ;
- peau : aspect visuel général de la peau uniquement, sans diagnostic ;
- originalite : caractère visuellement distinctif non médical ;
- qualite_photo : netteté, cadrage, lumière et visibilité.

CALIBRATION OBLIGATOIRE :
5/10 = pied ordinaire / moyen sur ce critère.
6/10 = légèrement au-dessus de la moyenne.
7/10 = clairement remarquable.
8/10 = exceptionnel.
9/10 = extrêmement remarquable et peu courant.
10/10 = quasi parfait sur le critère ; à utiliser exceptionnellement.

Ne sois PAS généreux par défaut.
Une photo correcte d'un pied normal et propre ne doit pas recevoir 8 ou 9.
La majorité des pieds ordinaires doivent se situer environ entre 4.5 et 6.5
sur les critères esthétiques.
L'originalité ne signifie pas "beau" : un pied très classique doit rester
autour de 4-5 en originalité même s'il est très bien entretenu.
N'augmente jamais l'originalité à cause d'une anomalie médicale supposée.

Réponds UNIQUEMENT avec un objet JSON valide, sans markdown.

Si invalide :
{
  "photo_valide": false,
  "type_refus": "pas_de_pied",
  "raison": "courte raison en français"
}

Si valide :
{
  "photo_valide": true,
  "type_refus": null,
  "soin_general": 0.0,
  "ongles_pedicure": 0.0,
  "harmonie": 0.0,
  "peau": 0.0,
  "originalite": 0.0,
  "qualite_photo": 0.0,
  "description": "une phrase courte, amusante mais non insultante"
}
"""

    response = openai_client.responses.create(
        model=VISION_MODEL,
        reasoning={"effort": "none"},
        max_output_tokens=300,
        store=False,
        input=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": prompt,
                    },
                    {
                        "type": "input_image",
                        "image_url": f"data:image/jpeg;base64,{encoded}",
                        "detail": "low",
                    },
                ],
            }
        ],
    )

    data = parse_json_response(response.output_text)

    if not data.get("photo_valide", False):
        return {
            "photo_valide": False,
            "type_refus": data.get("type_refus", "pas_de_pied"),
            "raison": data.get(
                "raison",
                "Le scanner ne peut pas analyser cette capture."
            ),
        }

    for key in [
        "soin_general",
        "ongles_pedicure",
        "harmonie",
        "peau",
        "originalite",
        "qualite_photo",
    ]:
        data[key] = clamp_score(data.get(key, 0))

    if data["qualite_photo"] < 4.5:
        return {
            "photo_valide": False,
            "type_refus": "mauvaise_photo",
            "raison": "Le pied est visible mais la capture n'est pas assez nette ou bien cadrée.",
        }

    data["esthetique"] = calculate_esthetic(data)
    data["indice_pieddex"] = calculate_index(
        data["esthetique"],
        data["originalite"]
    )
    data["rarete"] = rarity_name(
        data["indice_pieddex"],
        data
    )

    description = str(data.get("description", "")).strip()
    if not description:
        description = "Un spécimen désormais répertorié dans le PiedDex."
    data["description"] = description[:220]

    return data


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
            .eq("user_id", st.session_state.user_id)
            .order("date_capture", desc=True)
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
        except (TypeError, ValueError):
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
    indice = clamp_score(analysis["indice_pieddex"])
    rarete = analysis["rarete"]

    try:
        (
            supabase
            .table("captures")
            .insert({
                "user_id": user_id,
                "numero": number,
                "nom": name,
                "score": int(round(indice)),
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
                "description": analysis["description"],
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

    (
        supabase
        .table("captures")
        .delete()
        .eq("id", capture_id)
        .execute()
    )

    if photo_path:
        try:
            (
                supabase
                .storage
                .from_(BUCKET_NAME)
                .remove([photo_path])
            )
        except Exception:
            pass



# ============================================================
# PROFILS + AMIS
# ============================================================

def get_my_profile():
    if not st.session_state.user_id:
        return None

    try:
        response = (
            supabase
            .table("profiles")
            .select("user_id,pseudo,avatar_url,created_at")
            .eq("user_id", st.session_state.user_id)
            .limit(1)
            .execute()
        )

        if response.data:
            profile = response.data[0]
            st.session_state.profile_pseudo = profile.get("pseudo")
            return profile

        st.session_state.profile_pseudo = None
        return None

    except Exception as e:
        st.error(f"Impossible de charger ton profil : {e}")
        return None


def create_my_profile(pseudo):
    pseudo = pseudo.strip()

    if len(pseudo) < 3:
        raise ValueError("Le pseudo doit contenir au moins 3 caractères.")

    if len(pseudo) > 24:
        raise ValueError("Le pseudo doit contenir au maximum 24 caractères.")

    if not re.fullmatch(r"[A-Za-zÀ-ÿ0-9_\- ]+", pseudo):
        raise ValueError(
            "Utilise seulement des lettres, chiffres, espaces, _ ou -."
        )

    response = (
        supabase
        .table("profiles")
        .insert({
            "user_id": st.session_state.user_id,
            "pseudo": pseudo,
        })
        .execute()
    )

    st.session_state.profile_pseudo = pseudo
    return response.data


def update_my_pseudo(new_pseudo):
    new_pseudo = new_pseudo.strip()

    if len(new_pseudo) < 3:
        raise ValueError("Le pseudo doit contenir au moins 3 caractères.")

    if len(new_pseudo) > 24:
        raise ValueError("Le pseudo doit contenir au maximum 24 caractères.")

    if not re.fullmatch(r"[A-Za-zÀ-ÿ0-9_\- ]+", new_pseudo):
        raise ValueError(
            "Utilise seulement des lettres, chiffres, espaces, _ ou -."
        )

    (
        supabase
        .table("profiles")
        .update({"pseudo": new_pseudo})
        .eq("user_id", st.session_state.user_id)
        .execute()
    )

    st.session_state.profile_pseudo = new_pseudo


def search_profiles(query):
    query = query.strip()

    if len(query) < 2:
        return []

    try:
        response = (
            supabase
            .table("profiles")
            .select("user_id,pseudo")
            .ilike("pseudo", f"%{query}%")
            .neq("user_id", st.session_state.user_id)
            .limit(12)
            .execute()
        )
        return response.data or []

    except Exception as e:
        st.error(f"Recherche impossible : {e}")
        return []


def get_friendships():
    try:
        response = (
            supabase
            .table("friendships")
            .select("id,requester_id,addressee_id,status,created_at")
            .order("created_at", desc=True)
            .execute()
        )
        return response.data or []

    except Exception as e:
        st.error(f"Impossible de charger les amis : {e}")
        return []


def get_profiles_map(user_ids):
    ids = list({str(uid) for uid in user_ids if uid})

    if not ids:
        return {}

    try:
        response = (
            supabase
            .table("profiles")
            .select("user_id,pseudo")
            .in_("user_id", ids)
            .execute()
        )

        return {
            str(p["user_id"]): p.get("pseudo", "Joueur")
            for p in (response.data or [])
        }

    except Exception:
        return {}


def relationship_with(other_user_id, friendships=None):
    uid = st.session_state.user_id
    friendships = friendships if friendships is not None else get_friendships()

    for relation in friendships:
        requester = str(relation.get("requester_id"))
        addressee = str(relation.get("addressee_id"))

        if (
            (requester == uid and addressee == other_user_id)
            or
            (requester == other_user_id and addressee == uid)
        ):
            return relation

    return None


def send_friend_request(addressee_id):
    if addressee_id == st.session_state.user_id:
        raise ValueError("Tu ne peux pas t'ajouter toi-même.")

    existing = relationship_with(addressee_id)

    if existing:
        status = existing.get("status")

        if status == "accepted":
            raise ValueError("Vous êtes déjà amis.")

        if status == "pending":
            raise ValueError("Une demande existe déjà.")

        try:
            (
                supabase
                .table("friendships")
                .delete()
                .eq("id", existing["id"])
                .execute()
            )
        except Exception:
            pass

    (
        supabase
        .table("friendships")
        .insert({
            "requester_id": st.session_state.user_id,
            "addressee_id": addressee_id,
            "status": "pending",
        })
        .execute()
    )


def accept_friend_request(friendship_id):
    (
        supabase
        .table("friendships")
        .update({"status": "accepted"})
        .eq("id", friendship_id)
        .eq("addressee_id", st.session_state.user_id)
        .execute()
    )


def reject_friend_request(friendship_id):
    (
        supabase
        .table("friendships")
        .delete()
        .eq("id", friendship_id)
        .eq("addressee_id", st.session_state.user_id)
        .execute()
    )


def cancel_friend_request(friendship_id):
    (
        supabase
        .table("friendships")
        .delete()
        .eq("id", friendship_id)
        .eq("requester_id", st.session_state.user_id)
        .execute()
    )


def remove_friend(friendship_id):
    (
        supabase
        .table("friendships")
        .delete()
        .eq("id", friendship_id)
        .execute()
    )


def split_friendships(friendships):
    uid = st.session_state.user_id

    incoming = []
    outgoing = []
    accepted = []

    for relation in friendships:
        status = relation.get("status")
        requester = str(relation.get("requester_id"))
        addressee = str(relation.get("addressee_id"))

        if status == "accepted":
            accepted.append(relation)

        elif status == "pending" and addressee == uid:
            incoming.append(relation)

        elif status == "pending" and requester == uid:
            outgoing.append(relation)

    return incoming, outgoing, accepted


def friend_other_user_id(relation):
    uid = st.session_state.user_id
    requester = str(relation.get("requester_id"))
    addressee = str(relation.get("addressee_id"))

    return addressee if requester == uid else requester


def require_profile():
    profile = get_my_profile()

    if profile:
        return profile

    st.title("🦶 PIEDDEX")
    st.subheader("Choisis ton pseudo")
    st.write(
        "Avant d'entrer dans PiedDex, choisis le nom sous lequel "
        "tes amis pourront te trouver."
    )

    with st.form("first_profile_form"):
        pseudo = st.text_input(
            "Pseudo",
            placeholder="Ex : PiedMaster31",
            max_chars=24
        )

        create = st.form_submit_button(
            "CRÉER MON PROFIL",
            width="stretch"
        )

    if create:
        try:
            create_my_profile(pseudo)
            st.success("Profil créé !")
            time.sleep(0.4)
            st.rerun()

        except Exception as e:
            message = str(e)

            if "duplicate" in message.lower() or "unique" in message.lower():
                st.error(
                    "Ce pseudo est déjà pris. Choisis-en un autre."
                )
            else:
                st.error(message)

    st.stop()



# ============================================================
# CLASSEMENT ENTRE AMIS
# ============================================================

def get_friend_leaderboard():
    """
    Appelle la fonction SQL sécurisée Supabase.
    Elle renvoie uniquement les statistiques de moi + mes amis acceptés,
    sans exposer leurs captures ni leurs photos.
    """
    try:
        response = (
            supabase
            .rpc("get_friend_leaderboard")
            .execute()
        )

        rows = response.data or []

        # Normalisation utile pour l'affichage Streamlit
        for row in rows:
            row["total_captures"] = int(row.get("total_captures") or 0)
            row["score_pieddex"] = int(row.get("score_pieddex") or 0)
            row["moyenne"] = float(row.get("moyenne") or 0)
            row["meilleur"] = float(row.get("meilleur") or 0)
            row["moyenne_esthetique"] = float(
                row.get("moyenne_esthetique") or 0
            )
            row["moyenne_originalite"] = float(
                row.get("moyenne_originalite") or 0
            )

        return rows

    except Exception as e:
        st.error(
            "Impossible de charger le classement. "
            "Vérifie que la fonction SQL get_friend_leaderboard "
            f"a bien été créée dans Supabase. Détail : {e}"
        )
        return []


def medal_for_rank(rank):
    return {
        1: "🥇",
        2: "🥈",
        3: "🥉",
    }.get(rank, f"#{rank}")


@st.dialog(
    "Statistiques du joueur",
    width="large"
)
def show_player_stats(player, rank, total_players):
    pseudo = player.get("pseudo", "Joueur")
    is_me = str(player.get("user_id")) == st.session_state.user_id

    st.markdown(
        f"## {'👤' if not is_me else '⭐'} @{pseudo}"
    )

    if is_me:
        st.caption("C'est toi.")

    st.markdown(
        f"### {medal_for_rank(rank)} "
        f"{rank}e sur {total_players}"
        if rank > 1
        else f"### 🥇 1er sur {total_players}"
    )

    st.metric(
        "🏆 Points PiedDex",
        f"{player['score_pieddex']} pts"
    )

    c1, c2 = st.columns(2)

    with c1:
        st.metric(
            "Spécimens capturés",
            player["total_captures"]
        )
        st.metric(
            "Indice moyen",
            f"{player['moyenne']:.1f}/10"
        )

    with c2:
        st.metric(
            "Meilleur spécimen",
            f"{player['meilleur']:.1f}/10"
        )
        st.metric(
            "Esthétique moyenne",
            f"{player['moyenne_esthetique']:.1f}/10"
        )

    st.metric(
        "Originalité moyenne",
        f"{player['moyenne_originalite']:.1f}/10"
    )

    st.divider()

    st.caption(
        "Barème : Commun 0 · Peu commun 1 · Rare 15 · "
        "Épique 50 · Légendaire 150 · Mythique 500"
    )


# ============================================================
# CSS DYNAMIQUE
# ============================================================

def inject_card_style(capture):
    indice = capture_index(capture)
    style = rarity_style(indice)
    key = f"card_{capture['id']}"

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
        1px solid {style["border"]} !important;
    border-radius:
        12px !important;
    padding:
        4px !important;
    box-shadow:
        0 0 12px {style["glow"]},
        0 7px 16px rgba(0,0,0,0.32) !important;
}}

.st-key-{key} .stButton > button {{
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


def inject_analysis_style(indice, analysis=None):
    style = rarity_style(indice, analysis)

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
        2px solid {style["border"]} !important;
    border-radius:
        22px !important;
    padding:
        18px !important;
    box-shadow:
        0 0 26px {style["glow"]},
        0 15px 30px rgba(0,0,0,0.40) !important;
}}

.st-key-analysis_result [data-testid="stMetricValue"] {{
    color:
        {style["color"]} !important;
    font-weight:
        950 !important;
    text-shadow:
        0 0 13px {style["glow"]} !important;
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
    indice = capture_index(capture)
    rarete = capture.get("rarete") or rarity_name(indice)

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
            "Indice PiedDex",
            f"{indice:.1f}/10"
        )

    with c2:
        esth = capture.get("esthetique")
        st.metric(
            "Esthétique",
            f"{float(esth):.1f}/10" if esth is not None else "—"
        )

    with c3:
        orig = capture.get("originalite")
        st.metric(
            "Originalité",
            f"{float(orig):.1f}/10" if orig is not None else "—"
        )

    st.markdown(
        f"**{rarity_symbol_from_name(rarete)} {rarete}**"
    )

    if capture.get("description"):
        st.write(capture["description"])

    if capture.get("soin_general") is not None:
        with st.expander("🔎 Détails de l'analyse"):
            d1, d2 = st.columns(2)

            with d1:
                st.metric(
                    "Soin général",
                    f"{float(capture['soin_general']):.1f}/10"
                )
                st.metric(
                    "Ongles / pédicure",
                    f"{float(capture['ongles_pedicure']):.1f}/10"
                )

            with d2:
                st.metric(
                    "Harmonie",
                    f"{float(capture['harmonie']):.1f}/10"
                )
                st.metric(
                    "Aspect peau",
                    f"{float(capture['peau']):.1f}/10"
                )

            st.caption(
                f"Qualité de la capture : "
                f"{float(capture.get('qualite_photo', 0)):.1f}/10"
            )

    date_capture = str(
        capture.get("date_capture", "")
    )

    if date_capture:
        st.caption(
            f"Capturé le {date_capture[:10]}"
        )

    st.divider()

    st.warning(
        "La suppression est définitive."
    )

    if st.button(
        "🗑️ Supprimer ce spécimen",
        key=f"delete_{capture['id']}",
        width="stretch"
    ):
        try:
            delete_capture(capture)

            st.success(
                "Spécimen supprimé."
            )

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
    st.title("🦶 PIEDDEX")

    st.caption(
        "Connecte-toi pour accéder à ton PiedDex personnel."
    )

    login_tab, register_tab = st.tabs(
        [
            "🔐 Connexion",
            "✨ Créer un compte"
        ]
    )

    with login_tab:
        with st.form("login_form"):

            email = st.text_input(
                "Email",
                placeholder="toi@email.fr"
            )

            password = st.text_input(
                "Mot de passe",
                type="password"
            )

            submit_login = st.form_submit_button(
                "SE CONNECTER",
                width="stretch"
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
                            "email": email.strip(),
                            "password": password
                        })
                    )

                    save_auth_session(response)

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

    with register_tab:
        with st.form("register_form"):

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

            submit_register = st.form_submit_button(
                "CRÉER MON COMPTE",
                width="stretch"
            )

        if submit_register:
            if (
                not email_register
                or not password_register
            ):
                st.warning(
                    "Remplis tous les champs."
                )

            elif len(password_register) < 6:
                st.warning(
                    "Le mot de passe doit avoir "
                    "au moins 6 caractères."
                )

            elif password_register != password_confirm:
                st.warning(
                    "Les mots de passe ne correspondent pas."
                )

            else:
                try:
                    response = (
                        supabase.auth
                        .sign_up({
                            "email": email_register.strip(),
                            "password": password_register
                        })
                    )

                    if save_auth_session(response):
                        st.success(
                            "Compte créé."
                        )
                        time.sleep(0.5)
                        st.rerun()

                    else:
                        st.success(
                            "Compte créé. Vérifie ton email avant "
                            "de te connecter si la confirmation "
                            "email est activée."
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

my_profile = require_profile()


# ============================================================
# HEADER
# ============================================================

st.title("🦶 PIEDDEX")

st.caption(
    "Collection personnelle de spécimens"
)


# ============================================================
# UTILISATEUR + DÉCONNEXION
# ============================================================

user_col, logout_col = st.columns(
    [3, 1]
)

with user_col:
    st.caption(
        f"🟢 {st.session_state.profile_pseudo} · "
        f"{st.session_state.user_email}"
    )

with logout_col:
    if st.button(
        "Déconnexion",
        width="stretch"
    ):
        try:
            supabase.auth.sign_out()
        except Exception:
            pass

        for key in defaults:
            st.session_state[key] = defaults[key]

        st.rerun()


# ============================================================
# ONGLETS
# ============================================================

tab_capture, tab_collection, tab_friends, tab_leaderboard, tab_profile = st.tabs(
    [
        "📸 CAPTURER",
        "📚 MON PIEDDEX",
        "👥 AMIS",
        "🏆 CLASSEMENT",
        "👤 PROFIL"
    ]
)


# ============================================================
# CAPTURER
# ============================================================

with tab_capture:

    st.subheader(
        "Scanner de spécimen"
    )

    st.info(
        "Trouve un pied, prends une photo nette, "
        "donne-lui un nom puis lance l'analyse."
    )

    photo = st.camera_input(
        "📷 Prendre une photo"
    )

    if photo:

        st.image(
            photo,
            caption="Spécimen potentiel",
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
                st.session_state.analysis_data = None
                st.session_state.analysis_error = None

                try:
                    with st.spinner(
                        "Scanner PiedDex en cours..."
                    ):
                        analysis = analyse_pied(
                            photo.getvalue()
                        )

                    if not analysis.get(
                        "photo_valide",
                        False
                    ):
                        st.session_state.analysis_error = analysis
                    else:
                        st.session_state.analysis_data = analysis
                        st.session_state.analysis_name = nom.strip()
                        st.session_state.analysis_photo = photo.getvalue()

                except Exception as e:
                    st.session_state.analysis_error = {
                        "type_refus": "erreur",
                        "raison": str(e)
                    }

        if st.session_state.analysis_error:
            error = st.session_state.analysis_error
            error_type = error.get(
                "type_refus",
                "pas_de_pied"
            )

            if error_type == "mauvaise_photo":
                st.error(
                    "📸 CAPTURE INEXPLOITABLE"
                )
                st.write(
                    "Un pied a bien été détecté, mais le scanner "
                    "ne peut pas l'analyser correctement."
                )
                st.write(
                    "**Refais une photo plus nette du pied ! 🦶**"
                )
                if error.get("raison"):
                    st.caption(error["raison"])

            elif error_type == "erreur":
                st.error(
                    "⚠️ Le scanner n'a pas pu terminer l'analyse."
                )
                st.write(
                    "Réessaie dans quelques instants."
                )
                st.caption(
                    error.get("raison", "")
                )

            else:
                st.error(
                    "❌ AUCUN SPÉCIMEN DÉTECTÉ"
                )
                st.write(
                    "Le scanner PiedDex n'a pas trouvé de pied "
                    "exploitable sur cette photo."
                )
                st.write(
                    "**Refais une photo et trouve un pied à capturer ! 🦶**"
                )
                st.caption(
                    "Le pied doit être découvert, suffisamment visible et net."
                )

        if (
            st.session_state.analysis_data is not None
            and st.session_state.analysis_photo is not None
        ):
            analysis = st.session_state.analysis_data
            name = st.session_state.analysis_name

            indice = analysis["indice_pieddex"]
            esthetique = analysis["esthetique"]
            originalite = analysis["originalite"]
            rarete = analysis["rarete"]

            inject_analysis_style(
                indice,
                analysis
            )

            with st.container(
                key="analysis_result"
            ):
                st.caption(
                    "ANALYSE TERMINÉE"
                )

                st.subheader(
                    f"{rarity_symbol_from_name(rarete)} "
                    f"{name.upper()}"
                )

                c1, c2 = st.columns(2)

                with c1:
                    st.metric(
                        "Esthétique",
                        f"{esthetique:.1f}/10"
                    )

                with c2:
                    st.metric(
                        "Originalité",
                        f"{originalite:.1f}/10"
                    )

                st.divider()

                st.metric(
                    "INDICE PIEDDEX",
                    f"{indice:.1f}/10"
                )

                st.markdown(
                    f"### {rarity_symbol_from_name(rarete)} {rarete}"
                )

                st.write(
                    analysis["description"]
                )

                with st.expander(
                    "🔎 Voir le détail du scanner"
                ):
                    d1, d2 = st.columns(2)

                    with d1:
                        st.metric(
                            "Soin général",
                            f"{analysis['soin_general']:.1f}/10"
                        )
                        st.metric(
                            "Ongles / pédicure",
                            f"{analysis['ongles_pedicure']:.1f}/10"
                        )

                    with d2:
                        st.metric(
                            "Harmonie",
                            f"{analysis['harmonie']:.1f}/10"
                        )
                        st.metric(
                            "Aspect peau",
                            f"{analysis['peau']:.1f}/10"
                        )

                    st.caption(
                        "Qualité de la photo : "
                        f"{analysis['qualite_photo']:.1f}/10"
                    )

                if rarete == "MYTHIQUE":
                    st.balloons()

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
                                st.session_state.analysis_data
                            )

                        st.session_state.analysis_data = None
                        st.session_state.analysis_name = None
                        st.session_state.analysis_photo = None
                        st.session_state.analysis_error = None

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

    st.subheader(
        "Ma collection"
    )

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
                    indice = capture_index(capture)
                    rarete = (
                        capture.get("rarete")
                        or rarity_name(indice)
                    )

                    inject_card_style(
                        capture
                    )

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
                                f"**{rarity_symbol_from_name(rarete)} "
                                f"{indice:.1f}/10**"
                            )

                            if st.button(
                                "Voir",
                                key=(
                                    f"view_"
                                    f"{capture['id']}"
                                ),
                                width="stretch"
                            ):
                                show_specimen(
                                    capture
                                )



# ============================================================
# AMIS
# ============================================================

with tab_friends:

    st.subheader("👥 Mes amis")
    st.caption(
        f"Ton pseudo : @{st.session_state.profile_pseudo}"
    )

    friendships = get_friendships()
    incoming, outgoing, accepted = split_friendships(friendships)

    all_related_ids = {
        friend_other_user_id(relation)
        for relation in friendships
    }

    profiles_map = get_profiles_map(all_related_ids)

    st.markdown("### 🔎 Trouver un joueur")

    search_query = st.text_input(
        "Rechercher par pseudo",
        placeholder="Entre au moins 2 caractères",
        key="friend_search"
    )

    if search_query.strip():

        if len(search_query.strip()) < 2:
            st.caption("Entre au moins 2 caractères.")

        else:
            results = search_profiles(search_query)

            if not results:
                st.info("Aucun joueur trouvé.")

            else:
                current_friendships = get_friendships()

                for player in results:
                    other_id = str(player["user_id"])
                    pseudo = player.get("pseudo", "Joueur")
                    relation = relationship_with(
                        other_id,
                        current_friendships
                    )

                    left, right = st.columns([3, 2])

                    with left:
                        st.write(f"**@{pseudo}**")

                    with right:
                        if relation is None:
                            if st.button(
                                "➕ Ajouter",
                                key=f"add_friend_{other_id}",
                                width="stretch"
                            ):
                                try:
                                    send_friend_request(other_id)
                                    st.success(
                                        f"Demande envoyée à @{pseudo}."
                                    )
                                    time.sleep(0.35)
                                    st.rerun()
                                except Exception as e:
                                    st.warning(str(e))

                        elif relation.get("status") == "accepted":
                            st.caption("✅ Déjà ami")

                        elif relation.get("status") == "pending":
                            requester = str(
                                relation.get("requester_id")
                            )

                            if requester == st.session_state.user_id:
                                st.caption("⏳ Demande envoyée")
                            else:
                                st.caption("📩 Demande reçue")

    st.divider()

    st.markdown(
        f"### 📩 Demandes reçues ({len(incoming)})"
    )

    if not incoming:
        st.caption("Aucune demande en attente.")

    for relation in incoming:
        other_id = friend_other_user_id(relation)
        pseudo = profiles_map.get(other_id, "Joueur")

        name_col, accept_col, reject_col = st.columns(
            [3, 1.3, 1.3]
        )

        with name_col:
            st.write(f"**@{pseudo}**")

        with accept_col:
            if st.button(
                "✅",
                key=f"accept_{relation['id']}",
                help="Accepter",
                width="stretch"
            ):
                try:
                    accept_friend_request(relation["id"])
                    st.success(
                        f"@{pseudo} est maintenant ton ami."
                    )
                    time.sleep(0.3)
                    st.rerun()
                except Exception as e:
                    st.error(
                        f"Impossible d'accepter : {e}"
                    )

        with reject_col:
            if st.button(
                "✕",
                key=f"reject_{relation['id']}",
                help="Refuser",
                width="stretch"
            ):
                try:
                    reject_friend_request(relation["id"])
                    st.rerun()
                except Exception as e:
                    st.error(
                        f"Impossible de refuser : {e}"
                    )

    st.divider()

    st.markdown(
        f"### 🤝 Mes amis ({len(accepted)})"
    )

    if not accepted:
        st.info(
            "Tu n'as pas encore d'amis sur PiedDex. "
            "Recherche un pseudo pour commencer."
        )

    for relation in accepted:
        other_id = friend_other_user_id(relation)
        pseudo = profiles_map.get(other_id, "Joueur")

        name_col, action_col = st.columns(
            [4, 1.5]
        )

        with name_col:
            st.write(f"🟢 **@{pseudo}**")

        with action_col:
            if st.button(
                "Retirer",
                key=f"remove_friend_{relation['id']}",
                width="stretch"
            ):
                try:
                    remove_friend(relation["id"])
                    st.rerun()
                except Exception as e:
                    st.error(
                        f"Impossible de retirer cet ami : {e}"
                    )

    st.divider()

    with st.expander(
        f"⏳ Demandes envoyées ({len(outgoing)})"
    ):
        if not outgoing:
            st.caption(
                "Aucune demande envoyée en attente."
            )

        for relation in outgoing:
            other_id = friend_other_user_id(relation)
            pseudo = profiles_map.get(other_id, "Joueur")

            name_col, cancel_col = st.columns(
                [3, 1.5]
            )

            with name_col:
                st.write(f"@{pseudo}")

            with cancel_col:
                if st.button(
                    "Annuler",
                    key=f"cancel_{relation['id']}",
                    width="stretch"
                ):
                    try:
                        cancel_friend_request(
                            relation["id"]
                        )
                        st.rerun()
                    except Exception as e:
                        st.error(
                            f"Impossible d'annuler : {e}"
                        )



# ============================================================
# CLASSEMENT
# ============================================================

with tab_leaderboard:

    st.subheader("🏆 Classement PiedDex")

    st.caption(
        "Le classement comprend uniquement toi et tes amis acceptés."
    )

    st.info(
        "Points : ◇ Commun 0 · ◆ Peu commun 1 · ✦ Rare 15 · "
        "✦✦ Épique 50 · ★ Légendaire 150 · ✺ Mythique 500"
    )

    leaderboard = get_friend_leaderboard()

    if not leaderboard:
        st.warning(
            "Aucune donnée de classement disponible pour le moment."
        )

    else:
        sort_mode = st.selectbox(
            "Classer par",
            [
                "Points PiedDex",
                "Nombre de spécimens",
                "Meilleur spécimen",
                "Meilleure moyenne"
            ],
            key="leaderboard_sort"
        )

        if sort_mode == "Nombre de spécimens":
            leaderboard = sorted(
                leaderboard,
                key=lambda p: (
                    p["total_captures"],
                    p["score_pieddex"],
                    p["meilleur"]
                ),
                reverse=True
            )

        elif sort_mode == "Meilleur spécimen":
            leaderboard = sorted(
                leaderboard,
                key=lambda p: (
                    p["meilleur"],
                    p["score_pieddex"],
                    p["moyenne"]
                ),
                reverse=True
            )

        elif sort_mode == "Meilleure moyenne":
            leaderboard = sorted(
                leaderboard,
                key=lambda p: (
                    p["moyenne"],
                    p["score_pieddex"],
                    p["total_captures"]
                ),
                reverse=True
            )

        else:
            leaderboard = sorted(
                leaderboard,
                key=lambda p: (
                    p["score_pieddex"],
                    p["total_captures"],
                    p["meilleur"],
                    p["moyenne"]
                ),
                reverse=True
            )

        total_players = len(leaderboard)

        st.divider()

        for rank, player in enumerate(
            leaderboard,
            start=1
        ):
            is_me = (
                str(player.get("user_id"))
                == st.session_state.user_id
            )

            pseudo = player.get("pseudo", "Joueur")
            medal = medal_for_rank(rank)

            with st.container(border=True):
                left, middle, right = st.columns(
                    [1.1, 4, 2]
                )

                with left:
                    st.markdown(
                        f"### {medal}"
                    )

                with middle:
                    suffix = " **(TOI)**" if is_me else ""
                    st.markdown(
                        f"**@{pseudo}**{suffix}"
                    )

                    st.caption(
                        f"{player['total_captures']} spécimen(s) · "
                        f"record {player['meilleur']:.1f}/10"
                    )

                with right:
                    if sort_mode == "Nombre de spécimens":
                        st.metric(
                            "Spécimens",
                            player["total_captures"]
                        )

                    elif sort_mode == "Meilleur spécimen":
                        st.metric(
                            "Record",
                            f"{player['meilleur']:.1f}/10"
                        )

                    elif sort_mode == "Meilleure moyenne":
                        st.metric(
                            "Moyenne",
                            f"{player['moyenne']:.1f}/10"
                        )

                    else:
                        st.metric(
                            "Points",
                            f"{player['score_pieddex']}"
                        )

                if st.button(
                    "Voir les statistiques",
                    key=f"stats_{player['user_id']}_{sort_mode}",
                    width="stretch"
                ):
                    show_player_stats(
                        player,
                        rank,
                        total_players
                    )


# ============================================================
# PROFIL
# ============================================================

with tab_profile:

    captures = get_captures()

    st.subheader(
        "👤 Mon profil"
    )

    st.write(
        f"**Pseudo :** @{st.session_state.profile_pseudo}"
    )

    st.write(
        f"**Compte :** "
        f"{st.session_state.user_email}"
    )

    with st.expander("✏️ Modifier mon pseudo"):
        new_pseudo = st.text_input(
            "Nouveau pseudo",
            value=st.session_state.profile_pseudo or "",
            max_chars=24,
            key="edit_profile_pseudo"
        )

        if st.button(
            "ENREGISTRER LE PSEUDO",
            key="save_new_pseudo",
            width="stretch"
        ):
            try:
                update_my_pseudo(new_pseudo)
                st.success("Pseudo mis à jour.")
                time.sleep(0.35)
                st.rerun()
            except Exception as e:
                message = str(e)

                if "duplicate" in message.lower() or "unique" in message.lower():
                    st.error("Ce pseudo est déjà utilisé.")
                else:
                    st.error(message)

    total = len(captures)

    if captures:
        scores = [
            capture_index(capture)
            for capture in captures
        ]

        best_score = max(scores)
        average_score = (
            sum(scores)
            / len(scores)
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

    rarity_counts = {
        "COMMUN": 0,
        "PEU COMMUN": 0,
        "RARE": 0,
        "ÉPIQUE": 0,
        "LÉGENDAIRE": 0,
        "MYTHIQUE": 0,
    }

    for capture in captures:
        name = (
            capture.get("rarete")
            or rarity_name(
                capture_index(capture)
            )
        )

        if name in rarity_counts:
            rarity_counts[name] += 1

    st.write(
        f"◇ **Communs :** "
        f"{rarity_counts['COMMUN']}"
    )

    st.write(
        f"◆ **Peu communs :** "
        f"{rarity_counts['PEU COMMUN']}"
    )

    st.write(
        f"✦ **Rares :** "
        f"{rarity_counts['RARE']}"
    )

    st.write(
        f"💜 **Épiques :** "
        f"{rarity_counts['ÉPIQUE']}"
    )

    st.write(
        f"⭐ **Légendaires :** "
        f"{rarity_counts['LÉGENDAIRE']}"
    )

    st.write(
        f"🌟 **Mythiques :** "
        f"{rarity_counts['MYTHIQUE']}"
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
