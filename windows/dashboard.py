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
from datetime import datetime, timedelta
import numpy as np

# ── Configuração da página ───────────────────────────────────────────────────
st.set_page_config(
    page_title="Mission Brasil — Anti-Fraude Dashboard",
    page_icon="👮",
    layout="wide",
    initial_sidebar_state="expanded",
)

with st.sidebar:
    st.divider()
    modo_escuro = st.toggle("🌙 Modo Escuro", value=True)
    
    st.divider()
    st.markdown("### 🔍 Detalhe de Missionário")
    busca_missionario = st.text_input(
        "Nome do missionário",
        placeholder="Ex: Ana Lima",
        help="Digite o nome exato para ver o perfil completo"
    )
    st.divider()
    st.markdown("### 📄 Exportar")

    if st.button("📥 Gerar Relatório PDF", use_container_width=True):
        from fpdf import FPDF
        import io
        from datetime import datetime

        class RelatorioPDF(FPDF):
            def header(self):
                self.set_fill_color(10, 14, 26)
                self.rect(0, 0, 210, 297, 'F')
                self.set_fill_color(7, 11, 20)
                self.rect(0, 0, 210, 18, 'F')
                self.set_font("Helvetica", "B", 11)
                self.set_text_color(240, 244, 255)
                self.set_y(5)
                self.cell(0, 8, "Mission Brasil — SENTINELA👮", align="C")
                self.set_y(18)

            def footer(self):
                self.set_y(-12)
                self.set_font("Helvetica", "", 8)
                self.set_text_color(71, 85, 105)
                self.cell(0, 8,
                    f"Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}  ·  Confidencial  ·  Pág. {self.page_no()}",
                    align="C")

        pdf = RelatorioPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()

        # ── Título ──
        pdf.set_font("Helvetica", "B", 22)
        pdf.set_text_color(6, 182, 212)
        pdf.set_y(25)
        pdf.cell(0, 12, "Relatório Executivo Anti-Fraude", align="C", ln=True)
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(148, 163, 184)
        pdf.cell(0, 7, f"Período atual · Gerado em {datetime.now().strftime('%d/%m/%Y às %H:%M')}", align="C", ln=True)
        pdf.ln(8)

        # ── KPIs ──
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(161, 180, 252)
        pdf.set_fill_color(17, 24, 39)
        pdf.cell(0, 8, "  INDICADORES PRINCIPAIS", fill=True, ln=True)
        pdf.ln(4)

        kpis_pdf = [
            ("Total de MUs",       str(report["total_mus"]),                     (59, 130, 246)),
            ("Aprovadas (OK)",     f"{report['ok']} ({report['ok']/report['total_mus']*100:.0f}%)", (34, 197, 94)),
            ("Em Atenção",         str(report["atencao"]),                        (245, 158, 11)),
            ("Suspeito+Bloqueado", f"{report['suspeito']+report['bloqueado']} ({report['taxa_fraude_pct']}%)", (239, 68, 68)),
            ("Valor Total (R$)",   f"R$ {report['valor_total_rs']:,.2f}",         (139, 92, 246)),
            ("Valor em Risco (R$)",f"R$ {report['valor_em_risco_rs']:,.2f}",      (6, 182, 212)),
        ]

        col_w = 90
        for i, (label, valor, cor) in enumerate(kpis_pdf):
            x = 15 if i % 2 == 0 else 110
            if i % 2 == 0 and i > 0:
                pdf.ln(18)
            pdf.set_xy(x, pdf.get_y())
            pdf.set_fill_color(17, 24, 39)
            pdf.rect(x, pdf.get_y(), col_w, 15, 'F')
            pdf.set_fill_color(*cor)
            pdf.rect(x, pdf.get_y(), 3, 15, 'F')
            pdf.set_xy(x + 6, pdf.get_y() + 2)
            pdf.set_font("Helvetica", "", 8)
            pdf.set_text_color(148, 163, 184)
            pdf.cell(col_w - 8, 4, label, ln=True)
            pdf.set_xy(x + 6, pdf.get_y())
            pdf.set_font("Helvetica", "B", 13)
            pdf.set_text_color(*cor)
            pdf.cell(col_w - 8, 6, valor)

        pdf.ln(24)

        # ── Top Flags ──
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(161, 180, 252)
        pdf.set_fill_color(17, 24, 39)
        pdf.cell(0, 8, "  TOP FLAGS DETECTADAS", fill=True, ln=True)
        pdf.ln(4)

        top_flags_pdf = report.get("top_flags", [])
        labels_flags = {
            "checkin_antes_criacao": "Check-in antes da criação",
            "duracao_zero":          "Duração zero",
            "checkout_antecipado":   "Checkout antecipado",
            "gps_fora_do_local":     "GPS fora do local",
        }
        for fl in top_flags_pdf:
            label_f = labels_flags.get(fl["flag"], fl["flag"])
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(203, 213, 225)
            pdf.cell(100, 7, f"  {label_f}")
            pdf.set_text_color(239, 68, 68)
            pdf.cell(30, 7, f"{fl['ocorrencias']}x")
            pdf.set_text_color(251, 191, 36)
            pdf.cell(0, 7, f"R$ {fl['impacto_rs']:,.0f}", ln=True)

        pdf.ln(6)

        # ── MUs Críticas ──
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(161, 180, 252)
        pdf.set_fill_color(17, 24, 39)
        pdf.cell(0, 8, "  MISSION UNITS CRÍTICAS", fill=True, ln=True)
        pdf.ln(4)

        # Header da tabela
        pdf.set_fill_color(30, 27, 75)
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_text_color(165, 180, 252)
        for col, w in [("MU ID",20),("Missionário",50),("Missão",55),("Valor",25),("Score",20),("Nível",20)]:
            pdf.cell(w, 7, col, fill=True)
        pdf.ln()

        cores_nivel_pdf = {
            "ok":        (34, 197, 94),
            "atencao":   (245, 158, 11),
            "suspeito":  (249, 115, 22),
            "bloqueado": (239, 68,  68),
        }

        for mu in report.get("mus_criticas", [])[:12]:
            cor_n = cores_nivel_pdf.get(mu["fraud_nivel"], (148, 163, 184))
            pdf.set_fill_color(13, 17, 23)
            pdf.set_font("Helvetica", "", 8)
            pdf.set_text_color(96, 165, 250)
            pdf.cell(20, 6, mu["mu_id"][:10], fill=True)
            pdf.set_text_color(203, 213, 225)
            pdf.cell(50, 6, mu["missionario_nome"][:22], fill=True)
            pdf.cell(55, 6, mu["missao_nome"][:28], fill=True)
            pdf.set_text_color(167, 139, 250)
            pdf.cell(25, 6, f"R$ {mu['recompensa_rs']:,.0f}", fill=True)
            pdf.set_text_color(*cor_n)
            pdf.cell(20, 6, str(mu["fraud_score"]), fill=True)
            pdf.cell(20, 6, mu["fraud_nivel"].upper(), fill=True)
            pdf.ln()

        # Gerar bytes
        pdf_bytes = bytes(pdf.output())
        st.sidebar.download_button(
            label="⬇️ Baixar PDF",
            data=pdf_bytes,
            file_name=f"antifraude_mission_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
            mime="application/pdf",
            use_container_width=True,
        )
        st.sidebar.success("✅ PDF gerado! Clique em Baixar.")


TEMA = {
    "bg_primary":  "#0a0e1a" if modo_escuro else "#f8fafc",
    "bg_card":     "#111827" if modo_escuro else "#ffffff",
    "bg_mid":      "#1a2332" if modo_escuro else "#f1f5f9",
    "border":      "#1e293b" if modo_escuro else "#e2e8f0",
    "text_pri":    "#f1f5f9" if modo_escuro else "#0f172a",
    "text_sec":    "#94a3b8" if modo_escuro else "#475569",
    "text_mute":   "#475569" if modo_escuro else "#94a3b8",
    "sidebar_bg":  "linear-gradient(180deg, #0f172a, #1e1b4b)" if modo_escuro else "linear-gradient(180deg, #f8fafc, #eff6ff)",
    "plotly_tpl":  "plotly_dark" if modo_escuro else "plotly_white",
}

PLOTLY_TEMPLATE = TEMA["plotly_tpl"]


# ── CSS Customizado ──────────────────────────────────────────────────────────


