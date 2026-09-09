import streamlit as st
from supabase import create_client
from datetime import datetime
import random
import uuid
import time

# ============================================================
# CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="PiedDex",
    page_icon="🦶",
    layout="centered",
    initial_sidebar_state="collapsed"
)

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

BUCKET = "pieddex-photos"


# ============================================================
# SESSION
# ============================================================

if "user" not in st.session_state:
    st.session_state.user = None

if "access_token" not in st.session_state:
    st.session_state.access_token = None

if "refresh_token" not in st.session_state:
    st.session_state.refresh_token = None

if "analyse" not in st.session_state:
    st.session_state.analyse = None

if "analyse_nom" not in st.session_state:
    st.session_state.analyse_nom = None

if "analyse_photo" not in st.session_state:
    st.session_state.analyse_photo = None


# ============================================================
# DESIGN
# ============================================================

st.markdown(
    """
<style>

/* ------------------------------------------------------------
   BASE
------------------------------------------------------------ */

.stApp {
    background:
        radial-gradient(circle at 50% 0%, #26365e 0%, #121a32 30%, #080d1b 75%);
    color: white;
}

.block-container {
    max-width: 1050px;
    padding-top: 1.1rem;
    padding-bottom: 5rem;
}

header[data-testid="stHeader"] {
    background: transparent;
}

#MainMenu {
    visibility: hidden;
}

footer {
    visibility: hidden;
}


/* ------------------------------------------------------------
   LOGO
------------------------------------------------------------ */

.logo {
    text-align: center;
    margin-bottom: 8px;
}

.logo-main {
    font-size: clamp(38px, 10vw, 68px);
    font-weight: 1000;
    letter-spacing: -3px;
    color: #ffd83d;
    text-shadow:
        0 3px 0 #cb8712,
        0 6px 0 #3a4a91,
        0 8px 15px rgba(0,0,0,.55);
}

.logo-sub {
    color: #9eb1db;
    font-size: 12px;
    letter-spacing: 4px;
    font-weight: 800;
    margin-top: -5px;
}


/* ------------------------------------------------------------
   PANNEAUX
------------------------------------------------------------ */

.panel {
    background:
        linear-gradient(145deg, rgba(32,45,82,.96), rgba(13,21,43,.96));
    border: 1px solid rgba(144,173,235,.25);
    border-radius: 22px;
    padding: 20px;
    box-shadow:
        inset 0 1px rgba(255,255,255,.08),
        0 15px 35px rgba(0,0,0,.35);
    margin: 12px 0;
}

.scan-title {
    text-align: center;
    color: #ffd84a;
    font-weight: 1000;
    font-size: 23px;
    letter-spacing: 1px;
}

.scan-sub {
    text-align: center;
    color: #91a5d1;
    font-size: 13px;
    margin-bottom: 10px;
}


/* ------------------------------------------------------------
   BOUTONS
------------------------------------------------------------ */

.stButton > button {
    width: 100%;
    border-radius: 14px;
    min-height: 44px;
    font-weight: 900;
    border: 1px solid rgba(255,255,255,.16);
    background: linear-gradient(180deg,#263a6a,#182746);
    color: white;
    box-shadow: 0 5px 13px rgba(0,0,0,.25);
}

.stButton > button:hover {
    border-color: #ffd83d;
    color: #ffd83d;
    transform: translateY(-1px);
}

div[data-testid="stFormSubmitButton"] button {
    background: linear-gradient(180deg,#ffd943,#e3a514);
    color: #17203a;
    border: none;
}


/* ------------------------------------------------------------
   INPUTS
------------------------------------------------------------ */

.stTextInput input {
    background: #0c1428;
    border: 1px solid #344979;
    color: white;
    border-radius: 12px;
}

.stTextInput input:focus {
    border-color: #ffd83d;
}


/* ------------------------------------------------------------
   RARETÉS
------------------------------------------------------------ */

.common {
    color: #b8c2d8;
}

.uncommon {
    color: #68d391;
}

.rare {
    color: #56b9ff;
}

.epic {
    color: #bd7cff;
}

.legendary {
    color: #ffd83d;
}


/* ------------------------------------------------------------
   CARTE ANALYSE
------------------------------------------------------------ */

.result-card {
    border-radius: 23px;
    padding: 5px;
    margin: 15px 0;
}

.result-inner {
    border-radius: 19px;
    padding: 20px;
    background: linear-gradient(145deg,#182746,#0b1327);
    text-align: center;
}

.result-name {
    font-size: 27px;
    font-weight: 1000;
}

.result-score {
    font-size: 58px;
    font-weight: 1000;
    line-height: 1;
    margin: 8px;
}

.result-rarity {
    font-size: 18px;
    font-weight: 1000;
    letter-spacing: 2px;
}


/* ------------------------------------------------------------
   GALERIE
------------------------------------------------------------ */

.gallery-title {
    font-size: 25px;
    font-weight: 1000;
    color: white;
    margin-top: 12px;
}

.gallery-count {
    color: #95a9d5;
    font-size: 13px;
    margin-bottom: 12px;
}


/* ------------------------------------------------------------
   MOBILE
------------------------------------------------------------ */

@media (max-width: 600px) {

    .block-container {
        padding-left: .55rem;
        padding-right: .55rem;
        padding-top: .4rem;
    }

    .logo-main {
        font-size: 45px;
    }

    .logo-sub {
        font-size: 9px;
    }

    .stButton > button {
        min-height: 39px;
        padding-left: 3px;
        padding-right: 3px;
        font-size: 12px;
    }

    div[data-testid="stImage"] img {
        border-radius: 10px;
    }
}

</style>
""",
    unsafe_allow_html=True
)


