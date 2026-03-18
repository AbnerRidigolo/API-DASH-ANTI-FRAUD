"""
dashboard.py — Dashboard Interativo Anti-Fraude Mission Brasil
Streamlit + Plotly

Rodar:
  streamlit run dashboard.py

Requer a API rodando em http://localhost:8000
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import pandas as pd
from datetime import datetime

# ── Configuração da página ───────────────────────────────────────────────────

st.set_page_config(
    page_title="Mission Brasil — Anti-Fraude Dashboard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS Customizado ──────────────────────────────────────────────────────────

st.markdown("""
<style>
    /* ── Importar fonte ── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

    /* ── Root variables ── */
    :root {
        --bg-primary: #0a0e1a;
        --bg-card: #111827;
        --bg-card-hover: #1a2332;
        --accent-blue: #3b82f6;
        --accent-cyan: #06b6d4;
        --accent-green: #10b981;
        --accent-yellow: #f59e0b;
        --accent-red: #ef4444;
        --accent-purple: #8b5cf6;
        --text-primary: #f1f5f9;
        --text-secondary: #94a3b8;
        --border-color: #1e293b;
    }

    /* ══════════════════════════════════════════════════════════════════════
       FORCE DARK BACKGROUND ON ALL STREAMLIT ELEMENTS
       ══════════════════════════════════════════════════════════════════════ */

    /* ── Global app ── */
    .stApp,
    .stApp > header,
    .main .block-container {
        background-color: #0a0e1a !important;
        color: #e2e8f0 !important;
        font-family: 'Inter', sans-serif !important;
    }

    /* ── Main content area ── */
    .main,
    .main > div,
    [data-testid="stAppViewContainer"],
    [data-testid="stAppViewBlockContainer"],
    [data-testid="stVerticalBlock"],
    [data-testid="stHorizontalBlock"],
    [data-testid="stMainBlockContainer"] {
        background-color: #0a0e1a !important;
    }

    /* ── All column containers ── */
    [data-testid="stColumn"],
    [data-testid="stColumn"] > div,
    [data-testid="stColumn"] > div > div {
        background-color: transparent !important;
    }

    /* ── Plotly chart wrappers — kill any white bg ── */
    .stPlotlyChart,
    .stPlotlyChart > div,
    .stPlotlyChart iframe,
    [data-testid="stPlotlyChart"],
    .js-plotly-plot,
    .plot-container,
    .plotly,
    .svg-container {
        background-color: #0a0e1a !important;
        background: #0a0e1a !important;
    }

    /* ── Expander ── */
    [data-testid="stExpander"],
    [data-testid="stExpander"] > div,
    [data-testid="stExpander"] details,
    [data-testid="stExpander"] summary,
    .streamlit-expanderHeader,
    .streamlit-expanderContent {
        background-color: #111827 !important;
        color: #e2e8f0 !important;
        border-color: #1e293b !important;
    }
    [data-testid="stExpander"] summary span {
        color: #c7d2fe !important;
        font-weight: 600 !important;
    }

    /* ── All text / markdown / labels ── */
    .stMarkdown,
    .stMarkdown p,
    .stMarkdown li,
    .stMarkdown span,
    .stText,
    label,
    .stTextInput label,
    .stNumberInput label,
    .stSelectbox label,
    .stMultiSelect label,
    .stSlider label,
    [data-testid="stWidgetLabel"],
    [data-testid="stWidgetLabel"] p {
        color: #cbd5e1 !important;
    }

    /* ── Headings across the app ── */
    h1, h2, h3, h4, h5, h6 {
        color: #e0e7ff !important;
    }

    /* ── Input widgets (text, number, select) ── */
    .stTextInput input,
    .stNumberInput input,
    .stSelectbox > div > div,
    .stMultiSelect > div > div,
    [data-testid="stTextInput"] input,
    [data-testid="stNumberInput"] input {
        background-color: #1e293b !important;
        color: #e2e8f0 !important;
        border-color: #334155 !important;
    }
    .stTextInput input:focus,
    .stNumberInput input:focus {
        border-color: #6366f1 !important;
        box-shadow: 0 0 0 1px #6366f1 !important;
    }

    /* ── Select / Multiselect dropdowns ── */
    [data-baseweb="select"],
    [data-baseweb="select"] > div,
    [data-baseweb="popover"],
    [data-baseweb="popover"] > div,
    [data-baseweb="menu"],
    [data-baseweb="menu"] ul,
    [data-baseweb="menu"] li {
        background-color: #1e293b !important;
        color: #e2e8f0 !important;
    }
    [data-baseweb="menu"] li:hover {
        background-color: #334155 !important;
    }
    [data-baseweb="tag"] {
        background-color: #312e81 !important;
        color: #c7d2fe !important;
    }

    /* ── Slider ── */
    .stSlider [data-testid="stThumbValue"],
    .stSlider span {
        color: #cbd5e1 !important;
    }

    /* ── Buttons ── */
    .stButton > button {
        background: linear-gradient(135deg, #4f46e5, #6366f1) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        transition: all 0.2s ease !important;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #6366f1, #818cf8) !important;
        box-shadow: 0 4px 15px rgba(99,102,241,0.3) !important;
        transform: translateY(-1px) !important;
    }

    /* ── Dividers ── */
    hr,
    [data-testid="stDivider"] {
        border-color: #1e293b !important;
    }

    /* ── Sidebar ── */
    section[data-testid="stSidebar"],
    section[data-testid="stSidebar"] > div,
    section[data-testid="stSidebar"] > div > div {
        background: linear-gradient(180deg, #0f172a, #1e1b4b) !important;
        border-right: 1px solid #1e293b !important;
    }
    section[data-testid="stSidebar"] .stMarkdown,
    section[data-testid="stSidebar"] .stMarkdown p,
    section[data-testid="stSidebar"] .stMarkdown span,
    section[data-testid="stSidebar"] label {
        color: #c7d2fe !important;
    }
    section[data-testid="stSidebar"] .stMarkdown h1,
    section[data-testid="stSidebar"] .stMarkdown h2,
    section[data-testid="stSidebar"] .stMarkdown h3 {
        color: #e0e7ff !important;
    }
    section[data-testid="stSidebar"] .stMarkdown strong {
        color: #a5b4fc !important;
    }

    /* ── Alerts / info / warning / error ── */
    [data-testid="stAlert"],
    .stAlert {
        background-color: #1e293b !important;
        color: #e2e8f0 !important;
        border-color: #334155 !important;
    }

    /* ══════════════════════════════════════════════════════════════════════
       COMPONENT-SPECIFIC STYLES (unchanged logic, enhanced colors)
       ══════════════════════════════════════════════════════════════════════ */

    /* ── Header ── */
    .dashboard-header {
        background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #0f172a 100%);
        border: 1px solid rgba(99, 102, 241, 0.2);
        border-radius: 16px;
        padding: 28px 36px;
        margin-bottom: 24px;
        position: relative;
        overflow: hidden;
    }
    .dashboard-header::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 3px;
        background: linear-gradient(90deg, #3b82f6, #8b5cf6, #06b6d4);
    }
    .dashboard-header h1 {
        font-size: 28px;
        font-weight: 800;
        background: linear-gradient(135deg, #e0e7ff, #c7d2fe);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0 0 4px 0;
        letter-spacing: -0.5px;
    }
    .dashboard-header p {
        color: #94a3b8;
        font-size: 14px;
        margin: 0;
        font-weight: 400;
    }

    /* ── KPI Cards ── */
    .kpi-card {
        background: linear-gradient(145deg, #111827, #1a2332);
        border: 1px solid #1e293b;
        border-radius: 14px;
        padding: 22px 24px;
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    .kpi-card:hover {
        border-color: rgba(99, 102, 241, 0.4);
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.3);
    }
    .kpi-card::after {
        content: '';
        position: absolute;
        top: 0; left: 0;
        width: 4px;
        height: 100%;
        border-radius: 14px 0 0 14px;
    }
    .kpi-card.blue::after   { background: linear-gradient(180deg, #3b82f6, #2563eb); }
    .kpi-card.green::after  { background: linear-gradient(180deg, #10b981, #059669); }
    .kpi-card.yellow::after { background: linear-gradient(180deg, #f59e0b, #d97706); }
    .kpi-card.red::after    { background: linear-gradient(180deg, #ef4444, #dc2626); }
    .kpi-card.purple::after { background: linear-gradient(180deg, #8b5cf6, #7c3aed); }
    .kpi-card.cyan::after   { background: linear-gradient(180deg, #06b6d4, #0891b2); }

    .kpi-label {
        font-size: 12px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
        color: #94a3b8;
        margin-bottom: 8px;
    }
    .kpi-value {
        font-size: 32px;
        font-weight: 800;
        letter-spacing: -1px;
        line-height: 1;
        margin-bottom: 6px;
    }
    .kpi-value.blue   { color: #60a5fa; }
    .kpi-value.green  { color: #34d399; }
    .kpi-value.yellow { color: #fbbf24; }
    .kpi-value.red    { color: #f87171; }
    .kpi-value.purple { color: #a78bfa; }
    .kpi-value.cyan   { color: #22d3ee; }

    .kpi-sub {
        font-size: 12px;
        color: #64748b;
        font-weight: 500;
    }

    /* ── Section titles ── */
    .section-title {
        font-size: 18px;
        font-weight: 700;
        color: #e2e8f0 !important;
        margin: 32px 0 16px 0;
        padding-bottom: 10px;
        border-bottom: 2px solid #1e293b;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .section-title .icon {
        font-size: 22px;
    }

    /* ── Chart container ── */
    .chart-container {
        background: linear-gradient(145deg, #111827, #0f1629);
        border: 1px solid #1e293b;
        border-radius: 14px;
        padding: 20px;
        margin-bottom: 16px;
    }

    /* ── Status badges ── */
    .badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .badge-ok        { background: rgba(16,185,129,0.15); color: #34d399; border: 1px solid rgba(16,185,129,0.3); }
    .badge-atencao   { background: rgba(245,158,11,0.15); color: #fbbf24; border: 1px solid rgba(245,158,11,0.3); }
    .badge-suspeito  { background: rgba(249,115,22,0.15); color: #fb923c; border: 1px solid rgba(249,115,22,0.3); }
    .badge-bloqueado { background: rgba(239,68,68,0.15);  color: #f87171; border: 1px solid rgba(239,68,68,0.3); }

    /* ── Table styling ── */
    .dataframe {
        font-family: 'Inter', sans-serif !important;
        font-size: 13px !important;
        background-color: #111827 !important;
        color: #e2e8f0 !important;
    }

    /* ── Pulse animation for critical alerts ── */
    @keyframes pulse-glow {
        0%, 100% { box-shadow: 0 0 5px rgba(239,68,68,0.3); }
        50%      { box-shadow: 0 0 20px rgba(239,68,68,0.6); }
    }
    .alert-critical {
        animation: pulse-glow 2s infinite;
        border-color: rgba(239,68,68,0.5) !important;
    }

    /* ── Hide Streamlit defaults ── */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    header { visibility: hidden; }

    /* ── Metric delta styling ── */
    [data-testid="stMetricDelta"] {
        font-weight: 600;
    }

    /* ── Extra: scrollbar ── */
    ::-webkit-scrollbar { width: 8px; height: 8px; }
    ::-webkit-scrollbar-track { background: #0a0e1a; }
    ::-webkit-scrollbar-thumb { background: #334155; border-radius: 4px; }
    ::-webkit-scrollbar-thumb:hover { background: #475569; }
</style>
""", unsafe_allow_html=True)


# ── Constantes ───────────────────────────────────────────────────────────────

API_BASE = "http://localhost:8000"

CORES_NIVEL = {
    "ok":        "#10b981",
    "atencao":   "#f59e0b",
    "suspeito":  "#f97316",
    "bloqueado": "#ef4444",
}

LABELS_NIVEL = {
    "ok":        "✅ OK",
    "atencao":   "⚠️ Atenção",
    "suspeito":  "🔶 Suspeito",
    "bloqueado": "🔴 Bloqueado",
}

PLOTLY_TEMPLATE = "plotly_dark"


# ── Funções de dados ─────────────────────────────────────────────────────────

@st.cache_data(ttl=30)
def fetch_report():
    """Busca relatório resumido da API."""
    try:
        r = requests.get(f"{API_BASE}/report", timeout=5)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"❌ Erro ao conectar à API: {e}")
        return None


@st.cache_data(ttl=30)
def fetch_mission_units(nivel=None, min_score=0, max_score=100, limit=100):
    """Busca mission units da API com filtros."""
    try:
        params = {"min_score": min_score, "max_score": max_score, "limit": limit}
        if nivel:
            params["fraud_nivel"] = nivel
        r = requests.get(f"{API_BASE}/mission-units", params=params, timeout=5)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"❌ Erro ao buscar MUs: {e}")
        return []


# ── Sidebar ──────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## 🛡️ Anti-Fraude")
    st.markdown("**Mission Brasil**")
    st.divider()

    st.markdown("### 🎯 Filtros")

    filtro_nivel = st.multiselect(
        "Nível de Risco",
        options=["ok", "atencao", "suspeito", "bloqueado"],
        default=["ok", "atencao", "suspeito", "bloqueado"],
        format_func=lambda x: LABELS_NIVEL.get(x, x),
    )

    filtro_score = st.slider(
        "Faixa de Score",
        min_value=0.0,
        max_value=100.0,
        value=(0.0, 100.0),
        step=1.0,
    )

    st.divider()

    if st.button("🔄 Atualizar Dados", use_container_width=True, type="primary"):
        st.cache_data.clear()
        st.rerun()

    st.divider()
    st.markdown(
        f"<p style='color:#475569; font-size:11px; text-align:center;'>"
        f"Última atualização<br>{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
        f"</p>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p style='color:#334155; font-size:10px; text-align:center;'>v1.0 · Streamlit + Plotly</p>",
        unsafe_allow_html=True,
    )


# ── Header ───────────────────────────────────────────────────────────────────

st.markdown("""
<div class="dashboard-header">
    <h1>🛡️ Anti-Fraude Dashboard</h1>
    <p>Monitoramento em tempo real de Mission Units — Staff on Demand | Mission Brasil</p>
</div>
""", unsafe_allow_html=True)


# ── Carregar dados ───────────────────────────────────────────────────────────

report = fetch_report()

if report is None:
    st.warning(
        "⚠️ Não foi possível conectar à API. "
        "Certifique-se que está rodando: `uvicorn app:app --reload --port 8000`"
    )
    st.stop()

all_mus = fetch_mission_units(min_score=filtro_score[0], max_score=filtro_score[1])
df_mus = pd.DataFrame(all_mus)

if not df_mus.empty and filtro_nivel:
    df_mus = df_mus[df_mus["fraud_nivel"].isin(filtro_nivel)]


# ── KPI Cards ────────────────────────────────────────────────────────────────

st.markdown('<div class="section-title"><span class="icon">📊</span> Indicadores Principais</div>', unsafe_allow_html=True)

kpi1, kpi2, kpi3, kpi4, kpi5, kpi6 = st.columns(6)

with kpi1:
    st.markdown(f"""
    <div class="kpi-card blue">
        <div class="kpi-label">Total MUs</div>
        <div class="kpi-value blue">{report['total_mus']}</div>
        <div class="kpi-sub">Mission Units analisadas</div>
    </div>
    """, unsafe_allow_html=True)

with kpi2:
    st.markdown(f"""
    <div class="kpi-card green">
        <div class="kpi-label">Aprovadas</div>
        <div class="kpi-value green">{report['ok']}</div>
        <div class="kpi-sub">{report['ok']/report['total_mus']*100:.0f}% do total</div>
    </div>
    """, unsafe_allow_html=True)

with kpi3:
    st.markdown(f"""
    <div class="kpi-card yellow">
        <div class="kpi-label">Atenção</div>
        <div class="kpi-value yellow">{report['atencao']}</div>
        <div class="kpi-sub">Revisão leve</div>
    </div>
    """, unsafe_allow_html=True)

with kpi4:
    st.markdown(f"""
    <div class="kpi-card red">
        <div class="kpi-label">Suspeito + Bloqueado</div>
        <div class="kpi-value red">{report['suspeito'] + report['bloqueado']}</div>
        <div class="kpi-sub">{report['taxa_fraude_pct']}% taxa de fraude</div>
    </div>
    """, unsafe_allow_html=True)

with kpi5:
    st.markdown(f"""
    <div class="kpi-card purple">
        <div class="kpi-label">Valor Total</div>
        <div class="kpi-value purple">R$ {report['valor_total_rs']:,.0f}</div>
        <div class="kpi-sub">Em recompensas</div>
    </div>
    """, unsafe_allow_html=True)

with kpi6:
    alert_class = "alert-critical" if report['valor_em_risco_rs'] > 500 else ""
    st.markdown(f"""
    <div class="kpi-card cyan {alert_class}">
        <div class="kpi-label">💰 Valor em Risco</div>
        <div class="kpi-value cyan">R$ {report['valor_em_risco_rs']:,.0f}</div>
        <div class="kpi-sub">Pagamentos sob análise</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)


# ── Gráficos Linha 1: Distribuição + Gauge ──────────────────────────────────

st.markdown('<div class="section-title"><span class="icon">📈</span> Análise de Risco</div>', unsafe_allow_html=True)

col_donut, col_gauge, col_hist = st.columns([1, 1, 1.3])

# ── Donut: Distribuição por nível ──
with col_donut:
    niveis_data = {
        "Nível": ["OK", "Atenção", "Suspeito", "Bloqueado"],
        "Quantidade": [report["ok"], report["atencao"], report["suspeito"], report["bloqueado"]],
    }
    df_niveis = pd.DataFrame(niveis_data)

    fig_donut = px.pie(
        df_niveis,
        names="Nível",
        values="Quantidade",
        hole=0.55,
        color="Nível",
        color_discrete_map={
            "OK":        "#10b981",
            "Atenção":   "#f59e0b",
            "Suspeito":  "#f97316",
            "Bloqueado": "#ef4444",
        },
    )
    fig_donut.update_layout(
        template=PLOTLY_TEMPLATE,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter", color="#94a3b8"),
        title=dict(text="Distribuição por Nível de Risco", font=dict(size=15, color="#e2e8f0")),
        legend=dict(
            orientation="h",
            yanchor="bottom", y=-0.2,
            xanchor="center", x=0.5,
            font=dict(size=11),
        ),
        margin=dict(t=50, b=50, l=20, r=20),
        height=380,
    )
    fig_donut.update_traces(
        textinfo="percent+value",
        textfont=dict(size=12, color="white"),
        marker=dict(line=dict(color="#0a0e1a", width=2)),
    )
    st.plotly_chart(fig_donut, use_container_width=True)


# ── Gauge: Taxa de Fraude ──
with col_gauge:
    taxa = report["taxa_fraude_pct"]

    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=taxa,
        number=dict(suffix="%", font=dict(size=42, color="#e2e8f0", family="Inter")),
        delta=dict(reference=15, valueformat=".1f", suffix="%"),
        title=dict(text="Taxa de Fraude", font=dict(size=15, color="#e2e8f0", family="Inter")),
        gauge=dict(
            axis=dict(range=[0, 50], tickcolor="#475569", tickfont=dict(size=10, color="#64748b")),
            bar=dict(color="#8b5cf6", thickness=0.3),
            bgcolor="rgba(30,41,59,0.5)",
            borderwidth=0,
            steps=[
                dict(range=[0, 10],  color="rgba(16,185,129,0.2)"),
                dict(range=[10, 25], color="rgba(245,158,11,0.2)"),
                dict(range=[25, 40], color="rgba(249,115,22,0.2)"),
                dict(range=[40, 50], color="rgba(239,68,68,0.2)"),
            ],
            threshold=dict(
                line=dict(color="#ef4444", width=3),
                thickness=0.8,
                value=taxa,
            ),
        ),
    ))
    fig_gauge.update_layout(
        template=PLOTLY_TEMPLATE,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter"),
        margin=dict(t=80, b=30, l=30, r=30),
        height=380,
    )
    st.plotly_chart(fig_gauge, use_container_width=True)


# ── Histograma: Distribuição de Scores ──
with col_hist:
    if not df_mus.empty:
        fig_hist = px.histogram(
            df_mus,
            x="fraud_score",
            nbins=20,
            color="fraud_nivel",
            color_discrete_map=CORES_NIVEL,
            labels={"fraud_score": "Fraud Score", "fraud_nivel": "Nível", "count": "Qtd"},
            category_orders={"fraud_nivel": ["ok", "atencao", "suspeito", "bloqueado"]},
        )
        fig_hist.update_layout(
            template=PLOTLY_TEMPLATE,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter", color="#94a3b8"),
            title=dict(text="Distribuição de Fraud Scores", font=dict(size=15, color="#e2e8f0")),
            xaxis=dict(
                title="Score",
                gridcolor="rgba(30,41,59,0.5)",
                zerolinecolor="rgba(30,41,59,0.5)",
            ),
            yaxis=dict(
                title="Quantidade",
                gridcolor="rgba(30,41,59,0.5)",
                zerolinecolor="rgba(30,41,59,0.5)",
            ),
            legend=dict(
                orientation="h",
                yanchor="bottom", y=-0.25,
                xanchor="center", x=0.5,
                font=dict(size=11),
            ),
            bargap=0.08,
            margin=dict(t=50, b=60, l=20, r=20),
            height=380,
        )
        st.plotly_chart(fig_hist, use_container_width=True)
    else:
        st.info("Nenhum dado para exibir com os filtros selecionados.")


# ── Gráficos Linha 2: Top Flags + Valor por Missão ──────────────────────────

st.markdown('<div class="section-title"><span class="icon">🚩</span> Flags & Impacto Financeiro</div>', unsafe_allow_html=True)

col_flags, col_valor = st.columns([1, 1])

# ── Top Flags ──
with col_flags:
    top_flags = report.get("top_flags", [])
    if top_flags:
        df_flags = pd.DataFrame(top_flags)

        labels_map = {
            "checkin_antes_criacao": "Check-in antes da criação",
            "duracao_zero":         "Duração zero",
            "checkout_antecipado":  "Checkout antecipado",
            "gps_fora_do_local":    "GPS fora do local",
            "gps_checkout_divergente": "GPS divergente",
            "historico_reprovacoes": "Histórico reprovações",
            "atividades_ausentes":  "Atividades ausentes",
            "checkout_antes_checkin": "Checkout antes check-in",
            "duracao_impossivel":   "Duração impossível",
        }
        df_flags["flag_label"] = df_flags["flag"].map(labels_map).fillna(df_flags["flag"])

        fig_flags = go.Figure()

        fig_flags.add_trace(go.Bar(
            y=df_flags["flag_label"],
            x=df_flags["ocorrencias"],
            orientation="h",
            name="Ocorrências",
            marker=dict(
                color=df_flags["ocorrencias"],
                colorscale=[[0, "#3b82f6"], [0.5, "#8b5cf6"], [1, "#ef4444"]],
                line=dict(width=0),
                cornerradius=6,
            ),
            text=df_flags["ocorrencias"],
            textposition="auto",
            textfont=dict(color="white", size=13, family="Inter"),
        ))

        fig_flags.update_layout(
            template=PLOTLY_TEMPLATE,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter", color="#94a3b8"),
            title=dict(text="Top Flags Mais Frequentes", font=dict(size=15, color="#e2e8f0")),
            xaxis=dict(
                title="Ocorrências",
                gridcolor="rgba(30,41,59,0.5)",
                zerolinecolor="rgba(30,41,59,0.5)",
            ),
            yaxis=dict(
                autorange="reversed",
                tickfont=dict(size=12),
            ),
            showlegend=False,
            margin=dict(t=50, b=40, l=10, r=20),
            height=400,
        )
        st.plotly_chart(fig_flags, use_container_width=True)


# ── Impacto Financeiro por Flag ──
with col_valor:
    if top_flags:
        df_flags["flag_label"] = df_flags["flag"].map(labels_map).fillna(df_flags["flag"])

        fig_impacto = go.Figure()

        fig_impacto.add_trace(go.Bar(
            y=df_flags["flag_label"],
            x=df_flags["impacto_rs"],
            orientation="h",
            name="Impacto R$",
            marker=dict(
                color=df_flags["impacto_rs"],
                colorscale=[[0, "#06b6d4"], [0.5, "#f59e0b"], [1, "#ef4444"]],
                line=dict(width=0),
                cornerradius=6,
            ),
            text=[f"R$ {v:,.0f}" for v in df_flags["impacto_rs"]],
            textposition="auto",
            textfont=dict(color="white", size=12, family="Inter"),
        ))

        fig_impacto.update_layout(
            template=PLOTLY_TEMPLATE,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter", color="#94a3b8"),
            title=dict(text="Impacto Financeiro por Flag (R$)", font=dict(size=15, color="#e2e8f0")),
            xaxis=dict(
                title="Valor em R$",
                gridcolor="rgba(30,41,59,0.5)",
                zerolinecolor="rgba(30,41,59,0.5)",
            ),
            yaxis=dict(
                autorange="reversed",
                tickfont=dict(size=12),
            ),
            showlegend=False,
            margin=dict(t=50, b=40, l=10, r=20),
            height=400,
        )
        st.plotly_chart(fig_impacto, use_container_width=True)


# ── Gráfico Linha 3: Scatter Score vs Recompensa ────────────────────────────

st.markdown('<div class="section-title"><span class="icon">🔍</span> Análise Detalhada</div>', unsafe_allow_html=True)

if not df_mus.empty:
    col_scatter, col_box = st.columns([1.4, 1])

    with col_scatter:
        fig_scatter = px.scatter(
            df_mus,
            x="fraud_score",
            y="recompensa_rs",
            color="fraud_nivel",
            size="n_flags",
            size_max=18,
            color_discrete_map=CORES_NIVEL,
            hover_data=["mu_id", "missionario_nome", "missao_nome", "status"],
            labels={
                "fraud_score": "Fraud Score",
                "recompensa_rs": "Recompensa (R$)",
                "fraud_nivel": "Nível",
                "n_flags": "Nº Flags",
            },
            category_orders={"fraud_nivel": ["ok", "atencao", "suspeito", "bloqueado"]},
        )

        # Zona de risco
        fig_scatter.add_shape(
            type="rect",
            x0=45, x1=100, y0=0, y1=df_mus["recompensa_rs"].max() * 1.1,
            fillcolor="rgba(239,68,68,0.06)",
            line=dict(width=0),
            layer="below",
        )
        fig_scatter.add_annotation(
            x=72.5, y=df_mus["recompensa_rs"].max() * 1.05,
            text="⚠️ ZONA DE RISCO",
            font=dict(size=11, color="#f87171", family="Inter"),
            showarrow=False,
        )

        fig_scatter.update_layout(
            template=PLOTLY_TEMPLATE,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter", color="#94a3b8"),
            title=dict(text="Score de Fraude vs Recompensa", font=dict(size=15, color="#e2e8f0")),
            xaxis=dict(
                gridcolor="rgba(30,41,59,0.5)",
                zerolinecolor="rgba(30,41,59,0.5)",
            ),
            yaxis=dict(
                gridcolor="rgba(30,41,59,0.5)",
                zerolinecolor="rgba(30,41,59,0.5)",
                tickprefix="R$ ",
            ),
            legend=dict(
                orientation="h",
                yanchor="bottom", y=-0.2,
                xanchor="center", x=0.5,
            ),
            margin=dict(t=50, b=60, l=20, r=20),
            height=420,
        )
        st.plotly_chart(fig_scatter, use_container_width=True)

    with col_box:
        fig_box = px.box(
            df_mus,
            x="fraud_nivel",
            y="fraud_score",
            color="fraud_nivel",
            color_discrete_map=CORES_NIVEL,
            labels={"fraud_nivel": "Nível", "fraud_score": "Score"},
            category_orders={"fraud_nivel": ["ok", "atencao", "suspeito", "bloqueado"]},
            points="all",
        )
        fig_box.update_layout(
            template=PLOTLY_TEMPLATE,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter", color="#94a3b8"),
            title=dict(text="Box Plot — Score por Nível", font=dict(size=15, color="#e2e8f0")),
            xaxis=dict(gridcolor="rgba(30,41,59,0.5)"),
            yaxis=dict(gridcolor="rgba(30,41,59,0.5)"),
            showlegend=False,
            margin=dict(t=50, b=40, l=20, r=20),
            height=420,
        )
        st.plotly_chart(fig_box, use_container_width=True)


# ── Tabela: MUs Críticas ────────────────────────────────────────────────────

st.markdown('<div class="section-title"><span class="icon">🚨</span> Mission Units Críticas</div>', unsafe_allow_html=True)

criticas = report.get("mus_criticas", [])
if criticas:
    df_criticas = pd.DataFrame(criticas)

    # Badge HTML
    def nivel_badge(nivel):
        label = LABELS_NIVEL.get(nivel, nivel)
        return f'<span class="badge badge-{nivel}">{label}</span>'

    # Score com barra visual
    def score_bar(score):
        if score <= 20:   cor = "#10b981"
        elif score <= 45: cor = "#f59e0b"
        elif score <= 70: cor = "#f97316"
        else:             cor = "#ef4444"
        return (
            f'<div style="display:flex; align-items:center; gap:8px;">'
            f'<div style="background:rgba(30,41,59,0.5); border-radius:4px; width:80px; height:8px;">'
            f'<div style="background:{cor}; height:100%; width:{score}%; border-radius:4px;"></div>'
            f'</div>'
            f'<span style="color:{cor}; font-weight:700; font-size:13px;">{score}</span>'
            f'</div>'
        )

    html_rows = ""
    for _, row in df_criticas.iterrows():
        html_rows += f"""
        <tr>
            <td style="color:#60a5fa; font-weight:600;">{row['mu_id']}</td>
            <td>{row['missionario_nome']}</td>
            <td>{row['missao_nome']}</td>
            <td style="text-align:right; color:#a78bfa; font-weight:600;">R$ {row['recompensa_rs']:,.0f}</td>
            <td>{score_bar(row['fraud_score'])}</td>
            <td>{nivel_badge(row['fraud_nivel'])}</td>
            <td style="text-align:center; font-weight:600; color:#f87171;">{row['n_flags']}</td>
        </tr>
        """

    st.markdown(f"""
    <div style="overflow-x:auto; border-radius:12px; border:1px solid #1e293b;">
    <table style="width:100%; border-collapse:collapse; font-family:'Inter',sans-serif; font-size:13px;">
        <thead>
            <tr style="background:linear-gradient(135deg,#1e1b4b,#1e293b); border-bottom:2px solid #312e81;">
                <th style="padding:14px 16px; text-align:left; color:#a5b4fc; font-weight:700; font-size:11px; text-transform:uppercase; letter-spacing:1px;">MU ID</th>
                <th style="padding:14px 16px; text-align:left; color:#a5b4fc; font-weight:700; font-size:11px; text-transform:uppercase; letter-spacing:1px;">Missionário</th>
                <th style="padding:14px 16px; text-align:left; color:#a5b4fc; font-weight:700; font-size:11px; text-transform:uppercase; letter-spacing:1px;">Missão</th>
                <th style="padding:14px 16px; text-align:right; color:#a5b4fc; font-weight:700; font-size:11px; text-transform:uppercase; letter-spacing:1px;">Valor</th>
                <th style="padding:14px 16px; text-align:left; color:#a5b4fc; font-weight:700; font-size:11px; text-transform:uppercase; letter-spacing:1px;">Score</th>
                <th style="padding:14px 16px; text-align:left; color:#a5b4fc; font-weight:700; font-size:11px; text-transform:uppercase; letter-spacing:1px;">Nível</th>
                <th style="padding:14px 16px; text-align:center; color:#a5b4fc; font-weight:700; font-size:11px; text-transform:uppercase; letter-spacing:1px;">Flags</th>
            </tr>
        </thead>
        <tbody>
            {html_rows}
        </tbody>
    </table>
    </div>
    <style>
        table tbody tr {{
            border-bottom: 1px solid #1e293b;
            transition: background 0.2s;
        }}
        table tbody tr:hover {{
            background: rgba(99, 102, 241, 0.08) !important;
        }}
        table tbody td {{
            padding: 12px 16px;
            color: #cbd5e1;
        }}
    </style>
    """, unsafe_allow_html=True)
else:
    st.success("✅ Nenhuma MU crítica no momento!")


# ── Seção: Simulador de Análise ──────────────────────────────────────────────

st.markdown("<br>", unsafe_allow_html=True)
st.markdown('<div class="section-title"><span class="icon">🧪</span> Simulador de Análise Anti-Fraude</div>', unsafe_allow_html=True)

with st.expander("🔬 Abrir Simulador — Teste uma MU em tempo real", expanded=False):
    st.markdown("Preencha os campos abaixo para analisar uma Mission Unit em tempo real via API.")

    sim_c1, sim_c2 = st.columns(2)

    with sim_c1:
        st.markdown("##### 📋 Dados da Missão")
        sim_mu_id = st.text_input("MU ID", value="MU-TEST-001")
        sim_missao_nome = st.text_input("Nome da Missão", value="Hostess | Turnos de 8h")
        sim_duracao = st.number_input("Duração Esperada (horas)", value=8.0, min_value=0.5, step=0.5)
        sim_recompensa = st.number_input("Recompensa (R$)", value=140.0, min_value=0.0, step=10.0)

    with sim_c2:
        st.markdown("##### 👤 Dados do Missionário")
        sim_nome = st.text_input("Nome", value="João Silva")
        sim_historico = st.number_input("Missões no histórico", value=10, min_value=0)
        sim_reprovacoes = st.number_input("Reprovações", value=1, min_value=0)

    st.markdown("##### 📍 Localização & Atividades")
    sim_lat = st.number_input("Latitude do local", value=-23.5718, format="%.4f")
    sim_lng = st.number_input("Longitude do local", value=-46.6858, format="%.4f")

    st.markdown("---")
    st.markdown("**Configurar cenário de atividades:**")

    cenario = st.selectbox("Cenário pré-configurado", [
        "Normal — tudo ok",
        "Suspeito — check-in antes da criação",
        "Fraude — duração zero",
        "Fraude — GPS fora do local",
    ])

    if cenario == "Normal — tudo ok":
        atividades = [
            {"tipo": "check_in",  "timestamp": "2026-03-17T09:00:00", "lat": sim_lat, "lng": sim_lng},
            {"tipo": "iniciou",   "timestamp": "2026-03-17T09:05:00", "lat": sim_lat, "lng": sim_lng},
            {"tipo": "finalizou", "timestamp": "2026-03-17T17:00:00", "lat": sim_lat, "lng": sim_lng},
            {"tipo": "check_out", "timestamp": "2026-03-17T17:05:00", "lat": sim_lat, "lng": sim_lng},
        ]
    elif cenario == "Suspeito — check-in antes da criação":
        atividades = [
            {"tipo": "check_in",  "timestamp": "2026-03-16T08:00:00", "lat": sim_lat, "lng": sim_lng},
            {"tipo": "iniciou",   "timestamp": "2026-03-17T09:05:00", "lat": sim_lat, "lng": sim_lng},
            {"tipo": "finalizou", "timestamp": "2026-03-17T17:00:00", "lat": sim_lat, "lng": sim_lng},
            {"tipo": "check_out", "timestamp": "2026-03-17T17:05:00", "lat": sim_lat, "lng": sim_lng},
        ]
    elif cenario == "Fraude — duração zero":
        atividades = [
            {"tipo": "check_in",  "timestamp": "2026-03-17T09:00:00", "lat": sim_lat, "lng": sim_lng},
            {"tipo": "iniciou",   "timestamp": "2026-03-17T09:27:00", "lat": sim_lat, "lng": sim_lng},
            {"tipo": "finalizou", "timestamp": "2026-03-17T09:27:00", "lat": sim_lat, "lng": sim_lng},
            {"tipo": "check_out", "timestamp": "2026-03-17T09:30:00", "lat": sim_lat, "lng": sim_lng},
        ]
    else:  # GPS fora do local
        atividades = [
            {"tipo": "check_in",  "timestamp": "2026-03-17T09:00:00", "lat": sim_lat + 0.05, "lng": sim_lng + 0.05},
            {"tipo": "iniciou",   "timestamp": "2026-03-17T09:05:00", "lat": sim_lat + 0.05, "lng": sim_lng + 0.05},
            {"tipo": "finalizou", "timestamp": "2026-03-17T17:00:00", "lat": sim_lat + 0.05, "lng": sim_lng + 0.05},
            {"tipo": "check_out", "timestamp": "2026-03-17T17:05:00", "lat": sim_lat + 0.1, "lng": sim_lng + 0.1},
        ]

    if st.button("🚀 Executar Análise", type="primary", use_container_width=True):
        payload = {
            "mu_id": sim_mu_id,
            "status": "Validando Dados",
            "missao": {
                "id": "MB-SIM-001",
                "nome": sim_missao_nome,
                "descricao": "Missão simulada via dashboard",
                "duracao_esperada_horas": sim_duracao,
                "criado_em": "2026-03-17T09:00:00",
                "recompensa": {"dinheiro": sim_recompensa, "pontos": 0},
                "assinatura": "FREE",
            },
            "missionario": {
                "id": "USR-SIM-001",
                "nome": sim_nome,
                "historico_missoes": sim_historico,
                "historico_reprovacoes": sim_reprovacoes,
            },
            "localizacao": {
                "endereco": "Simulação — Dashboard",
                "lat": sim_lat,
                "lng": sim_lng,
            },
            "atividades": atividades,
        }

        try:
            resp = requests.post(f"{API_BASE}/analyze", json=payload, timeout=5)
            resp.raise_for_status()
            result = resp.json()

            # Resultado
            score = result["fraud_score"]
            nivel = result["fraud_nivel"]

            if score <= 20:   cor = "#10b981"
            elif score <= 45: cor = "#f59e0b"
            elif score <= 70: cor = "#f97316"
            else:             cor = "#ef4444"

            st.markdown(f"""
            <div style="background:linear-gradient(145deg,#111827,#1a2332); border:1px solid {cor}40;
                        border-radius:14px; padding:24px; margin-top:16px;">
                <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap;">
                    <div>
                        <div style="font-size:12px; color:#64748b; font-weight:600; text-transform:uppercase; letter-spacing:1px;">
                            Resultado da Análise
                        </div>
                        <div style="font-size:48px; font-weight:800; color:{cor}; line-height:1.1; margin-top:4px;">
                            {score}
                        </div>
                        <div style="margin-top:4px;">
                            <span class="badge badge-{nivel}">{LABELS_NIVEL.get(nivel, nivel)}</span>
                        </div>
                    </div>
                    <div style="text-align:right;">
                        <div style="color:#94a3b8; font-size:13px;">{result['recomendacao']}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Flags
            if result.get("flags"):
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("**🚩 Flags Detectadas:**")
                for f in result["flags"]:
                    st.markdown(
                        f"- **`{f['regra']}`** — {f['descricao']} "
                        f"*(+{f['pontos']} pts)*"
                    )
            else:
                st.success("✅ Nenhuma flag detectada — MU limpa!")

        except Exception as e:
            st.error(f"❌ Erro ao chamar a API: {e}")


# ── Footer ───────────────────────────────────────────────────────────────────

st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("""
<div style="text-align:center; padding:20px; border-top:1px solid #1e293b; color:#334155; font-size:12px;">
    Mission Brasil — Anti-Fraude Dashboard v1.0 · Powered by Streamlit + Plotly<br>
    Dados atualizados em tempo real via API FastAPI
</div>
""", unsafe_allow_html=True)