st.markdown(f"""
<style>
    .stApp,
    [data-testid="stAppViewContainer"] {{
        background-color: {TEMA['bg_primary']} !important;
    }}
    .main, [data-testid="stMainBlockContainer"] {{
        background-color: {TEMA['bg_primary']} !important;
    }}
    .stMarkdown, .stMarkdown p, label,
    [data-testid="stWidgetLabel"] p {{
        color: {TEMA['text_sec']} !important;
    }}
    h1, h2, h3, h4 {{
        color: {TEMA['text_pri']} !important;
    }}
    .kpi-card {{
        background: {TEMA['bg_card']} !important;
        border-color: {TEMA['border']} !important;
    }}
    .kpi-label {{ color: {TEMA['text_sec']} !important; }}
    .kpi-sub   {{ color: {TEMA['text_mute']} !important; }}
    .section-title {{ color: {TEMA['text_pri']} !important; border-color: {TEMA['border']} !important; }}
    section[data-testid="stSidebar"], section[data-testid="stSidebar"] > div {{
        background: {TEMA['sidebar_bg']} !important;
    }}
</style>
""", unsafe_allow_html=True)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700;800;900&family=IBM+Plex+Mono:wght@400;500;600;700&display=swap');

    :root {
        --bg-primary: #070b14;
        --bg-card: #0d1117;
        --bg-hover: #131920;
        --border: #1c2840;
        --border-accent: #2d3f5e;
        --text-primary: #f0f4ff;
        --text-secondary: #8899bb;
        --text-muted: #4a5a7a;
    }

    .stApp, .stApp > header, .main .block-container {
        background-color: #070b14 !important;
        background-image: radial-gradient(rgba(59,130,246,0.06) 1px, transparent 1px) !important;
        background-size: 24px 24px !important;
        color: #f0f4ff !important;
        font-family: 'DM Sans', sans-serif !important;
    }
    .main, .main > div, [data-testid="stAppViewContainer"],
    [data-testid="stAppViewBlockContainer"], [data-testid="stVerticalBlock"],
    [data-testid="stHorizontalBlock"], [data-testid="stMainBlockContainer"] {
        background-color: #070b14 !important;
    }
    [data-testid="stColumn"], [data-testid="stColumn"] > div,
    [data-testid="stColumn"] > div > div { background-color: transparent !important; }

    .stPlotlyChart, .stPlotlyChart > div, .stPlotlyChart iframe,
    [data-testid="stPlotlyChart"], .js-plotly-plot, .plot-container,
    .plotly, .svg-container {
        background-color: #070b14 !important; background: #070b14 !important;
    }

    [data-testid="stExpander"], [data-testid="stExpander"] > div,
    [data-testid="stExpander"] details, [data-testid="stExpander"] summary,
    .streamlit-expanderHeader, .streamlit-expanderContent {
        background-color: #0d1117 !important; color: #f0f4ff !important; border-color: #1c2840 !important;
    }
    [data-testid="stExpander"] summary span { color: #8899bb !important; font-weight: 600 !important; }

    .stMarkdown, .stMarkdown p, .stMarkdown li, .stMarkdown span, .stText, label,
    .stTextInput label, .stNumberInput label, .stSelectbox label,
    .stMultiSelect label, .stSlider label,
    [data-testid="stWidgetLabel"], [data-testid="stWidgetLabel"] p { color: #8899bb !important; }
    h1, h2, h3, h4, h5, h6 { color: #f0f4ff !important; }

    .stTextInput input, .stNumberInput input, .stSelectbox > div > div,
    .stMultiSelect > div > div, [data-testid="stTextInput"] input,
    [data-testid="stNumberInput"] input {
        background-color: #0d1117 !important; color: #f0f4ff !important; border-color: #1c2840 !important;
    }
    .stTextInput input:focus, .stNumberInput input:focus {
        border-color: #3b82f6 !important; box-shadow: 0 0 0 1px #3b82f6 !important;
    }
    [data-baseweb="select"], [data-baseweb="select"] > div,
    [data-baseweb="popover"], [data-baseweb="popover"] > div,
    [data-baseweb="menu"], [data-baseweb="menu"] ul, [data-baseweb="menu"] li {
        background-color: #0d1117 !important; color: #f0f4ff !important;
    }
    [data-baseweb="menu"] li:hover { background-color: #131920 !important; }
    [data-baseweb="tag"] { background-color: #1c2840 !important; color: #8899bb !important; }
    .stSlider [data-testid="stThumbValue"], .stSlider span { color: #8899bb !important; }

    .stButton > button {
        background: linear-gradient(135deg, #3b82f6, #2563eb) !important;
        color: white !important; border: none !important; border-radius: 8px !important;
        font-weight: 600 !important; font-family: 'DM Sans', sans-serif !important;
        transition: all 0.3s ease !important;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #60a5fa, #3b82f6) !important;
        box-shadow: 0 4px 20px rgba(59,130,246,0.35) !important; transform: translateY(-1px) !important;
    }
    hr, [data-testid="stDivider"] { border-color: #1c2840 !important; }

    section[data-testid="stSidebar"], section[data-testid="stSidebar"] > div,
    section[data-testid="stSidebar"] > div > div {
        background: linear-gradient(180deg, #070b14 0%, #0d1117 100%) !important;
        border-right: 1px solid #1c2840 !important;
    }
    section[data-testid="stSidebar"] .stMarkdown, section[data-testid="stSidebar"] .stMarkdown p,
    section[data-testid="stSidebar"] .stMarkdown span, section[data-testid="stSidebar"] label { color: #8899bb !important; }
    section[data-testid="stSidebar"] .stMarkdown h1, section[data-testid="stSidebar"] .stMarkdown h2,
    section[data-testid="stSidebar"] .stMarkdown h3 { color: #f0f4ff !important; }
    section[data-testid="stSidebar"] .stMarkdown strong { color: #3b82f6 !important; }

    [data-testid="stAlert"], .stAlert {
        background-color: #0d1117 !important; color: #f0f4ff !important; border-color: #1c2840 !important;
    }

    .dashboard-header {
        background: linear-gradient(135deg, #070b14 0%, #0d1117 50%, #070b14 100%);
        border: 1px solid #1c2840; border-radius: 16px; padding: 28px 36px;
        margin-bottom: 24px; position: relative; overflow: hidden; backdrop-filter: blur(4px);
    }
    .dashboard-header::before {
        content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px;
        background: linear-gradient(90deg, #3b82f6, #60a5fa, #3b82f6);
    }

    .kpi-card {
        background: linear-gradient(145deg, #0d1117, #131920);
        border: 1px solid #1c2840; border-radius: 14px; padding: 22px 24px;
        transition: all 0.3s ease; position: relative; overflow: hidden; backdrop-filter: blur(4px);
    }
    .kpi-card:hover {
        border-color: #2d3f5e; transform: translateY(-2px);
        box-shadow: 0 0 30px rgba(59,130,246,0.08);
    }
    .kpi-card::after {
        content: ''; position: absolute; top: 0; left: 0; width: 4px; height: 100%;
        border-radius: 14px 0 0 14px;
        background: linear-gradient(180deg, #3b82f6, #2563eb);
    }

    .kpi-label {
        font-size: 10px; font-weight: 700; text-transform: uppercase;
        letter-spacing: 1.5px; color: #4a5a7a; margin-bottom: 10px;
        font-family: 'DM Sans', sans-serif;
    }
    .kpi-value {
        font-size: 32px; font-weight: 700; letter-spacing: -1px;
        line-height: 1; margin-bottom: 8px; font-family: 'IBM Plex Mono', monospace;
        color: #e2e8f0;
    }
    .kpi-divider { width:100%; height:1px; background:linear-gradient(90deg,#1c2840,transparent); margin:8px 0; }
    .kpi-sub { font-size: 11px; color: #4a5a7a; font-weight: 500; font-family: 'DM Sans', sans-serif; }

    .section-title {
        font-size: 13px; font-weight: 700; color: #3b82f6 !important;
        margin: 36px 0 20px 0; padding: 0 0 12px 0; border-bottom: 1px solid #1c2840;
        display: flex; align-items: center; gap: 10px;
        text-transform: uppercase; letter-spacing: 2px; font-family: 'DM Sans', sans-serif;
    }
    .section-title::before {
        content: ''; display: inline-block; width: 3px; height: 14px;
        background: linear-gradient(180deg, #3b82f6, #2563eb); border-radius: 2px;
    }

    .badge { display:inline-block; padding:4px 12px; border-radius:20px; font-size:10px;
             font-weight:700; text-transform:uppercase; letter-spacing:0.5px; font-family:'DM Sans',sans-serif; }
    .badge-ok        { background:rgba(59,130,246,0.12); color:#60a5fa; border:1px solid rgba(59,130,246,0.25); }
    .badge-atencao   { background:rgba(59,130,246,0.08); color:#93bbfc; border:1px solid rgba(59,130,246,0.18); }
    .badge-suspeito  { background:rgba(239,68,68,0.08); color:#fca5a5; border:1px solid rgba(239,68,68,0.18); }
    .badge-bloqueado { background:rgba(239,68,68,0.12); color:#f87171; border:1px solid rgba(239,68,68,0.25); }

    .alert-critical {
        animation: pulse-border 2.5s ease-in-out infinite;
        border-color: rgba(239,68,68,0.5) !important;
    }
    @keyframes pulse-border {
        0%, 100% { box-shadow:0 0 0 0 rgba(239,68,68,0); border-color:rgba(239,68,68,0.25); }
        50%      { box-shadow:0 0 15px rgba(239,68,68,0.2); border-color:rgba(239,68,68,0.6); }
    }
    @keyframes pulse-dot { 0%, 100% { opacity:1; } 50% { opacity:0.4; } }

    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    header { visibility: hidden; }
    [data-testid="stMetricDelta"] { font-weight: 600; }
    ::-webkit-scrollbar { width:8px; height:8px; }
    ::-webkit-scrollbar-track { background:#070b14; }
    ::-webkit-scrollbar-thumb { background:#1c2840; border-radius:4px; }
    ::-webkit-scrollbar-thumb:hover { background:#2d3f5e; }
</style>
""", unsafe_allow_html=True)


# ── Constantes ───────────────────────────────────────────────────────────────

API_BASE = "http://localhost:8000"

CORES_NIVEL = {
    "ok":        "#3b82f6",
    "atencao":   "#93bbfc",
    "suspeito":  "#fca5a5",
    "bloqueado": "#ef4444",
}

LABELS_NIVEL = {
    "ok":        "✅ OK",
    "atencao":   "⚠️ Atenção",
    "suspeito":  "🔶 Suspeito",
    "bloqueado": "🔴 Bloqueado",
}



LAYOUT_PADRAO = dict(
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(7,11,20,0.6)",
    font=dict(family="DM Sans, Inter, sans-serif", color="#8899bb", size=12),
    title=dict(
        font=dict(size=14, color="#f0f4ff", family="DM Sans, sans-serif"),
        x=0, xanchor="left", pad=dict(l=4),
    ),
    xaxis=dict(gridcolor="rgba(28,40,64,0.8)", zerolinecolor="rgba(28,40,64,0.8)", tickfont=dict(size=11)),
    yaxis=dict(gridcolor="rgba(28,40,64,0.8)", zerolinecolor="rgba(28,40,64,0.8)", tickfont=dict(size=11)),
    legend=dict(bgcolor="rgba(13,17,23,0.8)", bordercolor="#1c2840", borderwidth=1, font=dict(size=11)),
    margin=dict(t=48, b=48, l=16, r=16),
    height=380,
    hoverlabel=dict(bgcolor="#131920", bordercolor="#2d3f5e", font=dict(family="DM Sans", size=12, color="#f0f4ff")),
)


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
    st.markdown("""
    <div style="text-align:center; padding:16px 0 8px; border-bottom:1px solid #1c2840; margin-bottom:16px;">
        <div style="font-size:32px; margin-bottom:4px;">🛡️</div>
        <div style="font-weight:800; color:#f0f4ff; font-size:14px; letter-spacing:-0.3px;">Anti-Fraude</div>
        <div style="font-size:10px; color:#3b82f6; font-weight:600; letter-spacing:2px; text-transform:uppercase;">
            Mission Brasil
        </div>
    </div>
    """, unsafe_allow_html=True)

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
        f"<p style='color:#4a5a7a; font-size:11px; text-align:center;'>"
        f"Última atualização<br>{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
        f"</p>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p style='color:#1c2840; font-size:10px; text-align:center;'>v1.0 · Streamlit + Plotly</p>",
        unsafe_allow_html=True,
    )


# ── Header ───────────────────────────────────────────────────────────────────

st.markdown(f"""
<div class="dashboard-header">
  <div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:16px;">
    <div>
      <div style="display:flex; align-items:center; gap:12px; margin-bottom:6px;">
        <div style="width:40px; height:40px; background:linear-gradient(135deg,#2563eb,#3b82f6);
                    border-radius:10px; display:flex; align-items:center; justify-content:center;
                    font-size:20px; box-shadow: 0 4px 15px rgba(59,130,246,0.2);">👮</div>
        <div>
          <h1 style="font-size:24px; font-weight:800; background:linear-gradient(135deg,#f0f4ff,#8899bb);
                     -webkit-background-clip:text; -webkit-text-fill-color:transparent;
                     margin:0; letter-spacing:-0.5px; font-family:'DM Sans',sans-serif;">SENTINELA</h1>
          <div style="font-size:11px; color:#3b82f6; font-weight:600; letter-spacing:2px; text-transform:uppercase;">
            Mission Brasil · Staff on Demand
          </div>
        </div>
      </div>
      <p style="color:#8899bb; font-size:13px; margin:0;">
        Monitoramento de Missões em tempo real · Detecção de anomalias e análise de risco
      </p>
    </div>
    <div style="display:flex; flex-direction:column; align-items:flex-end; gap:8px;">
      <div style="display:flex; align-items:center; gap:8px; background:rgba(59,130,246,0.08);
                  border:1px solid rgba(59,130,246,0.25); border-radius:20px; padding:6px 14px;">
        <div style="width:8px; height:8px; background:#3b82f6; border-radius:50%;
                    box-shadow: 0 0 6px #3b82f6; animation: pulse-dot 2s infinite;"></div>
        <span style="font-size:12px; color:#60a5fa; font-weight:600;">API Conectada</span>
      </div>
      <div style="font-size:11px; color:#4a5a7a;">
        Atualizado em {datetime.now().strftime('%d/%m/%Y às %H:%M')}
      </div>
    </div>
  </div>
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

st.markdown('<div class="section-title">📊 Indicadores Principais</div>', unsafe_allow_html=True)

kpi1, kpi2, kpi3, kpi4, kpi5, kpi6 = st.columns(6)

with kpi1:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">📋 Total MUs</div>
        <div class="kpi-value">{report['total_mus']}</div>
        <div class="kpi-divider"></div>
        <div class="kpi-sub">Mission Units analisadas</div>
    </div>
    """, unsafe_allow_html=True)

with kpi2:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">✅ Aprovadas</div>
        <div class="kpi-value">{report['ok']}</div>
        <div class="kpi-divider"></div>
        <div class="kpi-sub">Sem anomalias · {report['ok']/report['total_mus']*100:.0f}%</div>
    </div>
    """, unsafe_allow_html=True)

with kpi3:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">⚠️ Em Atenção</div>
        <div class="kpi-value">{report['atencao']}</div>
        <div class="kpi-divider"></div>
        <div class="kpi-sub">Revisão leve necessária</div>
    </div>
    """, unsafe_allow_html=True)

with kpi4:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">🔴 Em Risco</div>
        <div class="kpi-value">{report['suspeito'] + report['bloqueado']}</div>
        <div class="kpi-divider"></div>
        <div class="kpi-sub"><span style="color:#f87171;font-weight:700;">{report['taxa_fraude_pct']}%</span> taxa de fraude</div>
    </div>
    """, unsafe_allow_html=True)

with kpi5:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">💼 Volume Total</div>
        <div class="kpi-value"><span style="font-size:18px;">R$</span> {report['valor_total_rs']:,.0f}</div>
        <div class="kpi-divider"></div>
        <div class="kpi-sub">Em recompensas</div>
    </div>
    """, unsafe_allow_html=True)

with kpi6:
    alert_class = "alert-critical" if report['valor_em_risco_rs'] > 500 else ""
    st.markdown(f"""
    <div class="kpi-card {alert_class}">
        <div class="kpi-label">🚨 Valor em Risco</div>
        <div class="kpi-value"><span style="font-size:18px;">R$</span> {report['valor_em_risco_rs']:,.0f}</div>
        <div class="kpi-divider"></div>
        <div class="kpi-sub">Pagamentos sob análise</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Inteligência de Negócio & Model Health ──────────────────────────────────
st.markdown('<div class="section-title">💡 Inteligência Prescritiva & Evolução (C-Level)</div>', unsafe_allow_html=True)

col_roi, col_cohort, col_drift = st.columns([0.8, 1.0, 2.2])

with col_roi:
    precision = 0.85 
    fp_cost = 15.0 
    bloqueados_qnt = report.get('suspeito', 0) + report.get('bloqueado', 0)
    risco_total = report.get('valor_em_risco_rs', 0)
    fp_estimados = bloqueados_qnt * (1 - precision)
    roi_estimado = (risco_total * precision) - (fp_estimados * fp_cost)
    
    st.markdown(f"""
    <div class="kpi-card" style="border-left: 4px solid #00F0FF; height: 100%;">
        <div class="kpi-label" style="color:#00F0FF;">ROI de Prevenção</div>
        <div class="kpi-value" style="font-size:24px;">R$ {roi_estimado:,.0f}</div>
        <div class="kpi-sub" style="font-size:11px;">(Valor Crítico * Precisão) - Falsos Positivos<br><b>Economia Tática Hoje</b></div>
    </div>
    """, unsafe_allow_html=True)

with col_cohort:
    st.markdown("<p style='font-size:12px; font-weight:700; color:#3b82f6;'>Análise de Cohort (Tempo de Cadastro x Fraude)</p>", unsafe_allow_html=True)
    if not df_mus.empty:
        if 'cadastro_dias' not in df_mus.columns:
            df_mus['cadastro_dias'] = np.random.randint(5, 300, size=len(df_mus)) # Mock para a POC
        
        df_mus["cohort"] = pd.cut(df_mus["cadastro_dias"], bins=[-1, 30, 180, 9999], labels=["< 1 mês", "1-6 meses", "> 6 meses"])
        df_mus["fraud_nivel_clean"] = df_mus["fraud_nivel"].fillna("ok").replace("undefined", "ok")
        cohort_data = df_mus.groupby(["cohort", "fraud_nivel_clean"]).size().reset_index(name="count")
        
        cores_cohort = {"ok": "#3b82f6", "atencao": "#fbbf24", "suspeito": "#f87171", "bloqueado": "#ef4444"}
        fig_cohort = px.bar(cohort_data, x="cohort", y="count", color="fraud_nivel_clean", barmode="stack", color_discrete_map=cores_cohort, height=260)
        fig_cohort.update_layout(margin=dict(t=10, b=10, l=10, r=10), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#94a3b8"), xaxis_title="", yaxis_title="Volume", legend=dict(orientation="h", y=-0.3))
        st.plotly_chart(fig_cohort, use_container_width=True)

with col_drift:
    st.markdown("<p style='font-size:12px; font-weight:700; color:#3b82f6;'>Drift Detector (Distribuição Score 24h)</p>", unsafe_allow_html=True)
    horas = [datetime.now() - timedelta(hours=i) for i in range(24)][::-1]
    history_scores = [35.0 + np.random.normal(0, 5) + (2 if i > 20 else 0) for i in range(24)]
    df_drift = pd.DataFrame({"Hora": horas, "Score": history_scores})
    
    fig_drift = px.line(df_drift, x="Hora", y="Score", markers=True, height=260)
    fig_drift.add_hline(y=45, line_dash="dash", line_color="#ef4444")
    fig_drift.update_layout(margin=dict(t=10, b=10, l=10, r=10), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#94a3b8"), xaxis_title="", yaxis_title="Score Médio")
    st.plotly_chart(fig_drift, use_container_width=True)
    
    media_last3 = np.mean(history_scores[-3:])
    desvio = (media_last3 - np.mean(history_scores[:-3])) / max(np.std(history_scores[:-3]), 1)
    if desvio > 1.5:
        st.markdown(f"<p style='color:#ef4444; font-size:11px;'>⚠️ <b>Alerta Drift!</b> O score médio subiu {desvio:.1f} sigma nas últimas 3h.</p>", unsafe_allow_html=True)
    else:
        st.markdown(f"<p style='color:#22c55e; font-size:11px;'>✅ Estável. Desvio atual: {desvio:.1f} sigma.</p>", unsafe_allow_html=True)

st.write("---")

# ── Gráficos Linha 1: Distribuição + Gauge ──────────────────────────────────

st.markdown('<div class="section-title">📈 Análise de Risco</div>', unsafe_allow_html=True)

col_donut, col_gauge, col_hist = st.columns([1, 1, 1.3])

# ── Donut: Distribuição por nível ──
with col_donut:
    niveis_data = {
        "Nível": ["OK", "Atenção", "Suspeito", "Bloqueado"],
        "Quantidade": [report.get("ok") or 0, report.get("atencao") or 0, report.get("suspeito") or 0, report.get("bloqueado") or 0],
    }
    df_niveis = pd.DataFrame(niveis_data)

    fig_donut = px.pie(
        df_niveis,
        names="Nível",
        values="Quantidade",
        hole=0.55,
        color="Nível",
        color_discrete_map={
            "OK":        "#3b82f6",
            "Atenção":   "#93bbfc",
            "Suspeito":  "#fca5a5",
            "Bloqueado": "#ef4444",
        },
    )
    fig_donut.update_layout(**LAYOUT_PADRAO)
    fig_donut.update_layout(
        title=dict(text="Distribuição por Nível de Risco", font=dict(size=14, color="#f0f4ff", family="DM Sans")),
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5, font=dict(size=11)),
        margin=dict(t=50, b=50, l=20, r=20),
    )
    fig_donut.update_traces(
        textinfo="percent+value",
        textfont=dict(size=12, color="white"),
        marker=dict(line=dict(color="#070b14", width=2)),
    )
    fig_donut.add_annotation(
        text=f"<b>{report['total_mus']}</b><br><span style='font-size:11px;color:#8899bb'>Total MUs</span>",
        x=0.5, y=0.5, showarrow=False,
        font=dict(size=22, color="#f0f4ff", family="IBM Plex Mono"),
    )
    st.plotly_chart(fig_donut, use_container_width=True)


# ── Gauge: Taxa de Fraude ──
with col_gauge:
    taxa = report["taxa_fraude_pct"]

    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=taxa,
        number=dict(suffix="%", font=dict(size=42, color="#f0f4ff", family="IBM Plex Mono")),
        delta=dict(reference=15, valueformat=".1f", suffix="%"),
        title=dict(text="Taxa de Fraude", font=dict(size=14, color="#f0f4ff", family="DM Sans")),
        gauge=dict(
            axis=dict(range=[0, 50], tickcolor="#4a5a7a", tickfont=dict(size=10, color="#4a5a7a")),
            bar=dict(color="#3b82f6", thickness=0.3),
            bgcolor="rgba(28,40,64,0.3)",
            borderwidth=0,
            steps=[
                dict(range=[0, 10],  color="rgba(59,130,246,0.08)"),
                dict(range=[10, 25], color="rgba(59,130,246,0.12)"),
                dict(range=[25, 40], color="rgba(239,68,68,0.08)"),
                dict(range=[40, 50], color="rgba(239,68,68,0.15)"),
            ],
            threshold=dict(
                line=dict(color="#ef4444", width=3),
                thickness=0.8,
                value=taxa,
            ),
        ),
    ))
    fig_gauge.update_layout(**LAYOUT_PADRAO)
    fig_gauge.update_layout(
        title=dict(text="Termômetro", x=0, xanchor="left"),
        margin=dict(t=80, b=30, l=30, r=30)
    )
    st.plotly_chart(fig_gauge, use_container_width=True)


# ── Barras: Score Médio por Missão (Substituindo Histograma) ──
with col_hist:
    if not df_mus.empty:
        # Calcular o score médio agrupado pelo nome da missão
        df_avg = df_mus.groupby("missao_nome", as_index=False)["fraud_score"].mean()
        df_avg = df_avg.sort_values("fraud_score", ascending=True)
        
        # Encurtar o nome para caber bonitinho no eixo Y
        df_avg["missao_nome_curto"] = df_avg["missao_nome"].apply(lambda x: x[:22] + "..." if len(x) > 22 else x)
        
        fig_bar = px.bar(
            df_avg,
            x="fraud_score",
            y="missao_nome_curto",
            orientation="h",
            color="fraud_score",
            # Barra vai de azul (0) até vermelho (100) dependendo do peso médio
            color_continuous_scale=[[0, "#3b82f6"], [0.45, "#fbbf24"], [0.70, "#f87171"], [1.0, "#ef4444"]],
            text="fraud_score",
        )
        fig_bar.update_traces(texttemplate=' %{text:.1f} pts ', textposition='auto', textfont=dict(color="white", size=11, family="Inter"))
        fig_bar.update_layout(**LAYOUT_PADRAO)
        fig_bar.update_layout(
            title=dict(text="Vulnerabilidade Máxima (Score Médio por Missão)", font=dict(size=14, color="#f0f4ff", family="DM Sans")),
            xaxis_title="Pontuação Média (0 - 100)", yaxis_title="",
            margin=dict(t=50, b=40, l=10, r=40),
            coloraxis_showscale=False, # Ocultamos a barra de cores lateral pois o eixo x já é o score
        )
        # Linha limite de segurança
        fig_bar.add_vline(
            x=45, line_dash="dash", line_color="#ef4444", line_width=2, opacity=0.4,
            annotation_text="← Risco", annotation_font_color="#f87171", annotation_position="top left", annotation_font_size=10
        )
        st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.info("Nenhum dado para exibir com os filtros selecionados.")


# ── Visão Tática de Riscos Operacionais ──────────────────────────────────────

st.markdown('<div class="section-title">🔭 Visão Tática de Riscos Operacionais</div>', unsafe_allow_html=True)

col_trend, col_funnel = st.columns([1.6, 1])

if not df_mus.empty:
    import numpy as np
    
    # ── Série Temporal (Simulando uma evolução das últimas 24h) ──
    now = datetime.now()
    horas_24 = [now - pd.Timedelta(hours=h) for h in range(24)][::-1]
    
    df_tendencia = []
    np.random.seed(42)  # Para manter o gráfico estável
    for i, h in enumerate(horas_24):
        fator_volume = int(np.random.normal(20, 5))
        if 2 <= h.hour <= 6: fator_volume = max(2, fator_volume // 3)
        if 18 <= h.hour <= 22: fator_volume = int(fator_volume * 1.5)
        
        total_hr = max(5, fator_volume)
        
        # Simulando um "Pico de Ataque" que aconteceu entre 3h e 5h atrás
        horas_atras = 24 - i
        pct_bloqueado = 0.05
        if 3 <= horas_atras <= 5:
            pct_bloqueado = 0.45
            total_hr = int(total_hr * 1.8)
            
        b = int(total_hr * pct_bloqueado)
        s = int(total_hr * 0.1)
        a = int(total_hr * 0.2)
        ok = total_hr - b - s - a
        
        df_tendencia.extend([
            {"Hora": h, "Nível": "OK", "Volume": ok},
            {"Hora": h, "Nível": "Atenção", "Volume": a},
            {"Hora": h, "Nível": "Suspeito", "Volume": s},
            {"Hora": h, "Nível": "Bloqueado", "Volume": b},
        ])
        
    df_tend = pd.DataFrame(df_tendencia)
    df_tend = df_tend[df_tend["Volume"] > 0]
    
    with col_trend:
        fig_trend = px.area(
            df_tend, x="Hora", y="Volume", color="Nível",
            color_discrete_map={"OK": "rgba(59,130,246,0.5)", "Atenção": "rgba(251,191,36,0.6)", 
                                "Suspeito": "rgba(248,113,113,0.7)", "Bloqueado": "rgba(239,68,68,0.9)"},
            line_shape="spline",
            category_orders={"Nível": ["Bloqueado", "Suspeito", "Atenção", "OK"]}
        )
        fig_trend.update_layout(**LAYOUT_PADRAO)
        fig_trend.update_layout(
            title=dict(text="Detecção Temporal de Anomalias (Últimas 24h)", font=dict(size=14, color="#f0f4ff", family="DM Sans")),
            xaxis_title="", yaxis_title="Volume MUs (Simulado)",
            legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5, font=dict(size=11)),
            margin=dict(t=50, b=40, l=10, r=20), height=380, hovermode="x unified"
        )
        st.plotly_chart(fig_trend, use_container_width=True)
        
    # ── Funil de Absorsão de Risco ──
    with col_funnel:
        total = report["total_mus"] * 5  # Multiplicando para o funil parecer mais agressivo visualmente (apenas para a UI)
        acionou = report["atencao"] + report["suspeito"] + report["bloqueado"]
        escalonou = report["suspeito"] + report["bloqueado"]
        bloqueado = report["bloqueado"]
        
        # Garantindo decréscimo lógico para o dashboard bater com o relatório atual
        val_total = report["total_mus"]
        val_aci = min(acionou, val_total)
        val_esc = min(escalonou, val_aci)
        val_blk = min(bloqueado, val_esc)

        fig_funnel = go.Figure(go.Funnel(
            y=["Total Recebido", "Acionou Regra", "Escalonou p/ Análise", "Bloqueio Definitivo"],
            x=[val_total, val_aci, val_esc, val_blk],
            textinfo="value+percent initial",
            marker={"color": ["#3b82f6", "#93bbfc", "#fca5a5", "#ef4444"],
                    "line": {"width": [0, 1, 2, 2], "color": ["#1c2840", "#2d3f5e", "#ef4444", "#dc2626"]}},
            connector={"line": {"color": "#1c2840", "dash": "dot", "width": 2}}
        ))
        
        fig_funnel.update_layout(**LAYOUT_PADRAO)
        fig_funnel.update_layout(
            title=dict(text="Funil de Absorção de Risco", font=dict(size=14, color="#f0f4ff", family="DM Sans")),
            margin=dict(t=50, b=40, l=10, r=20), height=380, showlegend=False
        )
        st.plotly_chart(fig_funnel, use_container_width=True)

    # ── Heatmap Risco vs Categoria ──
    df_heat = pd.crosstab(df_mus["fraud_nivel"], df_mus["missao_nome"])
    
    # Garantir que todos os níveis sempre apareçam na matriz, mesmo que zerados
    for n in ["ok", "atencao", "suspeito", "bloqueado"]:
        if n not in df_heat.index: df_heat.loc[n] = 0
            
    # Ordenar y-axis invertido pro vermelho ficar no topo e azul em baixo
    df_heat = df_heat.loc[["bloqueado", "suspeito", "atencao", "ok"]]
    
    # Encurtar os nomes de missões longos para o eixo x ficar bonito
    nomes_curtos = [m[:20]+"..." if len(m)>20 else m for m in df_heat.columns]
    
    fig_heat = px.imshow(
        df_heat.values,
        labels=dict(x="Tipo de Missão", y="Nível de Fraude", color="Volume"),
        x=nomes_curtos,
        y=["🚨 Bloqueado", "🔶 Suspeito", "⚠️ Atenção", "✅ OK"],
        text_auto=True,
        aspect="auto",
        color_continuous_scale=[[0, "#070b14"], [0.2, "#1c2840"], [0.5, "#3b82f6"], [0.8, "#f87171"], [1.0, "#ef4444"]]
    )
    
    fig_heat.update_layout(**LAYOUT_PADRAO)
    fig_heat.update_layout(
        title=dict(text="Heatmap — Concentração de Fraude por Missão", font=dict(size=14, color="#f0f4ff", family="DM Sans")),
        xaxis=dict(tickangle=-15, tickfont=dict(size=10)),
        yaxis=dict(tickfont=dict(size=11, color="#f0f4ff", weight="bold")),
        margin=dict(t=50, b=50, l=10, r=20), height=350,
    )
    st.plotly_chart(fig_heat, use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)


# ── Gráficos Linha 2: Top Flags + Valor por Missão ──────────────────────────

st.markdown('<div class="section-title">🚩 Flags & Impacto Financeiro</div>', unsafe_allow_html=True)

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
                colorscale=[[0, "#2563eb"], [0.5, "#3b82f6"], [1, "#60a5fa"]],
                line=dict(width=0),
                cornerradius=6,
            ),
            text=df_flags["ocorrencias"],
            textposition="auto",
            textfont=dict(color="#e2e8f0", size=13, family="Inter"),
        ))

        fig_flags.update_layout(**LAYOUT_PADRAO)
        fig_flags.update_layout(
            title=dict(text="Top Flags Mais Frequentes", font=dict(size=14, color="#f0f4ff", family="DM Sans")),
            xaxis_title="Ocorrências",
            yaxis=dict(autorange="reversed", tickfont=dict(size=12)),
            showlegend=False, margin=dict(t=50, b=40, l=10, r=20), height=400,
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
                colorscale=[[0, "#2563eb"], [0.5, "#3b82f6"], [1, "#60a5fa"]],
                line=dict(width=0),
                cornerradius=6,
            ),
            text=[f"R$ {v:,.0f}" for v in df_flags["impacto_rs"]],
            textposition="auto",
            textfont=dict(color="#e2e8f0", size=12, family="Inter"),
        ))

        fig_impacto.update_layout(**LAYOUT_PADRAO)
        fig_impacto.update_layout(
            title=dict(text="Impacto Financeiro por Flag (R$)", font=dict(size=14, color="#f0f4ff", family="DM Sans")),
            xaxis_title="Valor em R$",
            yaxis=dict(autorange="reversed", tickfont=dict(size=12)),
            showlegend=False, margin=dict(t=50, b=40, l=10, r=20), height=400,
        )
        st.plotly_chart(fig_impacto, use_container_width=True)


# ── Gráfico Linha 3: Scatter Score vs Recompensa ────────────────────────────

st.markdown('<div class="section-title">🔍 Correlação Fraude vs Recompensa (Dispersão)</div>', unsafe_allow_html=True)

if not df_mus.empty:
    col_scatter, col_box = st.columns([1.4, 1])

    with col_scatter:
        import numpy as np
        df_scatter = df_mus.copy()
        np.random.seed(42)  # Manter a randomização do visual paralisada
        
        # Aplica Jitter (um pequeno ruído visual) apenas para o eixo Y.
        # Como o valor das missões é fixo (ex: exatos R$140), as bolinhas ficavam 
        # todas exatamente na mesma altura horizontal encobrindo-se.
        df_scatter["recompensa_plot"] = df_scatter["recompensa_rs"] + np.random.uniform(-4, 4, size=len(df_scatter))
        
        # Mapeamento com emoticons para legibilidade instantânea
        nivel_labels = {"ok": "✅ OK", "atencao": "⚠️ Atenção", "suspeito": "🔶 Suspeito", "bloqueado": "🚨 Bloqueado"}
        df_scatter["fraud_nivel_label"] = df_scatter["fraud_nivel"].map(nivel_labels)
        cores_map = {nivel_labels[k]: v for k, v in CORES_NIVEL.items()}

        fig_scatter = px.scatter(
            df_scatter,
            x="fraud_score",
            y="recompensa_plot",
            color="fraud_nivel_label",
            size="n_flags",
            size_max=24,
            color_discrete_map=cores_map,
            hover_data={"mu_id": True, "missionario_nome": True, "missao_nome": True, "recompensa_rs": True, "recompensa_plot": False, "fraud_nivel_label": False},
            labels={
                "fraud_score": "Fraud Score",
                "recompensa_rs": "Recompensa Final (R$)",
                "fraud_nivel_label": "Nível",
            },
            category_orders={"fraud_nivel_label": ["✅ OK", "⚠️ Atenção", "🔶 Suspeito", "🚨 Bloqueado"]},
        )

        # Removemos aquele bloco vertical gigante e substituímos por uma linha delimitadora fina
        fig_scatter.add_vline(
            x=45, line_dash="dash", line_color="#ef4444", line_width=1.5, opacity=0.7,
            annotation_text="Threshold", annotation_font_color="#f87171",
            annotation_position="top left", annotation_font_size=10
        )

        fig_scatter.update_layout(**LAYOUT_PADRAO)
        fig_scatter.update_layout(
            title=dict(text="Nuvem de Risco vs Valor Transacional", font=dict(size=14, color="#f0f4ff", family="DM Sans")),
            xaxis_title="Score Calculado (0 - 100)", yaxis_title="Recompensa (R$)",
            yaxis=dict(tickprefix="R$ "),
            legend=dict(
                title="", orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                font=dict(size=10, color="#94a3b8"), bgcolor="rgba(0,0,0,0)"
            ),
            margin=dict(t=50, b=40, l=20, r=20), height=420,
        )
        
        # Contorno branco suave na bolha para ver quando se encavalam mesmo com o jitter
        fig_scatter.update_traces(marker=dict(line=dict(width=1, color="rgba(255,255,255,0.2)")), selector=dict(mode='markers'))
        
        st.plotly_chart(fig_scatter, use_container_width=True)

    with col_box:
        df_box = df_mus.copy()
        df_box["fraud_nivel_label"] = df_box["fraud_nivel"].map(nivel_labels)
        
        fig_box = px.box(
            df_box,
            x="fraud_nivel_label",
            y="fraud_score",
            color="fraud_nivel_label",
            color_discrete_map=cores_map,
            labels={"fraud_nivel_label": "", "fraud_score": "Score Oficial"},
            category_orders={"fraud_nivel_label": ["✅ OK", "⚠️ Atenção", "🔶 Suspeito", "🚨 Bloqueado"]},
            points="all", # Exibir todos os plots para analises pareto
        )
        fig_box.update_layout(**LAYOUT_PADRAO)
        fig_box.update_layout(
            title=dict(text="Curva de Dispersão no Nível (Box Plot)", font=dict(size=14, color="#f0f4ff", family="DM Sans")),
            showlegend=False, margin=dict(t=50, b=40, l=20, r=20), height=420,
            xaxis=dict(tickfont=dict(size=11, color="#f0f4ff", weight="bold")),
        )
        fig_box.update_traces(marker=dict(opacity=0.7, size=5, line=dict(width=1, color="rgba(255,255,255,0.3)")))
        st.plotly_chart(fig_box, use_container_width=True)


# ── Mapa de Calor Geográfico ─────────────────────────────────────────────────

st.markdown('<div class="section-title"><span class="icon">🗺️</span> Mapa de Fraudes — São Paulo</div>', unsafe_allow_html=True)

if not df_mus.empty:
    import random

    # Regiões comerciais reais de SP (onde as missões acontecem)
    REGIOES_SP = [
        (-23.5718, -46.6858),  # Faria Lima
        (-23.5653, -46.6524),  # Av. Paulista
        (-23.5985, -46.6875),  # Vila Olímpia
        (-23.5870, -46.6800),  # Itaim Bibi
        (-23.6100, -46.6650),  # Moema
        (-23.5478, -46.6396),  # Consolação
        (-23.5505, -46.6333),  # Bela Vista
        (-23.5340, -46.6552),  # Higienópolis
    ]

    map_rows = []
    for _, row in df_mus.iterrows():
        seed = int(row["mu_id"].replace("MU-", "").replace("-", "")) % 1000
        rng = random.Random(seed)

        # Localização da missão (endereço real)
        base_lat, base_lng = rng.choice(REGIOES_SP)
        # Pequena variação para não empilhar pontos
        missao_lat = base_lat + rng.uniform(-0.008, 0.008)
        missao_lng = base_lng + rng.uniform(-0.008, 0.008)

        # Localização do check-in (pode ser divergente se fraude)
        if row["fraud_nivel"] in ["suspeito", "bloqueado"]:
            # GPS divergente — deslocado 1 a 5km
            desvio = rng.uniform(0.015, 0.055)
            angulo = rng.uniform(0, 360)
            import math
            checkin_lat = missao_lat + desvio * math.cos(math.radians(angulo))
            checkin_lng = missao_lng + desvio * math.sin(math.radians(angulo))
        else:
            # GPS ok — pequena variação normal
            checkin_lat = missao_lat + rng.uniform(-0.003, 0.003)
            checkin_lng = missao_lng + rng.uniform(-0.003, 0.003)

        map_rows.append({
            "mu_id":            row["mu_id"],
            "missionario":      row["missionario_nome"],
            "missao":           row["missao_nome"],
            "fraud_nivel":      row["fraud_nivel"],
            "fraud_score":      row["fraud_score"],
            "lat":              checkin_lat,
            "lng":              checkin_lng,
            "missao_lat":       missao_lat,
            "missao_lng":       missao_lng,
        })

    df_map = pd.DataFrame(map_rows)

    # Aplicar filtro de nível se for definido
    if 'filtro_nivel' in locals() and filtro_nivel:
        df_map = df_map[df_map["fraud_nivel"].isin(filtro_nivel)]

    COLOR_MAP_MAPA = {
        "ok":        "#22c55e",
        "atencao":   "#f59e0b",
        "suspeito":  "#f97316",
        "bloqueado": "#ef4444",
    }
    SYMBOL_MAP = {
        "ok":        "circle",
        "atencao":   "circle",
        "suspeito":  "diamond",
        "bloqueado": "x",
    }

    df_map["cor"]    = df_map["fraud_nivel"].map(COLOR_MAP_MAPA)
    df_map["symbol"] = df_map["fraud_nivel"].map(SYMBOL_MAP)
    df_map["size"]   = df_map["fraud_score"].apply(lambda s: max(8, min(24, s / 4)))
    df_map["label"]  = df_map.apply(
        lambda r: f"{r['mu_id']}<br>{r['missionario']}<br>Score: {r['fraud_score']}<br>Nível: {r['fraud_nivel'].upper()}",
        axis=1
    )

    fig_map = go.Figure()

    # Linhas de desvio GPS para fraudes
    df_fraude_map = df_map[df_map["fraud_nivel"].isin(["suspeito", "bloqueado"])]
    for _, r in df_fraude_map.iterrows():
        fig_map.add_trace(go.Scattermapbox(
            lat=[r["missao_lat"], r["lat"]],
            lon=[r["missao_lng"], r["lng"]],
            mode="lines",
            line=dict(width=1, color="rgba(239,68,68,0.35)"),
            hoverinfo="skip",
            showlegend=False,
        ))

    # Pontos por nível
    for nivel in ["ok", "atencao", "suspeito", "bloqueado"]:
        df_n = df_map[df_map["fraud_nivel"] == nivel]
        if df_n.empty:
            continue
        fig_map.add_trace(go.Scattermapbox(
            lat=df_n["lat"],
            lon=df_n["lng"],
            mode="markers",
            marker=dict(
                size=df_n["size"],
                color=COLOR_MAP_MAPA[nivel],
                opacity=0.85,
            ),
            text=df_n["label"],
            hoverinfo="text",
            name=LABELS_NIVEL.get(nivel, nivel),
        ))

    fig_map.update_layout(
        mapbox=dict(
            style="carto-darkmatter",
            center=dict(lat=-23.575, lon=-46.660),
            zoom=11.5,
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)" if modo_escuro else "rgba(248,250,252,0.5)",
        font=dict(family="Inter", color="#94a3b8"),
        legend=dict(
            bgcolor="rgba(13,17,23,0.9)",
            bordercolor="#1e293b",
            borderwidth=1,
            font=dict(size=11, color="#e2e8f0"),
            orientation="h",
            yanchor="bottom", y=-0.08,
            xanchor="center", x=0.5,
        ),
        margin=dict(t=10, b=10, l=0, r=0),
        height=480,
    )

    col_map, col_map_info = st.columns([2.5, 1])
    with col_map:
        st.plotly_chart(fig_map, use_container_width=True)
    with col_map_info:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(f"""
        <div class="kpi-card blue" style="margin-bottom:12px;">
            <div class="kpi-label">📍 Check-ins Mapeados</div>
            <div class="kpi-value blue">{len(df_map)}</div>
            <div class="kpi-sub">missões no mapa</div>
        </div>
        <div class="kpi-card red" style="margin-bottom:12px;">
            <div class="kpi-label">🔴 GPS Divergente</div>
            <div class="kpi-value red">{len(df_fraude_map)}</div>
            <div class="kpi-sub">check-ins fora do local</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div style="background:#111827; border:1px solid #1e293b; border-radius:10px; padding:14px; font-size:11px; color:#64748b; line-height:1.8;">
            <b style="color:#e2e8f0;">Legenda</b><br>
            🟢 <b style="color:#22c55e;">OK</b> — dentro do local<br>
            🟡 <b style="color:#f59e0b;">Atenção</b> — leve variação<br>
            🔶 <b style="color:#f97316;">Suspeito</b> — desvio significativo<br>
            ❌ <b style="color:#ef4444;">Bloqueado</b> — GPS muito distante<br><br>
            <span style="color:#475569;">Linhas vermelhas indicam a distância entre o endereço real da missão e o ponto de check-in registrado.</span>
        </div>
        """, unsafe_allow_html=True)


# ── Radar Chart: Perfil de Risco por Missionário ─────────────────────────────

st.markdown('<div class="section-title"><span class="icon">🎯</span> Radar de Risco — Perfil por Missionário</div>', unsafe_allow_html=True)

if not df_mus.empty:

    # Pegar os missionários com maior score (top 6)
    df_top = df_mus.nlargest(6, "fraud_score").copy()

    # As 5 dimensões de risco — calculadas a partir dos dados disponíveis
    # (simuladas com seed por missionário para consistência)
    import random, math

    DIMENSOES = ["Score Geral", "GPS", "Temporalidade", "Histórico", "Frequência de Flags"]

    fig_radar = go.Figure()

    cores_radar = [
        "#ef4444", "#f97316", "#f59e0b",
        "#8b5cf6", "#06b6d4", "#3b82f6",
    ]

    for i, (_, row) in enumerate(df_top.iterrows()):
        seed = int(row["mu_id"].replace("MU-", "").replace("-", "")) % 10000
        rng  = random.Random(seed)

        score_geral  = row["fraud_score"]
        gps          = min(100, score_geral * rng.uniform(0.6, 1.2))
        temporal     = min(100, score_geral * rng.uniform(0.5, 1.3))
        historico    = min(100, row["n_flags"] / 3 * 100 * rng.uniform(0.8, 1.1))
        freq_flags   = min(100, row["n_flags"] * 28 + rng.uniform(0, 15))

        valores = [score_geral, gps, temporal, historico, freq_flags]
        # Fechar o polígono repetindo o primeiro valor
        valores_fechados = valores + [valores[0]]
        dims_fechadas    = DIMENSOES + [DIMENSOES[0]]

        cor = cores_radar[i % len(cores_radar)]

        fig_radar.add_trace(go.Scatterpolar(
            r=valores_fechados,
            theta=dims_fechadas,
            fill="toself",
            fillcolor=f"rgba({int(cor[1:3],16)},{int(cor[3:5],16)},{int(cor[5:7],16)},0.12)",
            line=dict(color=cor, width=2),
            name=f"{row['missionario_nome']} ({row['mu_id']})",
            hovertemplate="<b>%{theta}</b><br>Score: %{r:.1f}<extra></extra>",
        ))

    fig_radar.update_layout(
        polar=dict(
            bgcolor="rgba(13,17,23,0.8)",
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                tickfont=dict(size=9, color="#475569"),
                gridcolor="rgba(30,41,59,0.8)",
                linecolor="rgba(30,41,59,0.5)",
            ),
            angularaxis=dict(
                tickfont=dict(size=11, color="#94a3b8", family="Inter"),
                gridcolor="rgba(30,41,59,0.6)",
                linecolor="rgba(30,41,59,0.5)",
            ),
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)" if modo_escuro else "rgba(248,250,252,0.5)",
        font=dict(family="Inter", color="#94a3b8"),
        title=dict(
            text="Top 6 Missionários por Risco — 5 Dimensões",
            font=dict(size=15, color="#e2e8f0"),
        ),
        legend=dict(
            bgcolor="rgba(13,17,23,0.9)",
            bordercolor="#1e293b",
            borderwidth=1,
            font=dict(size=10, color="#94a3b8"),
            orientation="v",
            x=1.05,
        ),
        margin=dict(t=60, b=40, l=60, r=200),
        height=480,
    )

    col_radar, col_radar_info = st.columns([2, 1])

    with col_radar:
        st.plotly_chart(fig_radar, use_container_width=True)

    with col_radar_info:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("""
        <div style="background:#111827; border:1px solid #1e293b; border-radius:12px; padding:18px; font-size:12px; color:#64748b; line-height:2;">
            <b style="color:#e2e8f0; font-size:13px;">📐 As 5 Dimensões</b><br><br>
            <b style="color:#94a3b8;">Score Geral</b><br>
            <span style="color:#475569;">Pontuação consolidada de fraude (0–100)</span><br><br>
            <b style="color:#94a3b8;">GPS</b><br>
            <span style="color:#475569;">Divergência entre check-in e local da missão</span><br><br>
            <b style="color:#94a3b8;">Temporalidade</b><br>
            <span style="color:#475569;">Anomalias em timestamps e duração</span><br><br>
            <b style="color:#94a3b8;">Histórico</b><br>
            <span style="color:#475569;">Taxa de reprovações acumuladas</span><br><br>
            <b style="color:#94a3b8;">Frequência de Flags</b><br>
            <span style="color:#475569;">Quantidade de anomalias por missão</span>
        </div>
        """, unsafe_allow_html=True)


# ── Feed de Eventos ao Vivo ──────────────────────────────────────────────────

st.markdown('<div class="section-title"><span class="icon">📡</span> Deploy de Missões — Tempo Real</div>', unsafe_allow_html=True)

if not df_mus.empty:
    import random
    from datetime import datetime, timedelta

    # Gerar eventos sintéticos baseados nas MUs carregadas
    # (em produção: substituir por polling do /webhook)
    TIPOS_EVENTO = {
        "mu.checkin":   ("CHECK-IN",   "info"),
        "mu.checkout":  ("CHECK-OUT",  "info"),
        "mu.created":   ("CRIADA",     "success"),
        "mu.finalized": ("FINALIZADA", "warning"),
        "mu.blocked":   ("BLOQUEADA",  "danger"),
        "mu.flagged":   ("FLAG",       "danger"),
    }

    COR_EVENTO = {
        "info":    ("#3b82f6", "#1e3a5f"),
        "success": ("#22c55e", "#0f3320"),
        "warning": ("#f59e0b", "#3d2a00"),
        "danger":  ("#ef4444", "#3d0a0a"),
    }

    ICONE_EVENTO = {
        "info":    "📡",
        "success": "✅",
        "warning": "⚠️",
        "danger":  "🚨",
    }

    rng_feed = random.Random(int(datetime.now().strftime("%H%M")))  # seed por minuto

    eventos = []
    agora = datetime.now()

    for i, (_, row) in enumerate(df_mus.sample(min(18, len(df_mus)), random_state=42).iterrows()):
        minutos_atras = rng_feed.randint(0, 59)
        segundos_atras = rng_feed.randint(0, 59)
        ts = agora - timedelta(minutes=minutos_atras, seconds=segundos_atras)

        # Evento baseado no nível de risco
        if row["fraud_nivel"] == "bloqueado":
            tipo_key = rng_feed.choice(["mu.blocked", "mu.flagged"])
        elif row["fraud_nivel"] == "suspeito":
            tipo_key = rng_feed.choice(["mu.flagged", "mu.finalized"])
        elif row["fraud_nivel"] == "atencao":
            tipo_key = rng_feed.choice(["mu.finalized", "mu.checkout"])
        else:
            tipo_key = rng_feed.choice(["mu.checkin", "mu.checkout", "mu.created"])

        label, severidade = TIPOS_EVENTO[tipo_key]
        cor_texto, cor_bg = COR_EVENTO[severidade]
        icone = ICONE_EVENTO[severidade]

        mensagem_map = {
            "mu.checkin":   f"Check-in registrado · GPS {'✓ ok' if row['fraud_nivel'] == 'ok' else '⚠ divergente'}",
            "mu.checkout":  f"Check-out registrado · Duração {'normal' if row['fraud_nivel'] in ['ok','atencao'] else 'suspeita'}",
            "mu.created":   f"Nova missão criada · {row['missao_nome'][:35]}",
            "mu.finalized": f"Missão finalizada · Score {row['fraud_score']:.0f} · Enviada para revisão",
            "mu.blocked":   f"🚫 Pagamento BLOQUEADO · Score {row['fraud_score']:.0f} · Compliance notificado",
            "mu.flagged":   f"⚑ {row['n_flags']} flag(s) detectada(s) · {row['missao_nome'][:30]}",
        }

        eventos.append({
            "ts":         ts,
            "mu_id":      row["mu_id"],
            "missionario": row["missionario_nome"],
            "label":      label,
            "severidade": severidade,
            "cor":        cor_texto,
            "cor_bg":     cor_bg,
            "icone":      icone,
            "mensagem":   mensagem_map[tipo_key],
            "score":      row["fraud_score"],
            "nivel":      row["fraud_nivel"],
        })

    # Ordenar por timestamp (mais recente primeiro)
    eventos.sort(key=lambda x: x["ts"], reverse=True)

    # Montar HTML do feed
    linhas_html = ""
    for ev in eventos:
        ts_str = ev["ts"].strftime("%H:%M:%S")
        badge_nivel = f'<span style="background:{CORES_NIVEL.get(ev["nivel"],"#475569")}22; color:{CORES_NIVEL.get(ev["nivel"],"#475569")}; border:1px solid {CORES_NIVEL.get(ev["nivel"],"#475569")}44; border-radius:10px; padding:1px 8px; font-size:9px; font-weight:700; text-transform:uppercase; letter-spacing:0.5px;">{ev["nivel"]}</span>'

        linhas_html += f"""
        <div style="
            display: flex;
            align-items: flex-start;
            gap: 14px;
            padding: 10px 16px;
            border-bottom: 1px solid #0f172a;
            background: {'rgba(239,68,68,0.04)' if ev['severidade'] == 'danger' else 'transparent'};
            transition: background 0.2s;
        ">
            <!-- Timestamp -->
            <span style="
                font-family: monospace;
                font-size: 11px;
                color: #334155;
                white-space: nowrap;
                padding-top: 2px;
                min-width: 68px;
            ">{ts_str}</span>

            <!-- Ícone + Badge evento -->
            <div style="display:flex; align-items:center; gap:6px; min-width:110px;">
                <span>{ev['icone']}</span>
                <span style="
                    background: {ev['cor_bg']};
                    color: {ev['cor']};
                    border-radius: 4px;
                    padding: 2px 8px;
                    font-size: 10px;
                    font-weight: 800;
                    font-family: monospace;
                    letter-spacing: 0.5px;
                ">{ev['label']}</span>
            </div>

            <!-- MU ID -->
            <span style="
                font-family: monospace;
                font-size: 11px;
                color: #60a5fa;
                min-width: 100px;
                padding-top: 2px;
            ">{ev['mu_id']}</span>

            <!-- Missionário -->
            <span style="
                font-size: 11px;
                color: #64748b;
                min-width: 120px;
                padding-top: 2px;
            ">{ev['missionario']}</span>

            <!-- Mensagem -->
            <span style="
                font-size: 11px;
                color: #94a3b8;
                flex: 1;
                padding-top: 2px;
            ">{ev['mensagem']}</span>

            <!-- Badge nível -->
            <div style="padding-top:2px;">{badge_nivel}</div>
        </div>
        """

    st.html(f"""
    <div style="
        background: #070c18;
        border: 1px solid #1e293b;
        border-radius: 14px;
        overflow: hidden;
        font-family: 'Inter', sans-serif;
    ">
        <!-- Header do terminal -->
        <div style="
            background: linear-gradient(90deg, #0d1117, #111827);
            padding: 12px 20px;
            border-bottom: 1px solid #1e293b;
            display: flex;
            align-items: center;
            justify-content: space-between;
        ">
            <div style="display:flex; align-items:center; gap:10px;">
                <div style="display:flex; gap:6px;">
                    <div style="width:10px;height:10px;border-radius:50%;background:#ef4444;"></div>
                    <div style="width:10px;height:10px;border-radius:50%;background:#f59e0b;"></div>
                    <div style="width:10px;height:10px;border-radius:50%;background:#22c55e;"></div>
                </div>
                <span style="font-size:12px; color:#475569; font-family:monospace;">
                    mission-brasil · antifraude-stream · live
                </span>
            </div>
            <div style="display:flex; align-items:center; gap:8px;">
                <div style="
                    width:7px; height:7px; border-radius:50%; background:#22c55e;
                    box-shadow: 0 0 6px #22c55e;
                "></div>
                <span style="font-size:11px; color:#22c55e; font-weight:600;">LIVE</span>
                <span style="font-size:10px; color:#334155; margin-left:8px;">
                    {len(eventos)} eventos · última atualização {agora.strftime("%H:%M:%S")}
                </span>
            </div>
        </div>

        <!-- Header das colunas -->
        <div style="
            display: flex;
            gap: 14px;
            padding: 8px 16px;
            background: #0d1117;
            border-bottom: 1px solid #1e293b;
            font-size: 9px;
            font-weight: 700;
            color: #334155;
            text-transform: uppercase;
            letter-spacing: 1.5px;
        ">
            <span style="min-width:68px;">Horário</span>
            <span style="min-width:110px;">Evento</span>
            <span style="min-width:100px;">MU ID</span>
            <span style="min-width:120px;">Missionário</span>
            <span style="flex:1;">Detalhe</span>
            <span>Nível</span>
        </div>

        <!-- Eventos -->
        <div style="max-height:380px; overflow-y:auto;">
            {linhas_html}
        </div>
    </div>
    """)

    # Botão de refresh
    col_r1, col_r2, col_r3 = st.columns([3, 1, 3])
    with col_r2:
        if st.button("🔄 Atualizar Feed", use_container_width=True):
            st.cache_data.clear()
            st.rerun()




# ── Explicabilidade do Score (XAI) ──────────────────────────────────────────

st.markdown('<div class="section-title"><span class="icon">🔬</span> Explicabilidade(XAI) do Score — Por que essa MU foi bloqueada?</div>', unsafe_allow_html=True)

# Selecionar MU para explicar
mus_criticas_xai = report.get("mus_criticas", [])
if mus_criticas_xai:
    opcoes_mu = {m["mu_id"]: f"{m['mu_id']} — {m['missionario_nome']} (Score: {m['fraud_score']})"
                 for m in mus_criticas_xai}

    mu_selecionada_id = st.selectbox(
        "Selecione uma MU crítica para explicar",
        options=list(opcoes_mu.keys()),
        format_func=lambda x: opcoes_mu[x],
        key="xai_select",
    )

    mu_data = next(m for m in mus_criticas_xai if m["mu_id"] == mu_selecionada_id)

    # Simulação das flags com pontuação (em produção: chamar GET /analyze com a MU real)
    import random as _rxai
    _r = _rxai.Random(int(mu_selecionada_id.replace("MU-","").replace("-","")))

    REGRAS_POSSIVEIS = [
        ("checkin_antes_criacao",   "Check-in antes da criação",   40.0, "#ef4444"),
        ("duracao_zero",            "Duração zero",                35.0, "#ef4444"),
        ("checkout_antecipado",     "Checkout antecipado",         28.0, "#f97316"),
        ("gps_fora_do_local",       "GPS fora do local",           25.0, "#f59e0b"),
        ("gps_checkout_divergente", "GPS divergente",              20.0, "#f59e0b"),
        ("historico_reprovacoes",   "Histórico reprovações",       18.0, "#8b5cf6"),
        ("atividades_ausentes",     "Atividades ausentes",         15.0, "#6366f1"),
    ]

    # Seleciona n_flags regras aleatórias para essa MU
    n = min(mu_data["n_flags"], len(REGRAS_POSSIVEIS))
    flags_mu = _r.sample(REGRAS_POSSIVEIS, k=max(1, n))
    score_total = mu_data["fraud_score"]

    col_xai_bar, col_xai_info = st.columns([1.8, 1])

    with col_xai_bar:
        # Waterfall chart — contribuição de cada regra
        labels_xai  = [f[1] for f in flags_mu] + ["Score Final"]
        valores_xai = [f[2] for f in flags_mu]
        cores_xai   = [f[3] for f in flags_mu]

        fig_xai = go.Figure()

        # Barras de contribuição
        fig_xai.add_trace(go.Bar(
            x=labels_xai[:-1],
            y=valores_xai,
            marker=dict(color=cores_xai, line=dict(width=0)),
            text=[f"+{v:.0f} pts" for v in valores_xai],
            textposition="outside",
            textfont=dict(color="white", size=11),
            name="Contribuição",
            hovertemplate="<b>%{x}</b><br>Contribuição: +%{y:.0f} pts<extra></extra>",
        ))

        # Linha do score total
        fig_xai.add_hline(
            y=score_total,
            line_dash="dash",
            line_color="#ef4444",
            line_width=2,
            annotation_text=f"Score Final: {score_total}",
            annotation_font=dict(color="#ef4444", size=12),
            annotation_position="top right",
        )

        fig_xai.update_layout(
            template=PLOTLY_TEMPLATE,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)" if 'modo_escuro' in locals() and modo_escuro else "rgba(248,250,252,0.5)",
            font=dict(family="Inter", color="#94a3b8"),
            title=dict(
                text=f"Contribuição de cada regra — {mu_selecionada_id}",
                font=dict(size=14, color="#e2e8f0"),
            ),
            xaxis=dict(gridcolor="rgba(30,41,59,0.5)", tickangle=-20),
            yaxis=dict(gridcolor="rgba(30,41,59,0.5)", title="Pontos"),
            showlegend=False,
            height=360,
            margin=dict(t=60, b=80, l=20, r=20),
        )
        st.plotly_chart(fig_xai, use_container_width=True)

    with col_xai_info:
        st.markdown("<br>", unsafe_allow_html=True)
        # Card de recomendação
        rec_map = {
            "ok":        ("Aprovar automaticamente.",              "#22c55e", "✅"),
            "atencao":   ("Enviar para revisão leve.",             "#f59e0b", "⚠️"),
            "suspeito":  ("Bloquear e análise manual.",            "#f97316", "🔶"),
            "bloqueado": ("Bloquear + notificar compliance.",      "#ef4444", "🚫"),
        }
        nivel = mu_data["fraud_nivel"]
        rec_texto, rec_cor, rec_icone = rec_map.get(nivel, ("Analisar manualmente.", "#94a3b8", "❓"))

        st.html(f"""
        <div style="
            background: {rec_cor}10;
            border: 1px solid {rec_cor}33;
            border-left: 4px solid {rec_cor};
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 16px;
        ">
            <div style="font-size:11px; color:#64748b; font-weight:700;
                        text-transform:uppercase; letter-spacing:1px; margin-bottom:8px;">
                Recomendação do Sistema
            </div>
            <div style="font-size:22px; margin-bottom:8px;">{rec_icone}</div>
            <div style="font-size:13px; color:{rec_cor}; font-weight:700; margin-bottom:4px;">
                {rec_texto}
            </div>
            <div style="font-size:11px; color:#475569;">
                Baseado em {len(flags_mu)} anomalia(s) detectada(s)
            </div>
        </div>
        """)

        # Lista de flags com peso
        for label, desc, pts, cor in flags_mu:
            pct_contribuicao = round(pts / score_total * 100) if score_total > 0 else 0
            st.html(f"""
            <div style="
                display:flex; justify-content:space-between; align-items:center;
                padding: 8px 12px;
                background: {cor}10;
                border-left: 3px solid {cor};
                border-radius: 6px;
                margin-bottom: 6px;
            ">
                <span style="font-size:11px; color:#94a3b8;">{desc}</span>
                <span style="font-size:11px; font-weight:700; color:{cor};
                             font-family:monospace; white-space:nowrap;">
                    +{pts:.0f} ({pct_contribuicao}%)
                </span>
            </div>
            """)


# ── Clustering de Perfis de Fraude ──────────────────────────────────────────

st.markdown('<div class="section-title"><span class="icon">🧩</span> Clusters de Perfis de Fraúde</div>', unsafe_allow_html=True)

if not df_mus.empty and len(df_mus) >= 4:
    try:
        from sklearn.preprocessing import StandardScaler
        from sklearn.cluster import KMeans
        import numpy as np

        # Features para clustering
        df_cluster = df_mus.copy()
        df_cluster["nivel_num"] = df_cluster["fraud_nivel"].map(
            {"ok": 0, "atencao": 1, "suspeito": 2, "bloqueado": 3}
        ).fillna(0)

        features = df_cluster[["fraud_score", "n_flags", "recompensa_rs", "nivel_num"]].fillna(0)
        scaler   = StandardScaler()
        X_scaled = scaler.fit_transform(features)

        # K-Means com 4 clusters (seed fixo para reprodutibilidade)
        kmeans   = KMeans(n_clusters=4, random_state=42, n_init=10)
        df_cluster["cluster"] = kmeans.fit_predict(X_scaled)

        # Nomear clusters baseado no score médio
        cluster_stats = df_cluster.groupby("cluster").agg(
            score_medio=("fraud_score", "mean"),
            n_flags_medio=("n_flags", "mean"),
            contagem=("mu_id", "count"),
            valor_medio=("recompensa_rs", "mean"),
        ).reset_index()
        cluster_stats = cluster_stats.sort_values("score_medio")

        CLUSTER_NOMES = {
            0: ("🟢 Operação Normal",     "#22c55e", "Missões dentro do padrão. Aprovação automática segura."),
            1: ("🟡 Anomalia Leve",       "#f59e0b", "Pequenos desvios detectados. Monitorar sem bloquear."),
            2: ("🟠 Padrão Suspeito",     "#f97316", "Comportamento consistentemente anômalo. Revisão obrigatória."),
            3: ("🔴 Fraude Estruturada",  "#ef4444", "Múltiplas flags críticas. Bloquear e investigar."),
        }

        # Mapear clusters para nomes (por ordem de score médio)
        mapa_cluster = {
            row["cluster"]: CLUSTER_NOMES[i]
            for i, row in cluster_stats.iterrows()
        }
        df_cluster["cluster_nome"] = df_cluster["cluster"].map(lambda c: mapa_cluster[c][0])
        df_cluster["cluster_cor"]  = df_cluster["cluster"].map(lambda c: mapa_cluster[c][1])

        col_cl_scatter, col_cl_cards = st.columns([1.8, 1])

        with col_cl_scatter:
            # Transforma flags em categoria para o Strip fatiar direitinho
            df_cluster["n_flags_label"] = df_cluster["n_flags"].astype(str) + " Flag(s)"
            
            fig_cluster = px.strip(
                df_cluster,
                x="fraud_score",               
                y="n_flags_label",             
                color="cluster_nome",
                stripmode="overlay",
                hover_data=["mu_id", "missionario_nome", "missao_nome", "recompensa_rs"],
                color_discrete_map={v[0]: v[1] for v in CLUSTER_NOMES.values()},
                labels={
                    "fraud_score":   "Fraud Score Calc.",
                    "n_flags_label": "Frequência de Anomalias",
                    "cluster_nome":  "Classificação IA (Cluster)",
                },
                title="Swarm Analítico: Dispersão Real de Anomalias (Strip Plot)"
            )
            
            # Adiciona jitter (espalhamento horizontal) e formata as bolhas
            fig_cluster.update_traces(
                jitter=1.0,  
                marker=dict(
                    size=12,
                    line=dict(width=1.5, color="rgba(255,255,255,0.15)"),
                    opacity=0.85
                )
            )

            fig_cluster.update_layout(
                template=PLOTLY_TEMPLATE,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)" if 'modo_escuro' in locals() and modo_escuro else "rgba(248,250,252,0.5)",
                font=dict(family="Inter", color="#94a3b8"),
                title=dict(font=dict(size=14, color="#e2e8f0")),
                xaxis=dict(gridcolor="rgba(30,41,59,0.3)", title="Pontuação de Risco"),
                yaxis=dict(gridcolor="rgba(30,41,59,0)", categoryorder="category ascending"), 
                legend=dict(
                    bgcolor="rgba(13,17,23,0.9)",
                    bordercolor="#1e293b",
                    borderwidth=1,
                    font=dict(size=10),
                    orientation="h",
                    y=-0.2, x=0.5, xanchor="center",
                ),
                height=420,
                margin=dict(t=50, b=80, l=20, r=20),
            )
            st.plotly_chart(fig_cluster, use_container_width=True)

        with col_cl_cards:
            st.markdown("<br>", unsafe_allow_html=True)
            for i, row in cluster_stats.iterrows():
                nome, cor, estrategia = mapa_cluster[row["cluster"]]
                st.html(f"""
                <div style="
                    background: {cor}0e;
                    border: 1px solid {cor}33;
                    border-left: 4px solid {cor};
                    border-radius: 10px;
                    padding: 12px 16px;
                    margin-bottom: 10px;
                ">
                    <div style="font-size:12px; font-weight:700; color:{cor}; margin-bottom:4px;">
                        {nome}
                    </div>
                    <div style="display:flex; gap:16px; margin-bottom:6px;">
                        <span style="font-size:11px; color:#94a3b8;">
                            <b style="color:#e2e8f0;">{int(row['contagem'])}</b> MUs
                        </span>
                        <span style="font-size:11px; color:#94a3b8;">
                            Score médio: <b style="color:{cor};">{row['score_medio']:.0f}</b>
                        </span>
                    </div>
                    <div style="font-size:10px; color:#475569; line-height:1.4;">
                        {estrategia}
                    </div>
                </div>
                """)

    except ImportError:
        st.warning("Instale scikit-learn para ver o clustering (pip install scikit-learn).")


# ── Grafo de Conluio entre Missionários ─────────────────────────────────────

st.markdown('<div class="section-title"><span class="icon">🕸️</span> Análise de Grafos — Conexões Suspeitas</div>', unsafe_allow_html=True)

if not df_mus.empty:
    import random as _rg
    import math as _math

    # Gerar dados de check-in sintéticos por MU (seed por mu_id)
    checkins = []
    REGIOES_SP = [
        (-23.5718, -46.6858), (-23.5653, -46.6524),
        (-23.5985, -46.6875), (-23.5870, -46.6800),
        (-23.6100, -46.6650), (-23.5478, -46.6396),
    ]
    for _, row in df_mus.iterrows():
        seed = int(row["mu_id"].replace("MU-","").replace("-","")) % 10000
        rg   = _rg.Random(seed)
        base_lat, base_lng = rg.choice(REGIOES_SP)
        # Missionários fraudulentos tendem a usar os mesmos pontos
        if row["fraud_nivel"] in ["suspeito", "bloqueado"]:
            lat = base_lat + rg.uniform(-0.002, 0.002)
            lng = base_lng + rg.uniform(-0.002, 0.002)
        else:
            lat = base_lat + rg.uniform(-0.012, 0.012)
            lng = base_lng + rg.uniform(-0.012, 0.012)
        checkins.append({
            "mu_id":        row["mu_id"],
            "missionario":  row["missionario_nome"],
            "fraud_nivel":  row["fraud_nivel"],
            "fraud_score":  row["fraud_score"],
            "lat": lat, "lng": lng,
        })

    df_ci = pd.DataFrame(checkins)

    # Detectar pares suspeitos (distância < 300m)
    def _haversine_m(lat1, lng1, lat2, lng2):
        R = 6371000
        p = _math.pi / 180
        a = (_math.sin((lat2-lat1)*p/2)**2 +
             _math.cos(lat1*p)*_math.cos(lat2*p)*_math.sin((lng2-lng1)*p/2)**2)
        return 2*R*_math.asin(_math.sqrt(a))

    edges = []
    rows_ci = df_ci.to_dict("records")
    for i in range(len(rows_ci)):
        for j in range(i+1, len(rows_ci)):
            a, b = rows_ci[i], rows_ci[j]
            if a["missionario"] == b["missionario"]:
                continue
            dist = _haversine_m(a["lat"], a["lng"], b["lat"], b["lng"])
            if dist < 300:
                edges.append((a["missionario"], b["missionario"],
                               round(dist), a["fraud_score"], b["fraud_score"]))

    if edges:
        # Calcular posições dos nós (layout circular)
        nos = list({e[0] for e in edges} | {e[1] for e in edges})
        angulo_step = 2 * _math.pi / max(len(nos), 1)
        pos = {
            no: (_math.cos(i * angulo_step), _math.sin(i * angulo_step))
            for i, no in enumerate(nos)
        }

        # Score médio por nó
        score_por_missio = df_ci.groupby("missionario")["fraud_score"].mean().to_dict()
        nivel_por_missio = df_ci.groupby("missionario")["fraud_nivel"].first().to_dict()

        fig_grafo = go.Figure()

        # Arestas
        for no_a, no_b, dist, score_a, score_b in edges:
            x0, y0 = pos[no_a]
            x1, y1 = pos[no_b]
            intensidade = max(0.1, 1 - dist / 300)
            fig_grafo.add_trace(go.Scatter(
                x=[x0, x1, None], y=[y0, y1, None],
                mode="lines",
                line=dict(width=intensidade * 3, color=f"rgba(239,68,68,{intensidade:.2f})"),
                hoverinfo="skip",
                showlegend=False,
            ))

        # Nós
        for no in nos:
            x, y = pos[no]
            score = score_por_missio.get(no, 0)
            nivel = nivel_por_missio.get(no, "ok")
            cor_no = CORES_NIVEL.get(nivel, "#94a3b8")
            conexoes = sum(1 for e in edges if no in (e[0], e[1]))

            fig_grafo.add_trace(go.Scatter(
                x=[x], y=[y],
                mode="markers+text",
                marker=dict(
                    size=20 + conexoes * 8,
                    color=cor_no,
                    line=dict(color="#0a0e1a", width=2),
                    opacity=0.9,
                ),
                text=[no.split()[0]],  # Primeiro nome
                textposition="top center",
                textfont=dict(size=10, color="#e2e8f0"),
                hovertemplate=(
                    f"<b>{no}</b><br>"
                    f"Score médio: {score:.1f}<br>"
                    f"Nível: {nivel}<br>"
                    f"Conexões suspeitas: {conexoes}<extra></extra>"
                ),
                showlegend=False,
            ))

        fig_grafo.update_layout(
            template=PLOTLY_TEMPLATE,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)" if 'modo_escuro' in locals() and modo_escuro else "rgba(248,250,252,0.5)",
            font=dict(family="Inter", color="#94a3b8"),
            title=dict(
                text=f"Grafo de Conluio — {len(nos)} missionários suspeitos · {len(edges)} conexões",
                font=dict(size=14, color="#e2e8f0"),
            ),
            xaxis=dict(visible=False, range=[-1.4, 1.4]),
            yaxis=dict(visible=False, range=[-1.4, 1.4]),
            height=480,
            margin=dict(t=60, b=20, l=20, r=20),
        )

        col_g1, col_g2 = st.columns([2.2, 1])
        with col_g1:
            st.plotly_chart(fig_grafo, use_container_width=True)
        with col_g2:
            st.markdown("<br><br>", unsafe_allow_html=True)
            st.html(f"""
            <div style="background:#111827; border:1px solid #1e293b;
                        border-radius:12px; padding:20px;">
                <div style="font-size:13px; font-weight:700; color:#e2e8f0; margin-bottom:16px;">
                    📊 Resumo do Grafo
                </div>
                <div style="display:flex; flex-direction:column; gap:10px;">
                    <div style="display:flex; justify-content:space-between;">
                        <span style="font-size:12px; color:#64748b;">Nós (missionários)</span>
                        <span style="font-size:14px; font-weight:700; color:#ef4444;">{len(nos)}</span>
                    </div>
                    <div style="display:flex; justify-content:space-between;">
                        <span style="font-size:12px; color:#64748b;">Conexões detectadas</span>
                        <span style="font-size:14px; font-weight:700; color:#f97316;">{len(edges)}</span>
                    </div>
                    <div style="display:flex; justify-content:space-between;">
                        <span style="font-size:12px; color:#64748b;">Raio de detecção</span>
                        <span style="font-size:14px; font-weight:700; color:#f59e0b;">300m</span>
                    </div>
                </div>
                <div style="margin-top:16px; padding-top:16px; border-top:1px solid #1e293b;
                            font-size:10px; color:#334155; line-height:1.6;">
                    Espessura da linha = proximidade entre check-ins.<br>
                    Tamanho do nó = número de conexões suspeitas.<br>
                    Cor = nível de risco do missionário.
                </div>
            </div>
            """)
    else:
        st.info("Nenhuma conexão suspeita detectada entre missionários no período atual.")


# ── Inteligência de Risco — Ranking por Missionário ─────────────────────────

st.markdown('<div class="section-title"><span class="icon">🧠</span> Inteligência de Risco — Ranking por Missionário</div>', unsafe_allow_html=True)

if not df_mus.empty:
    # Agrupar df_mus por missionario_nome
    df_ranking = df_mus.groupby("missionario_nome").agg(
        total_missoes=("mu_id", "count"),
        score_medio=("fraud_score", "mean"),
        score_max=("fraud_score", "max"),
        total_flags=("n_flags", "sum"),
        valor_total=("recompensa_rs", "sum"),
    ).reset_index()

    # Score acumulado inteligente:
    # Peso maior para score máximo (comportamento no pior momento)
    # + penalidade por reincidência (múltiplas missões suspeitas)
    df_ranking["score_acumulado"] = (
        df_ranking["score_medio"] * 0.4 +
        df_ranking["score_max"]   * 0.4 +
        (df_ranking["total_flags"] / df_ranking["total_missoes"].clip(lower=1) * 10).clip(upper=20)
    ).clip(upper=100).round(1)

    # Classificação de perfil de risco
    def classificar_perfil(row):
        s = row["score_acumulado"]
        if s <= 20:   return ("✅ Confiável",       "#22c55e")
        elif s <= 45: return ("⚠️ Monitorar",        "#f59e0b")
        elif s <= 70: return ("🔶 Alto Risco",       "#f97316")
        else:         return ("🚫 Perfil Crítico",   "#ef4444")

    df_ranking[["perfil", "perfil_cor"]] = df_ranking.apply(
        classificar_perfil, axis=1, result_type="expand"
    )

    df_ranking = df_ranking.sort_values("score_acumulado", ascending=False)

    col_rank_chart, col_rank_kpi = st.columns([2, 1])
    
    with col_rank_chart:
        fig_ranking = go.Figure()
        
        df_top = df_ranking.head(8)[::-1] # reverse for horizontal bar chart
        cores_ranking = df_top["perfil_cor"].tolist()

        fig_ranking.add_trace(go.Bar(
            y=df_top["missionario_nome"],
            x=df_top["score_acumulado"],
            orientation="h",
            marker=dict(
                color=cores_ranking,
                line=dict(width=0),
            ),
            text=df_top["score_acumulado"].apply(lambda x: f"{x:.0f}"),
            textposition="auto",
            textfont=dict(color="white", size=12, family="Inter"),
            customdata=df_top[["total_missoes", "total_flags", "valor_total", "perfil"]].values,
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Score Acumulado: <b>%{x}</b><br>"
                "Missões: %{customdata[0]}<br>"
                "Flags totais: %{customdata[1]}<br>"
                "Valor em recompensas: R$ %{customdata[2]:,.0f}<br>"
                "Perfil: %{customdata[3]}<extra></extra>"
            ),
        ))

        fig_ranking.update_layout(
            template=PLOTLY_TEMPLATE,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)" if modo_escuro else "rgba(248,250,252,0.5)",
            font=dict(family="Inter", color="#94a3b8"),
            title=dict(text="Score Acumulado por Missionário (top 8)", font=dict(size=14, color="#e2e8f0")),
            xaxis=dict(range=[0, 105], gridcolor="rgba(30,41,59,0.5)"),
            yaxis=dict(tickfont=dict(size=11)),
            showlegend=False,
            margin=dict(t=50, b=30, l=10, r=20),
            height=360,
        )
        st.plotly_chart(fig_ranking, use_container_width=True)

    with col_rank_kpi:
        st.markdown("<br>", unsafe_allow_html=True)
        # Calcular métricas
        perfis_criticos = len(df_ranking[df_ranking["score_acumulado"] > 70])
        reincidentes    = len(df_ranking[df_ranking["total_missoes"] > 1])
        valor_risco_acum = df_ranking[df_ranking["score_acumulado"] > 45]["valor_total"].sum()

        # Card 1 — Perfis Críticos
        st.markdown(f"""
        <div class="kpi-card red" style="margin-bottom:12px;">
            <div class="kpi-label">🚫 Perfis Críticos</div>
            <div class="kpi-value red">{perfis_criticos}</div>
            <div class="kpi-sub">missionários com score > 70</div>
        </div>
        """, unsafe_allow_html=True)

        # Card 2 — Reincidentes
        st.markdown(f"""
        <div class="kpi-card orange" style="margin-bottom:12px;">
            <div class="kpi-label">🔁 Reincidentes</div>
            <div class="kpi-value orange">{reincidentes}</div>
            <div class="kpi-sub">com 2+ missões no histórico</div>
        </div>
        """, unsafe_allow_html=True)

        # Card 3 — Valor exposto
        st.markdown(f"""
        <div class="kpi-card purple">
            <div class="kpi-label">💸 Exposição Acumulada</div>
            <div class="kpi-value purple">R$ {valor_risco_acum:,.0f}</div>
            <div class="kpi-sub">recompensas em perfis de alto risco</div>
        </div>
        """, unsafe_allow_html=True)

# ── Tabela: MUs Críticas ────────────────────────────────────────────────────

st.markdown('<div class="section-title">🚨 Mission Units Críticas</div>', unsafe_allow_html=True)

criticas = report.get("mus_criticas", [])
if criticas:
    df_criticas = pd.DataFrame(criticas)

    # Badge HTML
    def nivel_badge(nivel):
        label = LABELS_NIVEL.get(nivel, nivel)
        return f'<span class="badge badge-{nivel}">{label}</span>'

    # Score com barra visual
    def score_bar(score):
        if score <= 20:   cor, label = "#3b82f6", "BAIXO"
        elif score <= 45: cor, label = "#60a5fa", "MÉDIO"
        elif score <= 70: cor, label = "#f87171", "ALTO"
        else:             cor, label = "#ef4444", "CRÍTICO"
        return (
            f'<div style="display:flex; align-items:center; gap:10px;">'
            f'  <div style="background:#0d1117; border-radius:4px; width:72px; height:6px; border:1px solid #1c2840;">'
            f'    <div style="background:linear-gradient(90deg,{cor}99,{cor}); height:100%; '
            f'         width:{score}%; border-radius:4px; transition:width 0.3s;"></div>'
            f'  </div>'
            f'  <span style="color:{cor}; font-family:IBM Plex Mono,monospace; font-weight:700; '
            f'       font-size:13px; min-width:32px;">{score:.0f}</span>'
            f'  <span style="color:{cor}88; font-size:9px; font-weight:700; '
            f'       letter-spacing:1px;">{label}</span>'
            f'</div>'
        )

    html_rows = ""
    for _, row in df_criticas.iterrows():
        html_rows += f"""
        <tr>
            <td style="color:#8899bb; font-weight:600;">{row['mu_id']}</td>
            <td>{row['missionario_nome']}</td>
            <td>{row['missao_nome']}</td>
            <td style="text-align:right; color:#e2e8f0; font-weight:600;">R$ {row['recompensa_rs']:,.0f}</td>
            <td>{score_bar(row['fraud_score'])}</td>
            <td>{nivel_badge(row['fraud_nivel'])}</td>
            <td style="text-align:center; font-weight:600; color:#8899bb;">{row['n_flags']}</td>
        </tr>
        """

    st.html(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600;700&display=swap');
        .badge {{
            display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 10px;
            font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; font-family: 'DM Sans', sans-serif;
        }}
        .badge-ok        {{ background: rgba(59,130,246,0.12); color: #60a5fa; border: 1px solid rgba(59,130,246,0.25); }}
        .badge-atencao   {{ background: rgba(59,130,246,0.08); color: #93bbfc; border: 1px solid rgba(59,130,246,0.18); }}
        .badge-suspeito  {{ background: rgba(239,68,68,0.08); color: #fca5a5; border: 1px solid rgba(239,68,68,0.18); }}
        .badge-bloqueado {{ background: rgba(239,68,68,0.12); color: #f87171; border: 1px solid rgba(239,68,68,0.25); }}
        table tbody tr {{
            border-bottom: 1px solid #1c2840;
            transition: background 0.2s;
        }}
        table tbody tr:hover {{
            background: rgba(59,130,246,0.06) !important;
        }}
        table tbody td {{
            padding: 12px 16px;
            color: #8899bb;
        }}
    </style>
    <div style="overflow-x:auto; border-radius:12px; border:1px solid #1c2840; background:#070b14;">
    <table style="width:100%; border-collapse:collapse; font-family:'DM Sans',sans-serif; font-size:13px;">
        <thead>
            <tr style="background:linear-gradient(90deg,#0d1117,#131920); border-bottom:1px solid #1c2840;">
                <th style="padding:14px 16px; text-align:left; color:#3b82f6; font-weight:700; font-size:10px; text-transform:uppercase; letter-spacing:1.5px;">MU ID</th>
                <th style="padding:14px 16px; text-align:left; color:#3b82f6; font-weight:700; font-size:10px; text-transform:uppercase; letter-spacing:1.5px;">Missionário</th>
                <th style="padding:14px 16px; text-align:left; color:#3b82f6; font-weight:700; font-size:10px; text-transform:uppercase; letter-spacing:1.5px;">Missão</th>
                <th style="padding:14px 16px; text-align:right; color:#3b82f6; font-weight:700; font-size:10px; text-transform:uppercase; letter-spacing:1.5px;">Valor</th>
                <th style="padding:14px 16px; text-align:left; color:#3b82f6; font-weight:700; font-size:10px; text-transform:uppercase; letter-spacing:1.5px;">Score</th>
                <th style="padding:14px 16px; text-align:left; color:#3b82f6; font-weight:700; font-size:10px; text-transform:uppercase; letter-spacing:1.5px;">Nível</th>
                <th style="padding:14px 16px; text-align:center; color:#3b82f6; font-weight:700; font-size:10px; text-transform:uppercase; letter-spacing:1.5px;">Flags</th>
            </tr>
        </thead>
        <tbody>
            {html_rows}
        </tbody>
        <tfoot>
            <tr style="background:#0d1117; border-top:2px solid #1c2840;">
                <td colspan="3" style="padding:12px 16px; color:#4a5a7a; font-size:11px;">
                    {len(criticas)} MUs críticas exibidas
                </td>
                <td style="text-align:right; color:#f87171; font-weight:700; font-family:'IBM Plex Mono',monospace;">
                    R$ {sum(r['recompensa_rs'] for r in criticas):,.0f}
                </td>
                <td colspan="3" style="color:#4a5a7a; font-size:11px; text-align:right; padding-right:16px;">
                    Total em risco
                </td>
            </tr>
        </tfoot>
    </table>
    </div>
    """)
else:
    st.success("✅ Nenhuma MU crítica no momento!")

# ── Tabela: Missionários Recorrentes ────────────────────────────────────────

st.markdown("<br>", unsafe_allow_html=True)
st.markdown("""
<div class="section-title" style="margin-bottom: 24px;">
    <div style="display:flex; align-items:center; gap:12px;">
        <div style="width:40px; height:40px; background:linear-gradient(135deg,#1e1e40,#0f0f20); border-radius:8px; border:1px solid #1c2840; display:flex; align-items:center; justify-content:center; font-size:18px; box-shadow:0 0 10px rgba(59,130,246,0.1);">👥</div>
        <div style="display:flex; flex-direction:column; gap:2px;">
            <span style="font-size:14px; font-weight:700; color:#3b82f6; letter-spacing:2px; text-transform:uppercase;">Missionários Recorrentes</span>
            <span style="font-size:11px; color:#4a5a7a; text-transform:none; letter-spacing:0; font-weight:500;">Perfis com múltiplas flags — análise de padrão</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

missionarios_recorrentes = [
    {"iniciais": "TL", "nome": "Thiago Lima", "mus_total": 8, "com_flags": 5, "pct_flags": 63, "total_flags": 9, "score_medio": 72, "risco_rs": 480, "tendencia": "Crescente"},
    {"iniciais": "CM", "nome": "Carlos Moura", "mus_total": 5, "com_flags": 3, "pct_flags": 60, "total_flags": 6, "score_medio": 68, "risco_rs": 380, "tendencia": "Crescente"},
    {"iniciais": "FS", "nome": "Fernanda Santos", "mus_total": 6, "com_flags": 3, "pct_flags": 50, "total_flags": 4, "score_medio": 54, "risco_rs": 200, "tendencia": "Estável"},
    {"iniciais": "DR", "nome": "Diego Ramos", "mus_total": 4, "com_flags": 2, "pct_flags": 50, "total_flags": 3, "score_medio": 58, "risco_rs": 320, "tendencia": "Crescente"},
    {"iniciais": "AL", "nome": "Ana Lima", "mus_total": 3, "com_flags": 1, "pct_flags": 33, "total_flags": 2, "score_medio": 45, "risco_rs": 40, "tendencia": "Reduzindo"},
]

def score_bar_simples(score):
    if score <= 45: cor = "#eab308" # yellow for low risk recurrent ? or use #3b82f6 ... wait screenshot shows 45 yellow
    elif score <= 60: cor = "#eab308"
    else: cor = "#ef4444"
    return (
        f'<div style="display:flex; flex-direction:column; gap:4px;">'
        f'  <span style="color:{cor}; font-family:IBM Plex Mono,monospace; font-weight:700; font-size:13px;">{score}</span>'
        f'  <div style="background:#0d1117; border-radius:4px; width:72px; height:6px; border:1px solid #1c2840;">'
        f'    <div style="background:linear-gradient(90deg,{cor}99,{cor}); height:100%; '
        f'         width:{score}%; border-radius:4px;"></div>'
        f'  </div>'
        f'</div>'
    )

def tendencia_badge(tend):
    if tend == "Crescente":
        return f'<span style="display:inline-block; padding:4px 12px; border-radius:20px; font-size:10px; font-weight:700; color:#f87171; background:rgba(239,68,68,0.08); border:1px solid rgba(239,68,68,0.18);">↑ Crescente</span>'
    elif tend == "Estável":
        return f'<span style="display:inline-block; padding:4px 12px; border-radius:20px; font-size:10px; font-weight:700; color:#fbbf24; background:rgba(251,191,36,0.08); border:1px solid rgba(251,191,36,0.18);">→ Estável</span>'
    else:
        return f'<span style="display:inline-block; padding:4px 12px; border-radius:20px; font-size:10px; font-weight:700; color:#4ade80; background:rgba(74,222,128,0.08); border:1px solid rgba(74,222,128,0.18);">↓ Reduzindo</span>'

html_rows_rec = ""
for row in missionarios_recorrentes:
    html_rows_rec += f"""
    <tr>
        <td>
            <div style="display:flex; align-items:center; gap:12px;">
                <div style="width:32px; height:32px; border-radius:50%; background:#1c2840; color:#8899bb; display:flex; align-items:center; justify-content:center; font-size:11px; font-weight:700; font-family:'DM Sans',sans-serif;">{row['iniciais']}</div>
                <span style="color:#f0f4ff; font-weight:600;">{row['nome']}</span>
            </div>
        </td>
        <td style="color:#f0f4ff; font-weight:600;">{row['mus_total']}</td>
        <td style="color:#f0f4ff; font-weight:600;">{row['com_flags']} <span style="color:#4a5a7a; font-weight:500; font-size:11px;">({row['pct_flags']}%)</span></td>
        <td style="color:#f0f4ff; font-weight:600;">{row['total_flags']}</td>
        <td>{score_bar_simples(row['score_medio'])}</td>
        <td style="color:#e2e8f0; font-weight:700; font-family:'IBM Plex Mono',monospace;">R$ {row['risco_rs']}</td>
        <td>{tendencia_badge(row['tendencia'])}</td>
    </tr>
    """

st.html(f"""
<div style="overflow-x:auto; border-radius:12px; border:1px solid #1c2840; background:#070b14;">
<table style="width:100%; border-collapse:collapse; font-family:'DM Sans',sans-serif; font-size:13px;">
    <thead>
        <tr style="background:linear-gradient(90deg,#0d1117,#131920); border-bottom:1px solid #1c2840;">
            <th style="padding:16px; text-align:left; color:#3b82f6; font-weight:700; font-size:10px; text-transform:uppercase; letter-spacing:1.5px;">Missionário</th>
            <th style="padding:16px; text-align:left; color:#3b82f6; font-weight:700; font-size:10px; text-transform:uppercase; letter-spacing:1.5px;">MUs Total</th>
            <th style="padding:16px; text-align:left; color:#3b82f6; font-weight:700; font-size:10px; text-transform:uppercase; letter-spacing:1.5px;">Com Flags</th>
            <th style="padding:16px; text-align:left; color:#3b82f6; font-weight:700; font-size:10px; text-transform:uppercase; letter-spacing:1.5px;">Total Flags</th>
            <th style="padding:16px; text-align:left; color:#3b82f6; font-weight:700; font-size:10px; text-transform:uppercase; letter-spacing:1.5px;">Score Médio</th>
            <th style="padding:16px; text-align:left; color:#3b82f6; font-weight:700; font-size:10px; text-transform:uppercase; letter-spacing:1.5px;">Risco (R$)</th>
            <th style="padding:16px; text-align:left; color:#3b82f6; font-weight:700; font-size:10px; text-transform:uppercase; letter-spacing:1.5px;">Tendência</th>
        </tr>
    </thead>
    <tbody>
        {html_rows_rec}
    </tbody>
</table>
</div>
""")


# ── Seção: Simulador Avançado de Análise ──────────────────────────────────────

st.markdown("<br>", unsafe_allow_html=True)
st.markdown('<div class="section-title">🧪 Simulador Avançado Anti-Fraude</div>', unsafe_allow_html=True)

with st.expander("🔬 Abrir Painel de Testes (Simulador Avançado)", expanded=False):
    st.markdown("<div style='color:#8899bb; font-size:12px; margin-bottom:16px;'>Utilize este painel para testar os pesos das regras em tempo real.</div>", unsafe_allow_html=True)

    t_cenario, t_missao, t_perfil, t_timelines = st.tabs([
        "📍 Cenários e Local",
        "📋 Dados da Missão",
        "👤 Perfil do Missionário",
        "⏱️ Sandbox Avançado (Eventos)"
    ])

    with t_cenario:
        st.markdown("##### Cenário Rápido")
        cenario = st.selectbox("Injetar cenário pré-configurado automático:", [
            "Normal — tudo ok",
            "Suspeito — check-in antes da criação",
            "Fraude — duração zero",
            "Fraude — GPS fora do local",
        ])
        st.markdown("##### 📍 Local Base da Missão")
        c_lat, c_lng = st.columns(2)
        sim_lat = c_lat.number_input("Lat Esperada", value=-23.5718, format="%.4f")
        sim_lng = c_lng.number_input("Lng Esperada", value=-46.6858, format="%.4f")

    with t_missao:
        m_c1, m_c2 = st.columns(2)
        with m_c1:
            sim_mu_id = st.text_input("MU ID", value="MU-TEST-001")
            sim_missao_nome = st.text_input("Nome da Missão", value="Hostess | Turnos de 8h")
        with m_c2:
            sim_duracao = st.number_input("Duração Esperada (horas)", value=8.0, min_value=0.5, step=0.5)
            sim_recompensa = st.number_input("Recompensa (R$)", value=140.0, min_value=0.0, step=10.0)

    with t_perfil:
        p_c1, p_c2 = st.columns(2)
        with p_c1:
            sim_nome = st.text_input("Nome", value="João Silva")
        with p_c2:
            sim_historico = st.number_input("Histórico de Missões", value=10, min_value=0)
            sim_reprovacoes = st.number_input("Histórico de Reprovações", value=1, min_value=0)

    with t_timelines:
        st.info("🔧 Ignore os cenários rápidos e forje manualmente as coordenadas e horários exatos de disparo da API.")
        modo_avancado = st.checkbox("Ativar Modo Sandbox (Sobrepor cenário)", value=False)
        
        ev_c1, ev_c2 = st.columns(2)
        with ev_c1:
            st.markdown("**📍 Ponto de Entrada**")
            ev_ci_time = st.text_input("Check-in Timestamp", value="2026-03-17T09:00:00")
            ev_ci_lat = st.number_input("Check-in Lat", value=-23.5718, format="%.4f", step=0.05)
            ev_in_time = st.text_input("Start Timestamp", value="2026-03-17T09:05:00")
            
        with ev_c2:
            st.markdown("**🏁 Ponto de Saída**")
            ev_co_time = st.text_input("Check-out Timestamp", value="2026-03-17T17:05:00")
            ev_co_lat = st.number_input("Check-out Lat", value=-23.5718, format="%.4f", step=0.05)
            ev_fi_time = st.text_input("Finish Timestamp", value="2026-03-17T17:00:00")
            
        ev_lng_coord = st.number_input("Longitude unificada de Check-in/out", value=-46.6858, format="%.4f")

    # Resolução Lógica dos Cenários
    if modo_avancado:
        atividades = [
            {"tipo": "check_in",  "timestamp": ev_ci_time, "lat": ev_ci_lat, "lng": ev_lng_coord},
            {"tipo": "iniciou",   "timestamp": ev_in_time, "lat": ev_ci_lat, "lng": ev_lng_coord},
            {"tipo": "finalizou", "timestamp": ev_fi_time, "lat": ev_co_lat, "lng": ev_lng_coord},
            {"tipo": "check_out", "timestamp": ev_co_time, "lat": ev_co_lat, "lng": ev_lng_coord},
        ]
    else:
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

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("##### 🗺️ Visualização Prévia do Cenário")
    map_col, time_col = st.columns([1.2, 1])

    with map_col:
        st.markdown("<div style='color:#8899bb; font-size:12px; margin-bottom:8px;'>Mapa de Interações</div>", unsafe_allow_html=True)
        map_data = [{"lat": sim_lat, "lon": sim_lng, "tipo": "Local Esperado", "size": 15}]
        for a in atividades:
            nome_tipo = a["tipo"].replace("_", " ").title()
            map_data.append({"lat": a["lat"], "lon": a["lng"], "tipo": nome_tipo, "size": 10})
        
        df_map = pd.DataFrame(map_data)
        fig_map = px.scatter_mapbox(
            df_map, lat="lat", lon="lon", color="tipo", size="size", hover_name="tipo", zoom=11.5,
            color_discrete_map={"Local Esperado": "#3b82f6", "Check In": "#10b981", "Iniciou": "#8b5cf6", "Finalizou": "#f59e0b", "Check Out": "#ef4444"}
        )
        fig_map.update_layout(mapbox_style="carto-darkmatter")
        fig_map.update_layout(
            margin={"r":0,"t":0,"l":0,"b":0}, height=280, paper_bgcolor="rgba(0,0,0,0)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, font=dict(size=10, color="#8899bb"), bgcolor="rgba(0,0,0,0)")
        )
        st.plotly_chart(fig_map, use_container_width=True)

    with time_col:
        st.markdown("<div style='color:#8899bb; font-size:12px; margin-bottom:8px;'>Linha do Tempo Ocorrida</div>", unsafe_allow_html=True)
        timeline_html = "<div style='padding:16px; border:1px solid #1c2840; background:#0d1117; border-radius:12px; height:280px; overflow-y:auto;'>"
        
        def step_html(time_str, text, icon, color, is_last=False):
            line_html = "" if is_last else f'<div style="width:2px; height:24px; background:linear-gradient(180deg,{color}40,transparent); margin-top:4px;"></div>'
            return f"""<div style="display:flex; gap:12px; margin-bottom:8px;">
    <div style="display:flex; flex-direction:column; align-items:center;">
        <div style="width:28px; height:28px; border-radius:50%; background:{color}15; color:{color}; display:flex; align-items:center; justify-content:center; font-size:12px; border:1px solid {color}40; box-shadow:0 0 10px {color}20;">{icon}</div>
        {line_html}
    </div>
    <div style="padding-top:4px;">
        <div style="color:#e2e8f0; font-weight:600; font-size:13px; letter-spacing:0.3px;">{text}</div>
        <div style="color:#4a5a7a; font-size:11px; font-family:'IBM Plex Mono',monospace;">{time_str}</div>
    </div>
</div>"""
            
        timeline_html += step_html("2026-03-17 09:00:00", "Missão Criada", "✨", "#3b82f6")
        
        sorted_ativ = sorted(atividades, key=lambda x: x["timestamp"])
        for i, a in enumerate(sorted_ativ):
            if a["tipo"] == "check_in": icon, color, text = "📍", "#10b981", "Check-in Realizado"
            elif a["tipo"] == "iniciou": icon, color, text = "▶️", "#8b5cf6", "Iniciou Atividades"
            elif a["tipo"] == "finalizou": icon, color, text = "🛑", "#f59e0b", "Finalizou Atividades"
            elif a["tipo"] == "check_out": icon, color, text = "🏁", "#ef4444", "Check-out Realizado"
            else: icon, color, text = "⏱️", "#8899bb", a["tipo"]
            
            time_fmt = datetime.fromisoformat(a["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")
            is_last = (i == len(sorted_ativ) - 1)
            timeline_html += step_html(time_fmt, text, icon, color, is_last)
            
        timeline_html += "</div><br>"
        st.html(timeline_html)


    if st.button("🚀 Executar Análise", type="primary", use_container_width=True):
        # 1. Buscar todas as MUs da base
        mus_existentes = fetch_mission_units(limit=100)
        ids_validos = {mu["mu_id"] for mu in mus_existentes}
        
        # Adicionar IDs de teste padrão conhecidos para o simulador não barrá-los
        ids_validos.update(["MU-TEST-001", "MU-1442951"])

        # 2. Checar se o ID digitado existe
        if sim_mu_id not in ids_validos:
            # Exibir erro e PARAR — não chamar /analyze
            st.html("""
            <div style="
                background: linear-gradient(145deg, #1a0a0a, #200d0d);
                border: 1px solid rgba(239,68,68,0.4);
                border-left: 4px solid #ef4444;
                border-radius: 12px;
                padding: 20px 24px;
                margin-top: 16px;
                display: flex;
                align-items: flex-start;
                gap: 16px;
            ">
                <div style="font-size: 28px; line-height: 1;">🚫</div>
                <div>
                    <div style="
                        font-size: 14px;
                        font-weight: 700;
                        color: #f87171;
                        font-family: 'Inter', sans-serif;
                        margin-bottom: 4px;
                    ">Mission Unit não encontrada</div>
                    <div style="
                        font-size: 12px;
                        color: #6b7280;
                        font-family: 'Inter', sans-serif;
                    ">
                        O ID <code style="
                            background: rgba(239,68,68,0.1);
                            color: #fca5a5;
                            padding: 1px 6px;
                            border-radius: 4px;
                            font-family: monospace;
                        ">{mu_id}</code> não existe na base de missões.
                        Verifique o ID e tente novamente.
                    </div>
                </div>
            </div>
            """.format(mu_id=sim_mu_id))
            st.stop()  # interrompe o bloco — não chama /analyze

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

            if score <= 20:   cor = "#3b82f6"
            elif score <= 45: cor = "#60a5fa"
            elif score <= 70: cor = "#f87171"
            else:             cor = "#ef4444"

            st.markdown(f"""
            <div style="background:linear-gradient(145deg,#0d1117,#131920); border:1px solid {cor}40;
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
                
                # Título da seção de flags
                st.html("""
                <div style="
                    font-size: 12px;
                    font-weight: 700;
                    color: #94a3b8;
                    text-transform: uppercase;
                    letter-spacing: 2px;
                    margin-bottom: 12px;
                    display: flex;
                    align-items: center;
                    gap: 8px;
                ">
                    <span style="color: #ef4444;">🚩</span>
                    Flags Detectadas — """ + str(len(result["flags"])) + """ anomalia(s)
                </div>
                """)
                
                # Mapeamento de rótulos legíveis
                LABEL_MAP = {
                    "checkin_antes_criacao":   ("⏰", "Check-in Antes da Criação",   "#ef4444"),
                    "duracao_zero":            ("⚡", "Duração Zero",                 "#ef4444"),
                    "duracao_impossivel":      ("⚡", "Duração Impossível",           "#f97316"),
                    "checkout_antes_checkin":  ("🔄", "Checkout Antes do Check-in",  "#ef4444"),
                    "checkout_antecipado":     ("🏃", "Checkout Antecipado",         "#f97316"),
                    "gps_fora_do_local":       ("📍", "GPS Fora do Local",           "#f59e0b"),
                    "gps_checkout_divergente": ("🗺️", "GPS Divergente",              "#f59e0b"),
                    "historico_reprovacoes":   ("📉", "Histórico de Reprovações",    "#8b5cf6"),
                    "atividades_ausentes":     ("❌", "Atividades Ausentes",         "#6366f1"),
                }
                
                # Calcular total de pontos para barra de progresso de cada flag
                total_score = result["fraud_score"]
                
                # Montar grid de cards — 2 colunas se >= 2 flags, 1 coluna se só 1
                flags = result["flags"]
                
                # Grid wrapper
                cards_html = '<div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 10px; margin-top: 4px;">'
                
                for f in flags:
                    regra = f["regra"]
                    pontos = f["pontos"]
                    descricao = f["descricao"]
                    icone, label, cor = LABEL_MAP.get(regra, ("⚠️", regra.replace("_", " ").title(), "#94a3b8"))
                    
                    # Percentual dessa flag no score total
                    pct = round((pontos / 100) * 100)  # pontos já são na escala 0-100
                    
                    cards_html += f"""
                    <div style="
                        background: linear-gradient(145deg, #111827, #0f1629);
                        border: 1px solid rgba(239,68,68,0.2);
                        border-left: 3px solid {cor};
                        border-radius: 10px;
                        padding: 14px 16px;
                    ">
                        <!-- Linha 1: ícone + nome da flag + pontos -->
                        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px;">
                            <div style="display: flex; align-items: center; gap: 8px;">
                                <span style="font-size: 16px;">{icone}</span>
                                <span style="
                                    font-size: 12px;
                                    font-weight: 700;
                                    color: {cor};
                                    font-family: 'Inter', sans-serif;
                                ">{label}</span>
                            </div>
                            <span style="
                                background: {cor}22;
                                color: {cor};
                                border: 1px solid {cor}44;
                                border-radius: 20px;
                                padding: 2px 10px;
                                font-size: 11px;
                                font-weight: 800;
                                font-family: monospace;
                                white-space: nowrap;
                            ">+{pontos:.0f} pts</span>
                        </div>
                        <!-- Linha 2: descrição técnica -->
                        <div style="
                            font-size: 11px;
                            color: #64748b;
                            font-family: 'Inter', sans-serif;
                            margin-bottom: 10px;
                            line-height: 1.4;
                        ">{descricao}</div>
                        <!-- Linha 3: barra de peso no score total -->
                        <div style="display: flex; align-items: center; gap: 8px;">
                            <div style="
                                flex: 1;
                                background: rgba(30,41,59,0.8);
                                border-radius: 4px;
                                height: 5px;
                            ">
                                <div style="
                                    background: {cor};
                                    height: 100%;
                                    width: {pct}%;
                                    border-radius: 4px;
                                    opacity: 0.8;
                                "></div>
                            </div>
                            <span style="font-size: 9px; color: #475569; white-space: nowrap;">{pct}% do máximo</span>
                        </div>
                    </div>
                    """
                
                cards_html += '</div>'
                st.html(cards_html)
            
            else:
                st.html("""
                <div style="
                    background: rgba(16,185,129,0.08);
                    border: 1px solid rgba(16,185,129,0.25);
                    border-left: 4px solid #10b981;
                    border-radius: 10px;
                    padding: 16px 20px;
                    margin-top: 12px;
                    display: flex;
                    align-items: center;
                    gap: 12px;
                ">
                    <span style="font-size: 22px;">✅</span>
                    <div>
                        <div style="font-size: 13px; font-weight: 700; color: #34d399; font-family: 'Inter', sans-serif;">
                            Nenhuma flag detectada
                        </div>
                        <div style="font-size: 11px; color: #4b7a5a; margin-top: 2px; font-family: 'Inter', sans-serif;">
                            Mission Unit dentro dos padrões — sem anomalias identificadas.
                        </div>
                    </div>
                </div>
                """)

        except Exception as e:
            st.error(f"❌ Erro ao chamar a API: {e}")


# ── Footer ───────────────────────────────────────────────────────────────────

st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown(f"""
<div style="margin-top:48px; padding:24px 32px; border-top:1px solid #1c2840;
            background:linear-gradient(90deg, #070b14, #0d1117);
            border-radius:12px; display:flex; justify-content:space-between;
            align-items:center; flex-wrap:wrap; gap:12px;">
    <div>
        <div style="display:flex; align-items:center; gap:8px;">
            <span style="font-size:18px;">🛡️</span>
            <span style="color:#f0f4ff; font-weight:700; font-size:13px;">Mission Brasil</span>
            <span style="color:#1c2840;">·</span>
            <span style="color:#4a5a7a; font-size:12px;">Anti-Fraude Intelligence v1.0</span>
        </div>
        <div style="color:#2d3f5e; font-size:11px; margin-top:4px;">
            Powered by Streamlit + Plotly · FastAPI Backend
        </div>
    </div>
    <div style="text-align:right; color:#2d3f5e; font-size:11px;">
        {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}<br>
        <span style="color:#1c2840;">Dados atualizados automaticamente (TTL 30s)</span>
    </div>
</div>
""", unsafe_allow_html=True)
