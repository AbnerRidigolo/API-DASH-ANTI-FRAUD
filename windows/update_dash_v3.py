import sys
import re

file_path = r'c:\Users\Abner Ridigolo\Downloads\antifraude_windows\windows\dashboard.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. REMOVE BOX PLOT
pattern_box = r'col_scatter,\s*col_box\s*=\s*st\.columns\(\[1\.5,\s*1\]\)\s*with\s*col_scatter:'
content = re.sub(pattern_box, 'if True:', content)

pattern_colbox_block = r'\s*with col_box:[\s\S]*?(?=# ── Explicabilidade do Score \(XAI\))'
# Wait! Instead of removing until XAI, we also want to remove Radar Chart!
# Let's find "with col_box" and remove up to "Explicabilidade do Score (XAI) ──────────────────────────────────────────"
# But wait, Radar chart was already injected earlier by me!
pattern_to_remove = r'    with col_box:.*?(?=# ── Explicabilidade do Score \(XAI\) ──────────────────────────────────────────)'
content = re.sub(pattern_to_remove, '\n\n', content, flags=re.DOTALL)


# 2. THRESHOLD CONTROL PANEL
# Inject before the charts section. 
# There is a section `# ── Análise Detalhada ──────────────────────────────────────────────────`
# Let's inject right below it.
analise_pattern = r'# ── Análise Detalhada ──────────────────────────────────────────────────\n\nst\.markdown\(\'<div class="section-title">.*?</div>\', unsafe_allow_html=True\)'
analise_match = re.search(analise_pattern, content)
if analise_match:
    panel_code = """
# ── Painel de Controle de Limiares (Backend Rules Mock) ──────────────────────
st.markdown('<div class="section-title"><span class="icon">⚙️</span> Controle de Parâmetros do Motor — Regras de Risco</div>', unsafe_allow_html=True)
with st.expander("Ajustes de Pesos de Regras no Backend", expanded=False):
    st.info("Estas alterações atualizariam a configuração dos limiares de bloqueio direto no banco de dados do motor de decisão da API (MOCK).")
    c_p1, c_p2, c_p3 = st.columns(3)
    c_p1.slider("Peso: Duração Abaixo de 2 min", 0, 100, 35)
    c_p1.slider("Peso: GPS Divergente (>300m)", 0, 100, 25)
    c_p2.slider("Limite Bloqueio Total (Score Máximo)", 0, 100, 70)
    c_p2.slider("Limite Atenção e Revisão", 0, 100, 45)
    c_p3.slider("Peso: Excesso de Flags de Pagamento", 0, 100, 15)
    
    col_btn1, col_btn2 = st.columns([1, 4])
    with col_btn1:
        if st.button("Gravar Novos Limiares"):
            st.success("Configuração atualizada! As próximas missões serão testadas com os novos parâmetros.")

"""
    content = content[:analise_match.end()] + '\n' + panel_code + content[analise_match.end():]


# 3. BULK ACTIONS IN CRITICAL MUs
# After # ── Tabela: MUs Críticas
# It ends with ` st.html(f"""...</table></div>""") `
tabela_pattern = r'            <td>{nivel_badge\(row\[\'fraud_nivel\'\]\)}</td>\n        </tr>\n        """\n\n    st\.html\(f"""[\s\S]*?</table>\n    </div>\n    """\)'
tabela_match = re.search(tabela_pattern, content)
if tabela_match:
    bulk_code = """

    # ── Ações em Lote (Bulk Actions) ─────────────────────────────────────────
    st.markdown("<br>### ⚡ Ações em Lote (Bulk Actions)", unsafe_allow_html=True)
    st.markdown("<span style='color:#64748b; font-size:12px;'>Execute resoluções para múltiplas Mission Units de uma só vez.</span>", unsafe_allow_html=True)
    
    col_sel, col_act1, col_act2 = st.columns([2, 1, 1])
    mu_list = df_criticas['mu_id'].tolist()
    
    selected_mus = col_sel.multiselect(
        "Selecionar MUs críticas para processar:", 
        mu_list, 
        default=[mu_list[0]] if mu_list else [],
        placeholder="Selecione as MUs"
    )
    
    if col_act1.button("✅ Aprovar (Override)", use_container_width=True):
        if selected_mus:
            st.success(f"{len(selected_mus)} MU(s) enviadas para soltura e liberação de pagamento!")
        else:
            st.warning("Selecione alguma MU.")
            
    if col_act2.button("🚫 Banir Missionários (Bulk)", use_container_width=True):
        if selected_mus:
            st.error(f"{len(selected_mus)} Missionário(s) banido(s) preventivamente da base!")
        else:
            st.warning("Selecione alguma MU.")
"""
    content = content[:tabela_match.end()] + bulk_code + content[tabela_match.end():]


# 4. SIMULATOR BACKTESTING
# Find `tab_cenarios, tab_missao, tab_perfil, tab_sandbox = st.tabs(...)`
tabs_pattern = r'(tab_cenarios,\s*tab_missao,\s*tab_perfil,\s*tab_sandbox\s*=\s*st\.tabs\(\s*\[)(.*?)(\]\s*\))'
content = re.sub(tabs_pattern, r'\1\2, "⏱️ Backtesting (Larga Escala)"\3', content)
content = content.replace('tab_cenarios, tab_missao, tab_perfil, tab_sandbox = st.tabs(', 'tab_cenarios, tab_missao, tab_perfil, tab_sandbox, tab_backtest = st.tabs(')

# Inject the backtest tab content before the execute button logic!
# Looking for `# --- Botão de Execução`
botao_exec_idx = content.find('# --- Botão de Execução')
if botao_exec_idx != -1:
    backtest_code = """
    with tab_backtest:
        st.markdown("#### 🔄 Simulação Retroativa de Parâmetros (Backtesting)")
        st.markdown("<span style='font-size:12px; color:#64748b;'>Teste limites de risco aplicando as novas políticas em MUs dos últimos 30 dias.</span>", unsafe_allow_html=True)
        
        sel_range = st.selectbox("Período de Base Histórica", ["Últimos 7 dias", "Últimos 15 dias", "Últimos 30 dias"])
        sel_rules = st.multiselect("Regras ativas no motor:", ["Bloquear GPS > 100m", "Reprovação se Score > 65", "Tolerância Zero para Velocidade"], default=["Reprovação se Score > 65"])
        
        if st.button("▶ Rodar Simulação de Backtesting", use_container_width=True):
            st.info("Simulando processamento em 12.450 MUs do histórico...")
            st.success("Backtesting Concluído! Resultado: 384 bloqueios a mais teriam acontecido. (Falso Positivo estimado em 18%).")
            
"""
    content = content[:botao_exec_idx] + backtest_code + content[botao_exec_idx:]


with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Modification V3 complete")
