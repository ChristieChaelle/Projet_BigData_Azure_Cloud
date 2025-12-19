
from __future__ import annotations
import streamlit as st
import requests
import pymongo
import time
from dotenv import load_dotenv
import os
import re
import json
from typing import Any, Dict, Optional, Tuple, List

# Import de reconstruction  d'une figure Plotly à partir du HTML
try:
    import plotly.graph_objects as go
except Exception:  # pragma: no cover
    go = None  # type: ignore

# =====================================================
# CONFIGURATION PAGE (Toujours en première ligne)
# =====================================================
st.set_page_config(
    page_title="Analyse de Données Crédit",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =====================================================
# VARIABLES D'ENVIRONNEMENT
# =====================================================
load_dotenv()
MONGODB_URI = os.getenv("MONGODB_URI")
API_BASE_URL = os.getenv("FLASK_API_URL")
DEFAULT_JOB_ID = os.getenv("DATAVIZ_JOB_ID")

# =====================================================
# STYLE CSS PROFESSIONNEL
# =====================================================
st.markdown(
    """
<style>
/* Page padding */
.block-container { padding-top: 1.2rem; padding-bottom: 2.5rem; }

/* Sidebar */
section[data-testid="stSidebar"] .stMarkdown { color: #1f2a44; }

.sidebar-card {
    background: white;
    border-radius: 14px;
    padding: 14px 14px 10px 14px;
    border: 1px solid rgba(31,42,68,0.08);
    box-shadow: 0 8px 20px rgba(31,42,68,0.05);
}
.sidebar-title { font-weight: 700; font-size: 14px; letter-spacing: .4px; color: #1f2a44; }
.sidebar-sub { font-size: 12px; color: rgba(31,42,68,0.70); margin-top: 4px; }

/* Top info bar */
.info-bar {
    background: linear-gradient(90deg, #1d4f91 0%, #2a6fbe 100%);
    border-radius: 14px;
    padding: 12px 14px;
    color: white;
    font-size: 13px;
    display: flex;
    align-items: center;
    justify-content: space-between;
}
.info-bar .pill {
    background: rgba(255,255,255,0.15);
    padding: 6px 10px;
    border-radius: 999px;
    font-size: 12px;
}

/* KPI strip */
.kpi-strip {
    background: #eef1fb;
    border-radius: 14px;
    padding: 14px;
    border: 1px solid rgba(31,42,68,0.06);
}
.kpi-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; }
.kpi {
    background: rgba(255,255,255,0.75);
    border: 1px solid rgba(31,42,68,0.06);
    border-radius: 12px;
    padding: 12px;
}
.kpi .v { font-weight: 800; font-size: 18px; color: #2a4a80; }
.kpi .l { font-size: 11px; color: rgba(31,42,68,0.70); margin-top: 2px; text-transform: uppercase; letter-spacing: .3px; }

/* Section cards */
.section-card {
    background: white;
    border-radius: 16px;
    padding: 16px;
    border: 1px solid rgba(31,42,68,0.08);
    box-shadow: 0 10px 26px rgba(31,42,68,0.06);
}
.section-title { font-weight: 800; font-size: 16px; color: #1f2a44; margin-bottom: 6px; }
.section-sub { font-size: 12px; color: rgba(31,42,68,0.70); margin-bottom: 10px; }

/* Recommendations */
.reco-wrap {
    background: #ecebff;
    border-radius: 16px;
    padding: 16px;
    border: 1px solid rgba(80, 70, 200, 0.12);
}
.reco-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.reco-col h4 { margin: 0 0 6px 0; font-size: 13px; color: #1f2a44; }
.reco-col ul { margin: 0; padding-left: 18px; color: rgba(31,42,68,0.85); font-size: 12px; }

/* Logo circulaire RB */
.rb-logo-circle {
    background-color: #1E4A8E;
    color: white;
    border-radius: 50%;
    width: 80px; height: 80px;
    display: flex; align-items: center; justify-content: center;
    font-weight: bold; font-size: 26px;
    margin: 0 auto 10px auto;
    box-shadow: 0 4px 10px rgba(0,0,0,0.2);
}
</style>
""",
    unsafe_allow_html=True,
)

# =====================================================
# PAGE ANALYSE
# =====================================================

THEMES = {
    1: {"label": "💼 Ancienneté d'emploi", "desc": "Corrélation entre la durée d’emploi et le risque de défaut."},
    2: {"label": "💰💸 Ratio crédit/revenu", "desc": "Évaluation de la relation entre ratio crédit/revenu et probabilité de défaut."},
    3: {"label": "🏦 DemandES de crédit", "desc": "Analyse des caractéristiques de demandes de crédit et leur impact sur le défaut."},
    4: {"label": "📝 Contrat et propriété", "desc": "Lien entre type de contrat, statut immobilier et taux de défaut."},
    5: {"label": "👨‍👩‍👧 Famille et enfants", "desc": "Influence de la structure familiale sur le risque de défaut."},
    6: {"label": "📅 Jour de demande", "desc": "Variation du taux de défaut selon le jour/période de demande."},
    7: {"label": "🏠 Logement & stabilité", "desc": "Impact des conditions de logement sur le risque."},
    8: {"label": "📊 Profil financier", "desc": "Analyse des segments financiers et indicateurs associés au défaut."},
}

DEFAULT_ANALYSIS_TYPE = 2  # Parcours 2: option 2 par défaut

# -----------------------------
# Gestion d'erreurs
# -----------------------------
def _http_get(url: str, params: Dict[str, Any], timeout: int = 120) -> requests.Response:
    return requests.get(url, params=params, timeout=timeout)

# Test connexion API
def check_api_health() -> Tuple[bool, str]:
    try:
        r = _http_get(f"{API_BASE_URL}/health", params={}, timeout=10)
        if r.status_code == 200:
            return True, "OK"
        return False, f"HTTP {r.status_code}: {r.text[:200]}"
    except Exception as e:
        return False, str(e)

# Transforme du HTML généré par Plotly (fig.to_html) en un objet
def extract_plotly_figure_from_html(html: str):
    """
    app.py renvoie fig.to_html(full_html=True). On tente d'extraire (data, layout) depuis Plotly.newPlot().
    Si on y arrive, on reconstruit une Figure pour st.plotly_chart (meilleur rendu).
    Sinon, on renvoie None.
    """
    if go is None:
        return None

    # Plotly.newPlot("div_id", [{"..."}], {"...layout..."}, {"responsive": true})
    m = re.search(r"Plotly\.newPlot\(\s*\"[^\"]+\"\s*,\s*(\[[\s\S]*?\])\s*,\s*({[\s\S]*?})\s*,\s*({[\s\S]*?})\s*\)\s*;", html)
    if not m:
        # guillemets simples
        m = re.search(r"Plotly\.newPlot\(\s*\'[^\']+\'\s*,\s*(\[[\s\S]*?\])\s*,\s*({[\s\S]*?})\s*,\s*({[\s\S]*?})\s*\)\s*;", html)
    if not m:
        return None

    data_json, layout_json, _config_json = m.group(1), m.group(2), m.group(3)

    try:
        data = json.loads(data_json)
        layout = json.loads(layout_json)
        fig = go.Figure(data=data, layout=layout)
        return fig
    except Exception:
        return None

# Calcule automatiquement des KPI à partir d’un graphique Plotly (fig)
def compute_kpis_from_fig(fig) -> Dict[str, Optional[float]]:
    """
    KPI auto à partir des traces:
    - clients_analyzed: somme des tailles de séries (approx)
    - avg_default_rate: moyenne des y (si y est un taux)
    - avg_ratio: moyenne des x (si x est un ratio)
    - avg_credit: si une série s'appelle credit/amt -> best effort
    """
    k = {"clients_analyzed": None, "avg_default_rate": None, "avg_ratio": None, "avg_credit": None}

    try:
        xs: List[float] = []
        ys: List[float] = []
        n = 0
        for tr in fig.data:
            x = getattr(tr, "x", None)
            y = getattr(tr, "y", None)
            # ignore les valeurs nulles, convertit en float et ajoute à la liste globale
            if x is not None:
                xs += [float(v) for v in x if v is not None and str(v) != "nan"]
            if y is not None:
                ys += [float(v) for v in y if v is not None and str(v) != "nan"]
            if x is not None:
                n = max(n, len(x))
            elif y is not None:
                n = max(n, len(y))

        if n > 0:
            k["clients_analyzed"] = float(n)

        if ys:
            k["avg_default_rate"] = sum(ys) / len(ys)

        if xs:
            k["avg_ratio"] = sum(xs) / len(xs)
            
    except Exception:
        pass

    return k

# Formate une valeur numérique en pourcentage lisible
def fmt_pct(v: Optional[float]) -> str:
    if v is None:
        return "—"
    # valeur entre 0 et 1
    if v <= 1.0:
        return f"{v*100:.1f}%"
    return f"{v:.1f}%"

# Formate une valeur numérique en deux chiffres apès la virgule
def fmt_ratio(v: Optional[float]) -> str:
    if v is None:
        return "—"
    return f"{v:.2f}"

# Formate une valeur numérique en €
def fmt_k(v: Optional[float]) -> str:
    if v is None:
        return "—"
    if v >= 1000:
        return f"{v/1000:.0f} K€"
    return f"{v:.0f}"

# Sidebar Spécifique
st.sidebar.markdown('<div class="rb-logo-circle">RB</div>', unsafe_allow_html=True)
st.sidebar.markdown("<h2 style='text-align:center; color:#1E4A8E; margin-top:0;'>Risk Banking</h2>", unsafe_allow_html=True)
st.sidebar.markdown("---")

st.sidebar.markdown(
    """
    <h2 style='text-align:center; color:#1E4A8E; margin:0; padding:0;'>📊 THÉMATIQUE D'ANALYSE</h2> 
    """,
    unsafe_allow_html=True,
)
st.sidebar.write("")

analysis_type = st.sidebar.radio(
    label="",
    options=list(THEMES.keys()),
    format_func=lambda k: THEMES[k]["label"],
    index=list(THEMES.keys()).index(DEFAULT_ANALYSIS_TYPE),
)
st.sidebar.write("")

st.sidebar.markdown('<div class="sidebar-card"><div class="sidebar-title">🔎 FILTRES D\'ANALYSE</div></div>', unsafe_allow_html=True)
min_credit = st.sidebar.number_input("Montant min. crédit (€)", min_value=0.0, value=5000.0, step=500.0)
max_credit = st.sidebar.number_input("Montant max. crédit (€)", min_value=0.0, value=50000.0, step=500.0)
min_income = st.sidebar.number_input("Revenu annuel min. (€)", min_value=0.0, value=20000.0, step=500.0)

st.sidebar.write("")

go_btn = st.sidebar.button("📊 Générer l'analyse", type="primary", use_container_width=True)

if go_btn :
    job_id = locals().get("job_id") or DEFAULT_JOB_ID

    # -----------------------------
    # Main header
    # -----------------------------
    st.markdown("## Analyse de Données Crédit")
    st.caption("Explorez les facteurs qui influencent le risque de défaut via des analyses thématiques et filtres.")


    # KPI strip (filled after analysis)
    kpi_placeholder = st.empty()

    # -----------------------------
    # Run analysis
    # -----------------------------
    def run_analysis() -> Tuple[Optional[str], Optional[Any], Optional[str]]:
        """
        Returns: (raw_html, fig, error)
        """
        job_id='000000'
        params = {
            "job_id": job_id,
            "analysis_type": int(analysis_type),
            "min_credit": float(min_credit),
            "max_credit": float(max_credit),
            "min_income": float(min_income),
        }

        try:
            with st.spinner("Génération de l'analyse (appel API /get_dataviz)…"):
                r = _http_get(f"{API_BASE_URL}/get_dataviz", params=params, timeout=180)
            if r.status_code != 200:
                return None, None, f"Erreur API /get_dataviz: HTTP {r.status_code} — {r.text[:400]}"
            html = r.text
            fig = extract_plotly_figure_from_html(html)
            return html, fig, None
        except Exception as e:
            return None, None, f"Erreur de connexion à l'API: {e}"

    # Auto-run once to avoid "nothing happens" if user forgets click
    if "auto_ran" not in st.session_state:
        st.session_state.auto_ran = False

    if go_btn or (not st.session_state.auto_ran):
        st.session_state.auto_ran = True
        raw_html, fig, err = run_analysis()

        if err:
            st.error(err)
            st.stop()

        # KPI block
        if fig is not None:
            k = compute_kpis_from_fig(fig)
            clients = k["clients_analyzed"]
            avg_def = k["avg_default_rate"]
            avg_ratio = k["avg_ratio"]
            avg_credit = k["avg_credit"]

            kpi_placeholder.markdown(
                f"""
    <div class="kpi-strip">
    <div class="kpi-grid">
        <div class="kpi"><div class="v">{int(clients) if clients else "—"}</div><div class="l">Clients analysés</div></div>
        <div class="kpi"><div class="v">{fmt_pct(avg_def)}</div><div class="l">Taux de défaut moyen</div></div>
        <div class="kpi"><div class="v">{fmt_ratio(avg_ratio)}</div><div class="l">Ratio crédit/revenu moyen</div></div>
        <div class="kpi"><div class="v">{fmt_k(avg_credit)}</div><div class="l">Montant moyen crédit</div></div>
    </div>
    </div>
    """,
                unsafe_allow_html=True,
            )
        else:
            kpi_placeholder.markdown(
                """
    <div class="kpi-strip">
    <div class="kpi-grid">
        <div class="kpi"><div class="v">—</div><div class="l">Clients analysés</div></div>
        <div class="kpi"><div class="v">—</div><div class="l">Taux de défaut moyen</div></div>
        <div class="kpi"><div class="v">—</div><div class="l">Ratio crédit/revenu moyen</div></div>
        <div class="kpi"><div class="v">—</div><div class="l">Montant moyen crédit</div></div>
    </div>
    </div>
    """,
                unsafe_allow_html=True,
            )

        st.write("")

        # Chart + Insights layout
        left, right = st.columns([1.45, 1.0], gap="large")

        with left:
            st.markdown(
                f"""
    <div class="section-card">
    <div class="section-title">{THEMES[analysis_type]["label"]}</div>
    <div class="section-sub">{THEMES[analysis_type]["desc"]}</div>
    </div>
    """,
                unsafe_allow_html=True,
            )
            st.write("")

            if fig is not None:
                st.plotly_chart(fig, use_container_width=True)
            else:
                # fallback: render html as-is
                from streamlit.components.v1 import html as st_html
                st_html(raw_html, height=560, scrolling=True)

        with right:
            st.markdown(
                """
    <div class="section-card">
    <div class="section-title">📌 Indicateurs clés</div>
    <div class="section-sub">Synthèse automatique (best effort) basée sur la visualisation.</div>
    </div>
    """,
                unsafe_allow_html=True,
            )
            st.write("")

            if fig is not None:
                k = compute_kpis_from_fig(fig)
                st.metric("Clients analysés", int(k["clients_analyzed"]) if k["clients_analyzed"] else "—")
                st.metric("Taux de défaut moyen", fmt_pct(k["avg_default_rate"]))
                st.metric("Ratio moyen", fmt_ratio(k["avg_ratio"]))
            else:
                st.info("Impossible d'extraire les indicateurs du graphique (HTML brut).")

            st.write("")

        st.write("")
        st.markdown(
            """
    <div class="reco-wrap">
    <div class="section-title">💡 Recommandations</div>
    <div class="reco-grid">
        <div class="reco-col">
        <h4>Recommandations opérationnelles</h4>
        <ul>
            <li>Ajuster les exigences de garantie sur les segments à risque.</li>
            <li>Proposer des taux d’intérêt adaptés au profil identifié.</li>
            <li>Mettre en place un suivi spécifique pour les segments à haut risque.</li>
            <li>Réviser périodiquement les critères d’octroi selon les analyses.</li>
        </ul>
        </div>
        <div class="reco-col">
        <h4>Actions stratégiques</h4>
        <ul>
            <li>Intégrer ces variables dans les modèles de scoring.</li>
            <li>Développer des parcours client différenciés selon le niveau de risque.</li>
            <li>Établir un reporting mensuel sur l’évolution des indicateurs clés.</li>
            <li>Former les équipes commerciales à l’interprétation des analyses.</li>
        </ul>
        </div>
    </div>
    </div>
    """,
            unsafe_allow_html=True,
        )

    else:
        # Initial KPI empty
        kpi_placeholder.markdown(
            """
    <div class="kpi-strip">
    <div class="kpi-grid">
        <div class="kpi"><div class="v">—</div><div class="l">Clients analysés</div></div>
        <div class="kpi"><div class="v">—</div><div class="l">Taux de défaut moyen</div></div>
        <div class="kpi"><div class="v">—</div><div class="l">Ratio crédit/revenu moyen</div></div>
        <div class="kpi"><div class="v">—</div><div class="l">Montant moyen crédit</div></div>
    </div>
    </div>
    """,
            unsafe_allow_html=True,
        )
else:
    st.markdown(
        """
        <h2 style='padding:.4em;'></h2> 
        """,
        unsafe_allow_html=True,
    )
    st.info("💡 Sélectionnez une thématique, appliquez les filtres puis appuyez sur le bouton générer l'analyse.")