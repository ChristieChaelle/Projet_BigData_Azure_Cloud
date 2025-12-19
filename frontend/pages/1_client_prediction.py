import streamlit as st
import requests
import os
import pymongo
import time
from dotenv import load_dotenv

# =====================================================
# CONFIGURATION PAGE (Toujours en première ligne)
# =====================================================
st.set_page_config(
    page_title="Prédiction client",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =====================================================
# VARIABLES D'ENVIRONNEMENT
# =====================================================
load_dotenv()
MONGODB_URI = os.getenv("MONGODB_URI")
FLASK_API_URL = os.getenv("FLASK_API_URL")

# =====================================================
# STYLE CSS PROFESSIONNEL
# =====================================================
st.markdown("""
<style>
:root { --rb-blue: #1E4A8E; }

/* Logo circulaire RB */
.rb-logo-circle {
    background-color: var(--rb-blue);
    color: white;
    border-radius: 50%;
    width: 80px; height: 80px;
    display: flex; align-items: center; justify-content: center;
    font-weight: bold; font-size: 26px;
    margin: 0 auto 10px auto;
    box-shadow: 0 4px 10px rgba(0,0,0,0.2);
}

.rb-card {
    background: white;
    padding: 25px;
    border-radius: 15px;
    box-shadow: 0 4px 15px rgba(0,0,0,0.05);
    margin-bottom: 20px;
}

/* Section Actions Recommandées */
.action-item {
    background-color: #f8f9fa;
    border-left: 5px solid var(--rb-blue);
    padding: 12px 18px;
    margin-bottom: 10px;
    border-radius: 0 10px 10px 0;
    font-size: 0.95em;
    color: #333;
}

.metric-label { color: #6c757d; font-size: 0.9em; margin-bottom: 2px; }
.metric-value { font-weight: bold; font-size: 1.1em; color: var(--rb-blue); }

/* Couleur de la barre de progression */
.stProgress > div > div > div > div { background-color: var(--rb-blue); }
</style>
""", unsafe_allow_html=True)

# =====================================================
# FONCTIONS DE DONNÉES (FLASK & MONGODB)
# =====================================================

def get_client_personal_data(client_id):
    """Récupère les informations civiles du client via MongoDB"""
    try:
        mongo_client = pymongo.MongoClient(MONGODB_URI)
        db = mongo_client["default_risk"] # Nom de votre DB dans MongoDB
        client = db["users_data"].find_one({"SK_CURR_ID": int(client_id)}, {"_id": 0})
        mongo_client.close()
        return client
    except Exception as e:
        st.error(f"Erreur MongoDB : {e}")
        return None

def predict_default_risk(client_id):
    """Récupère la prédiction et les recommandations via app.py (Flask)"""
    try:
        response = requests.get(
            f"{FLASK_API_URL}/predict_default",
            params={"client_id": client_id},
            timeout=300
        )
        if response.status_code == 200:
            data = response.json()
            score = round(data["prediction"]["risk_score"] * 100, 1)
            
            # Catégorisation simplifiée pour l'affichage
            if score >= 70: cat = "Élevé"
            elif score >= 40: cat = "Moyen"
            else: cat = "Faible"
            
            return {
                "score": score,
                "category": cat,
                "decision": data["recommendation"]["decision"],
                "actions": data["recommendation"].get("action_plan", []), # Récupéré de Flask
                "factors": data.get("impact_factors", [])
            }
    except Exception as e:
        st.error(f"Erreur API de prédiction : {e}")
    return None

# =====================================================
# PAGE CLIENT PREDICTION
# =====================================================

# Sidebar Spécifique
st.sidebar.markdown('<div class="rb-logo-circle">RB</div>', unsafe_allow_html=True)
st.sidebar.markdown("<h2 style='text-align:center; color:#1E4A8E; margin-top:0;'>Risk Banking</h2>", unsafe_allow_html=True)
st.sidebar.markdown("---")

client_id = st.sidebar.text_input("Saisir l'ID Client", placeholder="Ex: 114883")
analyze_btn = st.sidebar.button("🚀 Analyser le risque", use_container_width=True, type="primary")

st.sidebar.markdown("---")
with st.sidebar.expander("❓ Aide"):
    st.write("L'analyse utilise les modèles Databricks pour prédire la probabilité de défaut.")

# Logique d'affichage après clic
if analyze_btn and client_id:
    with st.spinner("⏳ Calcul du score et génération des recommandations..."):
        p_data = get_client_personal_data(client_id)
        prediction = predict_default_risk(client_id)
        time.sleep(1) # Fluidité visuelle

    if p_data and prediction:
        st.title(f"🔮 Dossier : {p_data.get('FirstName', '')} {p_data.get('LastName', '')}")
        
        # Avatar et Bascule de vue
        _, col_av, _ = st.columns([3,1,3])
        with col_av:
            img_url = p_data.get("PhotoURL", "https://www.w3schools.com/howto/img_avatar.png")
            st.image(img_url, width=150)
            
            if 'current_view' not in st.session_state:
                st.session_state.current_view = 'analyse'
            
            if st.button("🔄 Basculer Profil / Analyse", use_container_width=True):
                st.session_state.current_view = 'profil' if st.session_state.current_view == 'analyse' else 'analyse'

        view = st.session_state.get('current_view', 'analyse')

        if view == 'analyse':
            # --- VUE SCORE ---
            st.subheader("📊 Score de Risque")
            c1, c2, c3 = st.columns([1, 8, 2])
            c1.caption("Faible")
            c2.progress(int(prediction['score']))
            c3.markdown(f"<h2 style='color:orange; margin:0;'>{prediction['score']}%</h2>", unsafe_allow_html=True)

            st.markdown(f"""
            <div class="rb-card" style="border-left: 5px solid #1E4A8E; color:black">
                <h4 style="margin-top:0; color:black;">Recommandation Décisionnelle</h4>
                <p><b>Décision :</b> {prediction['decision']}</p>
                <span style="background:#4CAF50; color:white; padding:5px 15px; border-radius:15px; font-weight:bold;">
                    Catégorie : {prediction['category']}
                </span>
            </div>
            """, unsafe_allow_html=True)

            # --- ACTIONS DYNAMIQUES DE APP.PY ---
            st.subheader("🚀 Actions Stratégiques")
            if prediction['actions']:
                for i, action in enumerate(prediction['actions'], 1):
                    st.markdown(f"""<div class="action-item"><b>{i}.</b> {action}</div>""", unsafe_allow_html=True)
            else:
                st.info("Aucune action spécifique recommandée.")

        else:
            # --- VUE PROFIL ---
            st.subheader("👤 Détails du Client")
            col_p1, col_p2 = st.columns(2)
            with col_p1:
                st.markdown(f'<p class="metric-label">Revenu Annuel</p><p class="metric-value">{p_data.get("AMT_INCOME_TOTAL", "N/A")} €</p>', unsafe_allow_html=True)
            with col_p2:
                st.markdown(f'<p class="metric-label">Ancienneté</p><p class="metric-value">{p_data.get("DAYS_EMPLOYED", "N/A")} jours</p>', unsafe_allow_html=True)

            st.markdown("### 🔍 Facteurs d'Influence")
            for f in prediction["factors"]:
                color = "#e74c3c" if f["impact"] > 0 else "#2ecc71"
                st.markdown(f"**{f['name']}** : <span style='color:{color}'>{f['impact']}%</span>", unsafe_allow_html=True)
    else:
        st.error("❌ Erreur : ID introuvable ou API indisponible.")
else:
    st.info("💡 Saisissez un identifiant client dans la barre latérale pour commencer.")
