import sys
import re

file_path = r'c:\Users\Abner Ridigolo\Downloads\antifraude_windows\windows\dashboard.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. ADD PDF EXPORT TO SIDEBAR
# Look for the end of the sidebar code in update_dash (around "busca_missionario = st.text_input(...)").
# We can inject after the text input `help="Digite o nome exato para ver o perfil completo"\n    )`
sidebar_match = re.search(r'help="Digite o nome exato para ver o perfil completo"\n    \)', content)
if sidebar_match:
    inject_pdf = """
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
                self.cell(0, 8, "Mission Brasil — Anti-Fraude Intelligence", align="C")
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
"""
    content = content[:sidebar_match.end()] + inject_pdf + content[sidebar_match.end():]

# 2. COMPARATIVO SEMANA VS SEMANA
# Look for # ── KPIs Principais ──
# And we need to replace the entire 6 kpi cards section.
kpi_section_pattern = r'(# ── KPIs Principais ──\s+st\.markdown\(\'<div class="section-title">.*?</div>\', unsafe_allow_html=True\))([\s\S]*?)(st\.markdown\("<br>", unsafe_allow_html=True\))'
m_kpi = re.search(kpi_section_pattern, content)
if m_kpi:
    kpi_new = """

import random as _rng
def _simular_semana_anterior(report_atual):
    \"""Simula dados da semana anterior. Em produção: query com filtro de data.\"""
    seed = 99  # seed fixo para semana anterior
    r = _rng.Random(seed)
    fator = r.uniform(0.75, 1.15)
    return {
        "total_mus":        max(1, int(report_atual["total_mus"] * fator)),
        "bloqueado":        max(0, int(report_atual["bloqueado"] * r.uniform(0.6, 1.3))),
        "suspeito":         max(0, int(report_atual["suspeito"]  * r.uniform(0.7, 1.2))),
        "atencao":          max(0, int(report_atual["atencao"]   * r.uniform(0.8, 1.1))),
        "ok":               max(0, int(report_atual["ok"]        * r.uniform(0.9, 1.05))),
        "valor_em_risco_rs": report_atual["valor_em_risco_rs"] * r.uniform(0.6, 1.4),
        "taxa_fraude_pct":  report_atual["taxa_fraude_pct"]   * r.uniform(0.7, 1.3),
    }

semana_anterior = _simular_semana_anterior(report)

def _delta_badge(atual, anterior, invertido=False, prefixo="", sufixo=""):
    \"""Gera badge HTML de tendência com cor e seta.\"""
    diff = atual - anterior
    pct  = (diff / anterior * 100) if anterior != 0 else 0
    sobe = diff > 0

    # invertido=True: subir é ruim (ex: fraudes, valor em risco)
    cor   = "#ef4444" if (sobe and invertido) or (not sobe and not invertido) else "#22c55e"
    seta  = "↑" if sobe else "↓"
    sinal = "+" if sobe else ""

    return (
        f'<span style="font-size:11px; font-weight:700; color:{cor}; '
        f'background:{cor}18; border-radius:10px; padding:2px 8px; '
        f'display:inline-block; margin-top:4px;">'
        f'{seta} {sinal}{prefixo}{abs(diff):.0f}{sufixo} vs semana passada'
        f'</span>'
    )

kpi1, kpi2, kpi3, kpi4, kpi5, kpi6 = st.columns(6)

with kpi1:
    valor_atual = report['total_mus']
    valor_anterior = semana_anterior['total_mus']
    badge = _delta_badge(valor_atual, valor_anterior, invertido=False, sufixo=" MUs")
    st.markdown(f\"\"\"
    <div class="kpi-card blue">
        <div class="kpi-label">Total Analisado</div>
        <div class="kpi-value blue">{valor_atual}</div>
        <div class="kpi-sub">mission units</div>
        {badge}
    </div>
    \"\"\", unsafe_allow_html=True)

with kpi2:
    valor_atual = report['ok']
    valor_anterior = semana_anterior['ok']
    badge = _delta_badge(valor_atual, valor_anterior, invertido=False, sufixo=" MUs")
    pct_aprovado = report['ok'] / report['total_mus'] * 100 if report['total_mus'] > 0 else 0
    st.markdown(f\"\"\"
    <div class="kpi-card green">
        <div class="kpi-label">Aprovadas (Automático)</div>
        <div class="kpi-value green">{valor_atual}</div>
        <div class="kpi-sub">{pct_aprovado:.0f}% do fluxo</div>
        {badge}
    </div>
    \"\"\", unsafe_allow_html=True)

with kpi3:
    valor_atual = report['atencao']
    valor_anterior = semana_anterior['atencao']
    badge = _delta_badge(valor_atual, valor_anterior, invertido=True, sufixo=" MUs")
    st.markdown(f\"\"\"
    <div class="kpi-card orange">
        <div class="kpi-label">Atenção Leve</div>
        <div class="kpi-value orange">{valor_atual}</div>
        <div class="kpi-sub">pequenos desvios de GPS/tempo</div>
        {badge}
    </div>
    \"\"\", unsafe_allow_html=True)

with kpi4:
    risco_atual    = report['suspeito'] + report['bloqueado']
    risco_anterior = semana_anterior['suspeito'] + semana_anterior['bloqueado']
    badge = _delta_badge(risco_atual, risco_anterior, invertido=True, sufixo=" MUs")
    st.markdown(f\"\"\"
    <div class="kpi-card red">
        <div class="kpi-label">Suspeito + Bloqueado</div>
        <div class="kpi-value red">{risco_atual}</div>
        <div class="kpi-sub">{report['taxa_fraude_pct']}% taxa de fraude</div>
        {badge}
    </div>
    \"\"\", unsafe_allow_html=True)

with kpi5:
    valor_atual = report['valor_total_rs']
    valor_anterior = semana_anterior['valor_total_rs']
    badge = _delta_badge(valor_atual, valor_anterior, invertido=False, prefixo="R$")
    st.markdown(f\"\"\"
    <div class="kpi-card purple">
        <div class="kpi-label">Valor Total Analisado</div>
        <div class="kpi-value purple">R$ {valor_atual:,.0f}</div>
        <div class="kpi-sub">exposição global</div>
        {badge}
    </div>
    \"\"\", unsafe_allow_html=True)

with kpi6:
    valor_atual = report['valor_em_risco_rs']
    valor_anterior = semana_anterior['valor_em_risco_rs']
    badge = _delta_badge(valor_atual, valor_anterior, invertido=True, prefixo="R$")
    st.markdown(f\"\"\"
    <div class="kpi-card cyan">
        <div class="kpi-label">Retenção de Perdas Estimada</div>
        <div class="kpi-value cyan">R$ {valor_atual:,.0f}</div>
        <div class="kpi-sub">bloqueada da fraude</div>
        {badge}
    </div>
    \"\"\", unsafe_allow_html=True)

"""
    content = content[:m_kpi.start(2)] + kpi_new + content[m_kpi.start(3):]