# ============================================================
# FONCTIONS
# ============================================================

def logo():
    st.markdown(
        """
        <div class="logo">
            <div class="logo-main">PIEDDEX</div>
            <div class="logo-sub">COLLECTION DE SPÉCIMENS</div>
        </div>
        """,
        unsafe_allow_html=True
    )


def set_session(session):
    if not session:
        return

    st.session_state.user = session.user
    st.session_state.access_token = session.access_token
    st.session_state.refresh_token = session.refresh_token

    supabase.auth.set_session(
        session.access_token,
        session.refresh_token
    )


def restore_session():
    if (
        st.session_state.access_token
        and st.session_state.refresh_token
    ):
        try:
            response = supabase.auth.set_session(
                st.session_state.access_token,
                st.session_state.refresh_token
            )

            if response and response.session:
                set_session(response.session)

        except Exception:
            st.session_state.user = None
            st.session_state.access_token = None
            st.session_state.refresh_token = None


def rarity(score):

    if score <= 3:
        return "COMMUN", "common", "#8b98ad"

    elif score <= 5:
        return "PEU COMMUN", "uncommon", "#52cf83"

    elif score <= 7:
        return "RARE", "rare", "#42aefa"

    elif score <= 9:
        return "ÉPIQUE", "epic", "#a96bff"

    else:
        return "LÉGENDAIRE", "legendary", "#ffd43b"


def analyse_specimen():

    # Pour l'instant il s'agit d'un tirage ludique.
    # On pourra remplacer cette fonction par un modèle IA plus tard.

    chances = [
        1, 2, 3,
        4, 4,
        5, 5,
        6, 6,
        7, 7,
        8, 8,
        9,
        10
    ]

    return random.choice(chances)


def signed_photo(path):

    try:
        result = (
            supabase.storage
            .from_(BUCKET)
            .create_signed_url(path, 3600)
        )

        if isinstance(result, dict):
            return (
                result.get("signedURL")
                or result.get("signedUrl")
                or result.get("signed_url")
            )

        return None

    except Exception:
        return None


def get_captures():

    try:

        result = (
            supabase.table("captures")
            .select("*")
            .order("date_capture", desc=True)
            .execute()
        )

        return result.data or []

    except Exception as e:
        st.error(f"Impossible de charger le PiedDex : {e}")
        return []


def next_number():

    captures = get_captures()

    if not captures:
        return 1

    numbers = [
        int(c["numero"])
        for c in captures
        if c.get("numero") is not None
    ]

    return max(numbers, default=0) + 1


def save_capture(photo_bytes, nom, score):

    user = st.session_state.user

    if not user:
        raise Exception("Utilisateur non connecté.")

    rarete, _, _ = rarity(score)

    extension = "jpg"

    filename = (
        f"{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        f"_{uuid.uuid4().hex[:8]}.{extension}"
    )

    photo_path = f"{user.id}/{filename}"

    # Envoi photo
    supabase.storage.from_(BUCKET).upload(
        path=photo_path,
        file=photo_bytes,
        file_options={
            "content-type": "image/jpeg",
            "upsert": "false"
        }
    )

    numero = next_number()

    try:

        supabase.table("captures").insert({
            "user_id": user.id,
            "numero": numero,
            "nom": nom,
            "score": score,
            "rarete": rarete,
            "photo_path": photo_path
        }).execute()

    except Exception:

        # Si l'insertion DB échoue, on retire la photo
        try:
            supabase.storage.from_(BUCKET).remove([photo_path])
        except Exception:
            pass

        raise


