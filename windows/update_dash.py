import sys

file_path = r'c:\Users\Abner Ridigolo\Downloads\antifraude_windows\windows\dashboard.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. ADD TEMA, TOGGLE AND BUSCA MISSIONARIO TO SIDEBAR
# Find where the sidebar starts or where "Atualizar Dados" ends.
# I will find "Atualizar Dados" first. Let's look for "Atualizar"
import re

# Look for sidebar context
sidebar_match = re.search(r'st\.sidebar\.(?:.*?)(?:Atualizar|Carregando).*?\n', content, re.IGNORECASE)
if not sidebar_match:
    # If not found, let's look for `with st.sidebar:`
    sidebar_match = re.search(r'with st\.sidebar:(.*?)(\n[^\s#])', content, re.DOTALL)

# Let's inject after the last import
import_end_idx = content.find('# ── Configuração da página ───────────────────────────────────────────────────')
if import_end_idx != -1:
    content = content[:import_end_idx] + """
# ── Configuração da página ───────────────────────────────────────────────────
""" + content[import_end_idx + len('# ── Configuração da página ───────────────────────────────────────────────────'):].lstrip('\n')

# We can just define the toggle and TEMA right after st.set_page_config
page_conf_end_m = re.search(r'st\.set_page_config\([^)]+\)', content, re.DOTALL)
if page_conf_end_m:
    inject_point = page_conf_end_m.end()
    
    inject_code = """

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
"""
    content = content[:inject_point] + inject_code + content[inject_point:]

# 2. UPDATE CSS WITH TEMA
# The prompt provides CSS replacements. 
# "st.markdown(f\"\"\"<style>..."
css_pattern = r'(st\.markdown\(\s*\"\"\"\s*<style>[\s\S]*?</style>\s*\"\"\",\s*unsafe_allow_html=True\))'
m_css = re.search(css_pattern, content)
if m_css:
    old_css = m_css.group(1)
    # The prompt actually requested replacing only a few top rules and keeping the rest.
    # It's cleaner to rewrite the python script header style string to `f"""` and modify the first few classes.
    # But since the user wants the exact code:
    
    # We'll just replace the start of the CSS string: `"""\n<style>\n` with `f"""\n<style>\n`
    new_css = old_css.replace('st.markdown("""\n<style>', 'st.markdown(f"""\n<style>\n    .stApp,\n    [data-testid="stAppViewContainer"] {{\n        background-color: {TEMA[\'bg_primary\']} !important;\n    }}\n    .main, [data-testid="stMainBlockContainer"] {{\n        background-color: {TEMA[\'bg_primary\']} !important;\n    }}\n    .stMarkdown, .stMarkdown p, label,\n    [data-testid="stWidgetLabel"] p {{\n        color: {TEMA[\'text_sec\']} !important;\n    }}\n    h1, h2, h3, h4 {{\n        color: {TEMA[\'text_pri\']} !important;\n    }}\n    .kpi-card {{\n        background: {TEMA[\'bg_card\']} !important;\n        border-color: {TEMA[\'border\']} !important;\n    }}\n    .kpi-label {{ color: {TEMA[\'text_sec\']} !important; }}\n    .kpi-sub   {{ color: {TEMA[\'text_mute\']} !important; }}\n    .section-title {{ color: {TEMA[\'text_pri\']} !important; border-color: {TEMA[\'border\']} !important; }}')
    
    # Need to replace single `{` with `{{` in the REST of the CSS since it's now an f-string!
    # Let me do string manipulation.
    # Actually, it's easier to just do:
    pass


# Since f-strings in python hate bare `{` in CSS, making the entire CSS an f-string might require escaping every `{` in hundreds of lines of CSS.
# A much better approach: Just split the CSS injection into TWO blocks.
# Block 1: The dynamic TEMA css
# Block 2: The static CSS
# Let's insert the dynamic CSS just before the static CSS.
dynamic_css = """
st.markdown(f\"\"\"
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
\"\"\", unsafe_allow_html=True)
"""
css_start = content.find('st.markdown("""\n<style>')
if css_start != -1:
    content = content[:css_start] + dynamic_css + content[css_start:]