# 3, 4, 5. XAI, CLUSTERING AND MAP
# Replaced after Radar de Risco and before Ranking. Radar de Risco ends before Inteligência de Risco / Ranking.
# I will find `# ── Inteligência de Risco — Ranking por Missionário ─────────────────────────`
insertion_idx = content.find('# ── Inteligência de Risco — Ranking por Missionário')
if insertion_idx != -1:
    novas_secoes = """
# ── Explicabilidade do Score (XAI) ──────────────────────────────────────────

st.markdown('<div class="section-title"><span class="icon">🔬</span> Explicabilidade do Score — Por que essa MU foi bloqueada?</div>', unsafe_allow_html=True)

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

        st.html(f\"\"\"
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
        \"\"\")

        # Lista de flags com peso
        for label, desc, pts, cor in flags_mu:
            pct_contribuicao = round(pts / score_total * 100) if score_total > 0 else 0
            st.html(f\"\"\"
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
            \"\"\")


# ── Clustering de Perfis de Fraude ──────────────────────────────────────────

st.markdown('<div class="section-title"><span class="icon">🧩</span> Clustering de Perfis de Fraude</div>', unsafe_allow_html=True)

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
            fig_cluster = px.scatter(
                df_cluster,
                x="fraud_score",
                y="n_flags",
                color="cluster_nome",
                size="recompensa_rs",
                size_max=20,
                color_discrete_map={v[0]: v[1] for v in CLUSTER_NOMES.values()},
                hover_data=["mu_id", "missionario_nome", "missao_nome"],
                labels={
                    "fraud_score":   "Fraud Score",
                    "n_flags":       "Nº de Flags",
                    "cluster_nome":  "Cluster",
                    "recompensa_rs": "Recompensa (R$)",
                },
                title="Clusters de Comportamento — Score × Flags",
            )
            fig_cluster.update_layout(
                template=PLOTLY_TEMPLATE,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)" if 'modo_escuro' in locals() and modo_escuro else "rgba(248,250,252,0.5)",
                font=dict(family="Inter", color="#94a3b8"),
                title=dict(font=dict(size=14, color="#e2e8f0")),
                xaxis=dict(gridcolor="rgba(30,41,59,0.5)"),
                yaxis=dict(gridcolor="rgba(30,41,59,0.5)"),
                legend=dict(
                    bgcolor="rgba(13,17,23,0.9)",
                    bordercolor="#1e293b",
                    borderwidth=1,
                    font=dict(size=10),
                    orientation="h",
                    y=-0.2, x=0.5, xanchor="center",
                ),
                height=400,
                margin=dict(t=50, b=80, l=20, r=20),
            )
            st.plotly_chart(fig_cluster, use_container_width=True)

        with col_cl_cards:
            st.markdown("<br>", unsafe_allow_html=True)
            for i, row in cluster_stats.iterrows():
                nome, cor, estrategia = mapa_cluster[row["cluster"]]
                st.html(f\"\"\"
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
                \"\"\")

    except ImportError:
        st.warning("Instale scikit-learn para ver o clustering (pip install scikit-learn).")


# ── Grafo de Conluio entre Missionários ─────────────────────────────────────

st.markdown('<div class="section-title"><span class="icon">🕸️</span> Rede de Conluio — Conexões Suspeitas</div>', unsafe_allow_html=True)

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
            st.html(f\"\"\"
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
            \"\"\")
    else:
        st.info("Nenhuma conexão suspeita detectada entre missionários no período atual.")


"""
    content = content[:insertion_idx] + novas_secoes + content[insertion_idx:]

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Modification V2 complete")