def delete_capture(capture):

    try:

        photo_path = capture.get("photo_path")

        if photo_path:
            supabase.storage.from_(BUCKET).remove([photo_path])

        (
            supabase.table("captures")
            .delete()
            .eq("id", capture["id"])
            .execute()
        )

        st.success("Spécimen supprimé.")

        time.sleep(.5)
        st.rerun()

    except Exception as e:
        st.error(f"Suppression impossible : {e}")


# ============================================================
# AUTHENTIFICATION
# ============================================================

restore_session()


def authentication():

    logo()

    st.markdown(
        """
        <div class="panel">
            <div class="scan-title">ACCÈS DRESSEUR</div>
            <div class="scan-sub">
                Connecte-toi pour accéder à ta collection personnelle.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    login_tab, register_tab = st.tabs(
        ["🔐 CONNEXION", "✨ CRÉER UN COMPTE"]
    )

    # ---------------- LOGIN ----------------

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

            login = st.form_submit_button(
                "ENTRER DANS MON PIEDDEX",
                width="stretch"
            )

        if login:

            if not email or not password:
                st.warning("Entre ton email et ton mot de passe.")

            else:

                try:

                    response = supabase.auth.sign_in_with_password({
                        "email": email.strip(),
                        "password": password
                    })

                    set_session(response.session)

                    st.success("Connexion réussie !")
                    time.sleep(.4)
                    st.rerun()

                except Exception as e:
                    st.error(
                        "Connexion impossible. Vérifie ton email "
                        "et ton mot de passe."
                    )

    # ---------------- REGISTER ----------------

    with register_tab:

        with st.form("register_form"):

            new_email = st.text_input(
                "Ton email",
                key="register_email"
            )

            new_password = st.text_input(
                "Choisis un mot de passe",
                type="password",
                key="register_password"
            )

            confirm_password = st.text_input(
                "Confirme le mot de passe",
                type="password",
                key="confirm_password"
            )

            register = st.form_submit_button(
                "CRÉER MON COMPTE",
                width="stretch"
            )

        if register:

            if not new_email or not new_password:
                st.warning("Remplis tous les champs.")

            elif len(new_password) < 6:
                st.warning(
                    "Le mot de passe doit contenir au moins 6 caractères."
                )

            elif new_password != confirm_password:
                st.warning("Les mots de passe ne correspondent pas.")

            else:

                try:

                    response = supabase.auth.sign_up({
                        "email": new_email.strip(),
                        "password": new_password
                    })

                    if response.session:

                        set_session(response.session)

                        st.success("Compte créé !")
                        time.sleep(.5)
                        st.rerun()

                    else:

                        st.success(
                            "Compte créé. Vérifie ton email si Supabase "
                            "demande une confirmation."
                        )

                except Exception as e:
                    st.error(f"Création du compte impossible : {e}")


# ============================================================
# APPLICATION
# ============================================================

if not st.session_state.user:

    authentication()
    st.stop()


# Réapplique explicitement la session à ce client
try:
    supabase.auth.set_session(
        st.session_state.access_token,
        st.session_state.refresh_token
    )
except Exception:
    pass


logo()


# ============================================================
# BARRE UTILISATEUR
# ============================================================

user_email = st.session_state.user.email or "Dresseur"

top1, top2 = st.columns([3, 1])

with top1:
    st.caption(f"🟢 Connecté : **{user_email}**")

with top2:

    if st.button(
        "Déconnexion",
        width="stretch"
    ):

        try:
            supabase.auth.sign_out()
        except Exception:
            pass

        st.session_state.user = None
        st.session_state.access_token = None
        st.session_state.refresh_token = None
        st.session_state.analyse = None
        st.session_state.analyse_nom = None
        st.session_state.analyse_photo = None

        st.rerun()


# ============================================================
# ONGLETS
# ============================================================

capture_tab, collection_tab, profile_tab = st.tabs([
    "📸 CAPTURER",
    "📚 MON PIEDDEX",
    "👤 PROFIL"
])


# ============================================================
# CAPTURER
# ============================================================

with capture_tab:

    st.markdown(
        """
        <div class="panel">
            <div class="scan-title">SCANNER UN SPÉCIMEN</div>
            <div class="scan-sub">
                Photographie un nouveau spécimen pour tenter
                de l'ajouter à ta collection.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    photo = st.camera_input(
        "📷 Prendre une photo"
    )

    if photo:

        st.image(
            photo,
            width="stretch"
        )

        nom = st.text_input(
            "Nom du spécimen",
            placeholder="Ex : Piedator, Jean-Pied, Patoche..."
        )

        analyse_button = st.button(
            "⚡ ANALYSER LE SPÉCIMEN",
            width="stretch"
        )

        if analyse_button:

            if not nom.strip():

                st.warning(
                    "Donne d'abord un nom à ton spécimen."
                )

            else:

                with st.spinner(
                    "Analyse biométrique du spécimen..."
                ):

                    time.sleep(1.1)

                    score = analyse_specimen()

                    st.session_state.analyse = score
                    st.session_state.analyse_nom = nom.strip()
                    st.session_state.analyse_photo = photo.getvalue()

        if (
            st.session_state.analyse is not None
            and st.session_state.analyse_photo is not None
        ):

            score = st.session_state.analyse
            rarete, css_class, couleur = rarity(score)

            st.markdown(
                f"""
                <div class="result-card"
                     style="
                     background:
                     linear-gradient(
                         135deg,
                         {couleur},
                         #ffffff,
                         {couleur}
                     );
                     box-shadow:
                     0 0 25px {couleur}55;
                     ">
                    <div class="result-inner">

                        <div style="
                            color:#94a9d7;
                            font-size:11px;
                            letter-spacing:3px;
                            font-weight:900;">
                            ANALYSE TERMINÉE
                        </div>

                        <div class="result-name">
                            {st.session_state.analyse_nom.upper()}
                        </div>

                        <div class="result-score"
                             style="color:{couleur};">
                            {score}/10
                        </div>

                        <div class="result-rarity"
                             style="color:{couleur};">
                            {rarete}
                        </div>

                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

            if score == 10:
                st.balloons()

            if st.button(
                "💾 AJOUTER À MON PIEDDEX",
                type="primary",
                width="stretch"
            ):

                try:

                    with st.spinner(
                        "Capture du spécimen..."
                    ):

                        save_capture(
                            st.session_state.analyse_photo,
                            st.session_state.analyse_nom,
                            st.session_state.analyse
                        )

                    st.session_state.analyse = None
                    st.session_state.analyse_nom = None
                    st.session_state.analyse_photo = None

                    st.success(
                        "✨ Nouveau spécimen ajouté à ton PiedDex !"
                    )

                    time.sleep(.7)
                    st.rerun()

                except Exception as e:

                    st.error(
                        f"Impossible d'enregistrer le spécimen : {e}"
                    )


# ============================================================
# COLLECTION
# ============================================================

with collection_tab:

    captures = get_captures()

    st.markdown(
        '<div class="gallery-title">MON PIEDDEX</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        f"""
        <div class="gallery-count">
            {len(captures)} spécimen{"s" if len(captures) != 1 else ""}
            capturé{"s" if len(captures) != 1 else ""}
        </div>
        """,
        unsafe_allow_html=True
    )

    if not captures:

        st.info(
            "Ton PiedDex est vide. Va capturer ton premier spécimen !"
        )

    else:

        # ----------------------------------------------------
        # 4 CARTES PAR LIGNE
        # ----------------------------------------------------

        for row_start in range(0, len(captures), 4):

            row = captures[row_start:row_start + 4]

            columns = st.columns(
                4,
                gap="small"
            )

            for index, capture in enumerate(row):

                with columns[index]:

                    score = int(capture.get("score", 0))
                    rarete, css_class, couleur = rarity(score)

                    url = signed_photo(
                        capture.get("photo_path")
                    )

                    # Bordure colorée autour de chaque spécimen
                    st.markdown(
                        f"""
                        <div style="
                            height:5px;
                            border-radius:10px 10px 0 0;
                            background:{couleur};
                            box-shadow:0 0 10px {couleur};
                        "></div>
                        """,
                        unsafe_allow_html=True
                    )

                    if url:
                        st.image(
                            url,
                            width="stretch"
                        )
                    else:
                        st.caption("Photo indisponible")

                    nom_capture = capture.get(
                        "nom",
                        "Sans nom"
                    )

                    st.markdown(
                        f"""
                        <div style="
                            text-align:center;
                            margin-top:-3px;
                            line-height:1.1;
                        ">
                            <div style="
                                font-weight:1000;
                                font-size:12px;
                                overflow:hidden;
                                white-space:nowrap;
                                text-overflow:ellipsis;
                            ">
                                {nom_capture}
                            </div>

                            <div style="
                                color:{couleur};
                                font-size:14px;
                                font-weight:1000;
                                margin-top:3px;
                            ">
                                {score}/10
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                    if st.button(
                        "VOIR",
                        key=f"view_{capture['id']}",
                        width="stretch"
                    ):

                        st.session_state[
                            "selected_capture"
                        ] = capture["id"]

            st.write("")

        # ----------------------------------------------------
        # CARTE AGRANDIE
        # ----------------------------------------------------

        selected_id = st.session_state.get(
            "selected_capture"
        )

        if selected_id:

            selected = next(
                (
                    c for c in captures
                    if c["id"] == selected_id
                ),
                None
            )

            if selected:

                st.divider()

                score = int(
                    selected.get("score", 0)
                )

                rarete, css_class, couleur = rarity(score)

                close_col, _ = st.columns(
                    [1, 5]
                )

                with close_col:

                    if st.button(
                        "✕ FERMER",
                        width="stretch"
                    ):
                        st.session_state.pop(
                            "selected_capture",
                            None
                        )
                        st.rerun()

                st.markdown(
                    f"""
                    <div class="result-card"
                         style="
                         background:
                         linear-gradient(
                             135deg,
                             {couleur},
                             #ffffff,
                             {couleur}
                         );
                         box-shadow:
                         0 0 35px {couleur}66;
                         ">
                        <div class="result-inner">

                            <div style="
                                color:#9badd2;
                                font-size:11px;
                                letter-spacing:3px;
                            ">
                                SPÉCIMEN
                                #{str(selected.get("numero", 0)).zfill(3)}
                            </div>

                            <div class="result-name">
                                {selected.get("nom", "Sans nom").upper()}
                            </div>

                            <div class="result-rarity"
                                 style="color:{couleur};">
                                {rarete}
                            </div>

                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                selected_url = signed_photo(
                    selected.get("photo_path")
                )

                if selected_url:

                    st.image(
                        selected_url,
                        width="stretch"
                    )

                st.markdown(
                    f"""
                    <div style="
                        text-align:center;
                        font-size:65px;
                        font-weight:1000;
                        color:{couleur};
                        text-shadow:0 0 22px {couleur}66;
                    ">
                        {score}/10
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                st.caption(
                    f"Capturé le "
                    f"{str(selected.get('date_capture', ''))[:10]}"
                )

                st.warning(
                    "La suppression est définitive."
                )

                if st.button(
                    "🗑️ SUPPRIMER CE SPÉCIMEN",
                    key=f"delete_{selected['id']}",
                    width="stretch"
                ):

                    delete_capture(selected)


# ============================================================
# PROFIL
# ============================================================

with profile_tab:

    captures = get_captures()

    st.markdown(
        """
        <div class="panel">
            <div class="scan-title">CARTE DRESSEUR</div>
            <div class="scan-sub">
                Statistiques de ta collection personnelle.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.write("### 👤 Compte")
    st.write(st.session_state.user.email)

    st.write("### 📚 Collection")

    total = len(captures)

    if total:

        scores = [
            int(c.get("score", 0))
            for c in captures
        ]

        moyenne = sum(scores) / len(scores)
        meilleur = max(scores)

    else:

        moyenne = 0
        meilleur = 0

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Captures",
        total
    )

    c2.metric(
        "Moyenne",
        f"{moyenne:.1f}/10"
    )

    c3.metric(
        "Record",
        f"{meilleur}/10"
    )

    legendary_count = sum(
        1
        for c in captures
        if int(c.get("score", 0)) == 10
    )

    epic_count = sum(
        1
        for c in captures
        if int(c.get("score", 0)) in [8, 9]
    )

    st.write("### 🏆 Raretés")

    st.write(
        f"🌟 **Légendaires :** {legendary_count}"
    )

    st.write(
        f"💜 **Épiques :** {epic_count}"
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

        st.session_state.clear()
        st.rerun()