# 3. MODO DETALHE DE MISSIONARIO
# Replaces PLOTLY_TEMPLATE
content = content.replace('PLOTLY_TEMPLATE = "plotly_dark"', '')

# Find exactly where df_mus is populated.
# Look for: if "df_mus" in st.session_state:
# Wait, the user said "Logo após o carregamento dos dados (all_mus, df_mus), adicione:"
# Let's string search for # ── KPIs Principais
kpi_idx = content.find('# ── KPIs Principais')
if kpi_idx != -1:
    detalhe_code = """
# ── Modo Detalhe de Missionário ──────────────────────────────────────────────
if busca_missionario and not df_mus.empty:

    df_miss = df_mus[
        df_mus["missionario_nome"].str.contains(busca_missionario, case=False, na=False)
    ]

    if df_miss.empty:
        st.warning(f"Nenhum missionário encontrado com o nome '{busca_missionario}'.")
        st.stop()

    nome = df_miss.iloc[0]["missionario_nome"]
    total_mus   = len(df_miss)
    score_medio = df_miss["fraud_score"].mean()
    score_max   = df_miss["fraud_score"].max()
    total_flags = df_miss["n_flags"].sum()
    valor_total = df_miss["recompensa_rs"].sum()
    pct_risco   = len(df_miss[df_miss["fraud_nivel"].isin(["suspeito","bloqueado"])]) / total_mus * 100

    # Score acumulado (mesma fórmula da melhoria 2)
    score_acum = min(100, round(
        score_medio * 0.4 + score_max * 0.4 +
        min(20, total_flags / max(total_mus, 1) * 10), 1
    ))

    if score_acum <= 20:   perfil, cor_perfil = "✅ Confiável",     "#22c55e"
    elif score_acum <= 45: perfil, cor_perfil = "⚠️ Monitorar",     "#f59e0b"
    elif score_acum <= 70: perfil, cor_perfil = "🔶 Alto Risco",    "#f97316"
    else:                  perfil, cor_perfil = "🚫 Perfil Crítico","#ef4444"

    # ── Header do perfil ──
    st.html(f\"\"\"
    <div style="
        background: linear-gradient(135deg, #0f172a, #1e1b4b);
        border: 1px solid {cor_perfil}33;
        border-left: 5px solid {cor_perfil};
        border-radius: 16px;
        padding: 28px 32px;
        margin-bottom: 24px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 20px;
    ">
        <div>
            <div style="font-size:11px; color:#3b82f6; font-weight:700;
                        letter-spacing:2px; text-transform:uppercase; margin-bottom:6px;">
                Perfil de Missionário
            </div>
            <div style="font-size:28px; font-weight:800; color:#f1f5f9; margin-bottom:8px;">
                {nome}
            </div>
            <span style="
                background:{cor_perfil}22; color:{cor_perfil};
                border:1px solid {cor_perfil}44; border-radius:20px;
                padding:5px 16px; font-size:12px; font-weight:700;
            ">{perfil}</span>
        </div>
        <div style="text-align:right;">
            <div style="font-size:11px; color:#64748b; margin-bottom:4px;">Score Acumulado</div>
            <div style="font-size:56px; font-weight:800; color:{cor_perfil}; line-height:1;">
                {score_acum}
            </div>
            <div style="font-size:11px; color:#475569;">de 100 pontos</div>
        </div>
    </div>
    \"\"\")

    # ── KPIs do missionário ──
    c1, c2, c3, c4, c5 = st.columns(5)
    kpis_detalhe = [
        (c1, "📋 Missões",       str(total_mus),               "no histórico",          "blue"),
        (c2, "📊 Score Médio",   f"{score_medio:.1f}",          "média das MUs",         "purple"),
        (c3, "🔝 Score Máximo",  f"{score_max:.1f}",            "pior missão",           "red"),
        (c4, "🚩 Flags Totais",  str(int(total_flags)),         "anomalias acumuladas",  "orange"),
        (c5, "💰 Valor Total",   f"R$ {valor_total:,.0f}",      "em recompensas",        "cyan"),
    ]
    for col, label, valor, sub, cor in kpis_detalhe:
        with col:
            st.markdown(f\"\"\"
            <div class="kpi-card {cor}">
                <div class="kpi-label">{label}</div>
                <div class="kpi-value {cor}">{valor}</div>
                <div class="kpi-sub">{sub}</div>
            </div>
            \"\"\", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Linha do tempo de missões ──
    col_hist_miss, col_dist_miss = st.columns([1.6, 1])

    with col_hist_miss:
        fig_hist_miss = px.bar(
            df_miss.sort_values("fraud_score", ascending=False),
            x="mu_id",
            y="fraud_score",
            color="fraud_nivel",
            color_discrete_map=CORES_NIVEL,
            labels={"mu_id": "Mission Unit", "fraud_score": "Score"},
            title=f"Histórico de Scores — {nome}",
            category_orders={"fraud_nivel": ["ok","atencao","suspeito","bloqueado"]},
        )
        fig_hist_miss.add_hline(y=45, line_dash="dash", line_color="#f59e0b",
                                 opacity=0.5, annotation_text="Threshold Atenção")
        fig_hist_miss.add_hline(y=70, line_dash="dash", line_color="#ef4444",
                                 opacity=0.5, annotation_text="Threshold Risco")
        fig_hist_miss.update_layout(
            template=PLOTLY_TEMPLATE,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)" if modo_escuro else "rgba(248,250,252,0.5)",
            font=dict(family="Inter", color="#94a3b8"),
            title=dict(font=dict(size=14, color="#e2e8f0")),
            xaxis=dict(tickangle=-30, gridcolor="rgba(30,41,59,0.5)"),
            yaxis=dict(range=[0,105], gridcolor="rgba(30,41,59,0.5)"),
            showlegend=False,
            height=320,
            margin=dict(t=50, b=60, l=20, r=20),
        )
        st.plotly_chart(fig_hist_miss, use_container_width=True)

    with col_dist_miss:
        dist_niveis = df_miss["fraud_nivel"].value_counts().reset_index()
        dist_niveis.columns = ["nivel","count"]
        fig_pie_miss = px.pie(
            dist_niveis, names="nivel", values="count", hole=0.55,
            color="nivel",
            color_discrete_map=CORES_NIVEL,
            title="Distribuição por Risco",
        )
        fig_pie_miss.update_layout(
            template=PLOTLY_TEMPLATE,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)" if modo_escuro else "rgba(248,250,252,0.5)",
            font=dict(family="Inter", color="#94a3b8"),
            title=dict(font=dict(size=14, color="#e2e8f0")),
            showlegend=True,
            legend=dict(orientation="h", y=-0.15, x=0.5, xanchor="center", font=dict(size=10)),
            height=320,
            margin=dict(t=50, b=60, l=20, r=20),
        )
        st.plotly_chart(fig_pie_miss, use_container_width=True)

    # ── Tabela de MUs do missionário ──
    st.markdown(f'<div class="section-title"><span class="icon">📋</span> Todas as Mission Units — {nome}</div>',
                unsafe_allow_html=True)

    html_rows_miss = ""
    for _, row in df_miss.sort_values("fraud_score", ascending=False).iterrows():
        nivel = row["fraud_nivel"]
        score = row["fraud_score"]
        cor_score = CORES_NIVEL.get(nivel, "#94a3b8")
        html_rows_miss += f\"\"\"
        <tr>
            <td style="color:#60a5fa; font-weight:600; font-family:monospace;">{row['mu_id']}</td>
            <td>{row['missao_nome']}</td>
            <td style="text-align:right; color:#a78bfa; font-weight:600;">R$ {row['recompensa_rs']:,.0f}</td>
            <td style="color:{cor_score}; font-weight:700; font-family:monospace;">{score}</td>
            <td><span class="badge badge-{nivel}">{LABELS_NIVEL.get(nivel, nivel)}</span></td>
            <td style="text-align:center; color:#f87171; font-weight:600;">{row['n_flags']}</td>
            <td style="color:#64748b; font-size:11px;">{row['status']}</td>
        </tr>
        \"\"\"

    st.html(f\"\"\"
    <div style="overflow-x:auto; border-radius:12px; border:1px solid #1e293b; background:#0a0e1a;">
    <table style="width:100%; border-collapse:collapse; font-family:'Inter',sans-serif; font-size:13px;">
        <thead>
            <tr style="background:linear-gradient(135deg,#1e1b4b,#1e293b); border-bottom:2px solid #312e81;">
                <th style="padding:12px 16px; text-align:left;  color:#a5b4fc; font-size:10px; text-transform:uppercase; letter-spacing:1px;">MU ID</th>
                <th style="padding:12px 16px; text-align:left;  color:#a5b4fc; font-size:10px; text-transform:uppercase; letter-spacing:1px;">Missão</th>
                <th style="padding:12px 16px; text-align:right; color:#a5b4fc; font-size:10px; text-transform:uppercase; letter-spacing:1px;">Valor</th>
                <th style="padding:12px 16px; text-align:left;  color:#a5b4fc; font-size:10px; text-transform:uppercase; letter-spacing:1px;">Score</th>
                <th style="padding:12px 16px; text-align:left;  color:#a5b4fc; font-size:10px; text-transform:uppercase; letter-spacing:1px;">Nível</th>
                <th style="padding:12px 16px; text-align:center;color:#a5b4fc; font-size:10px; text-transform:uppercase; letter-spacing:1px;">Flags</th>
                <th style="padding:12px 16px; text-align:left;  color:#a5b4fc; font-size:10px; text-transform:uppercase; letter-spacing:1px;">Status</th>
            </tr>
        </thead>
        <tbody>{html_rows_miss}</tbody>
    </table>
    </div>
    \"\"\")

    # Botão para voltar ao dashboard principal
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("← Voltar ao Dashboard", type="secondary"):
        st.rerun()

    st.stop()  # Não renderiza o resto do dashboard quando em modo detalhe

# ── FIM MODO DETALHE ─────────────────────────────────────────────────────────

"""
    content = content[:kpi_idx] + detalhe_code + content[kpi_idx:]


