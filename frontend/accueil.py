import streamlit as st

st.set_page_config(
    page_title="Accueil",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =====================================================
# 3️⃣ STYLE CSS PROFESSIONNEL
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

st.info("💡 Bienvenue dans notre application de scoring bancaire !")

st.sidebar.markdown('<div class="rb-logo-circle">RB</div>', unsafe_allow_html=True)
st.sidebar.markdown("<h2 style='text-align:center; color:#1E4A8E; margin-top:0;'>Risk Banking</h2>", unsafe_allow_html=True)

st.markdown(
    f"""
    Cette application permet de :
    </br>
    📅 Visualiser et analyser les données bancaires 
    </br>
    📝 Évaluer le scoring des clients.
    </br>
    📊 Explorer les statistiques et dashboards interactifs.
""", unsafe_allow_html=True
)