# 4. RANKING
ranking_code = """
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
        st.markdown(f\"\"\"
        <div class="kpi-card red" style="margin-bottom:12px;">
            <div class="kpi-label">🚫 Perfis Críticos</div>
            <div class="kpi-value red">{perfis_criticos}</div>
            <div class="kpi-sub">missionários com score > 70</div>
        </div>
        \"\"\", unsafe_allow_html=True)

        # Card 2 — Reincidentes
        st.markdown(f\"\"\"
        <div class="kpi-card orange" style="margin-bottom:12px;">
            <div class="kpi-label">🔁 Reincidentes</div>
            <div class="kpi-value orange">{reincidentes}</div>
            <div class="kpi-sub">com 2+ missões no histórico</div>
        </div>
        \"\"\", unsafe_allow_html=True)

        # Card 3 — Valor exposto
        st.markdown(f\"\"\"
        <div class="kpi-card purple">
            <div class="kpi-label">💸 Exposição Acumulada</div>
            <div class="kpi-value purple">R$ {valor_risco_acum:,.0f}</div>
            <div class="kpi-sub">recompensas em perfis de alto risco</div>
        </div>
        \"\"\", unsafe_allow_html=True)

"""

critica_idx = content.find('# ── Tabela: MUs Críticas')
if critica_idx != -1:
    content = content[:critica_idx] + ranking_code + content[critica_idx:]

# 5. REPLACE plot_bgcolor
# Replace globally `plot_bgcolor="rgba(0,0,0,0)",` with `plot_bgcolor="rgba(0,0,0,0)" if modo_escuro else "rgba(248,250,252,0.5)",`
# To avoid double escaping:
content = content.replace('plot_bgcolor="rgba(0,0,0,0)",', 'plot_bgcolor="rgba(0,0,0,0)" if modo_escuro else "rgba(248,250,252,0.5)",')

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Modification complete")
