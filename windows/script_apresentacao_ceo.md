# Roteiro de Apresentação Executiva: SENTINEL Anti-Fraude v3

**Público-Target:** CEO e Diretoria Executiva
**Objetivo:** Demonstrar como a nova camada de inteligência protege a margem da operação e garante a escalabilidade do Mission Brasil.

---

## 1. Abertura: O Problema e a Oportunidade (2 min)
*   **Gancho:** "Hoje, conforme o Mission Brasil cresce, o risco de fraudes operacionais escala na mesma proporção. Sem automação, perdemos dinheiro em 'ghost workers' e pagamentos indevidos."
*   **O Desafio:** Identificar padrões sutis que a análise humana não consegue pegar em tempo real (ex: check-ins retroativos ou GPS manipulado).
*   **A Promessa:** Apresentamos o **SENTINEL**, nosso motor de análise em tempo real que atua como um filtro invisível entre a execução da missão e o fechamento financeiro.

---

## 2. A Engenharia: A API Anti-Fraude (3 min)
*   *Mostrar a documentação técnica (Swagger) para passar confiança na robustez.*
*   **O que ela faz:** "Nossa API analisa cada Mission Unit (MU) individualmente através de 7 regras de ouro automáticas."
*   **As Regras de Ouro:**
    1.  **GPS Geofencing:** Detecta se o missionário está realmente onde diz estar.
    2.  **Divergência de Percurso:** Verifica se o check-in e check-out ocorreram no mesmo local.
    3.  **Cronômetro de Execução:** Bloqueia missões finalizadas em tempo impossível (ex: uma missão de 8h feita em 10 segundos).
    4.  **Check-in Retroativo:** Pega tentativas de burlar o sistema criando registros antes da missão existir.
    5.  **Histórico Reputacional:** O motor 'aprende' com o comportamento passado do missionário.
*   **Automação de Decisões:** "Não apenas detectamos, recomentamos a ação: **Aprovação Automática**, **Revisão Leve** ou **Bloqueio de Pagamento**."

---

## 3. A Visão do Comandante: Dashboard Intelligence (5 min)
*   *Navegar pelo Dashboard focado nos KPIs coloridos.*
*   **Métricas de Valor (Tempo Real):** 
    *   **Volume Total vs. Valor em Risco:** Demonstração do capital isolado para análise preventiva.
    *   **Funil de Segurança:** Fluxo de missões OK vs. MUs em atenção/risco.
*   **Inteligência C-Level (O diferencial):**
    *   **ROI de Prevenção:** Cálculo de economia direta ao barrar fraudes (Valor Crítico * Precisão).
    *   **Análise de Cohort:** "Descobrimos se a fraude vem de usuários novos ou antigos, permitindo ajustes no Onboarding."
    *   **Drift Detector:** Monitoramento da saúde do modelo. Se o comportamento das fraudes mudar, o sistema aciona um alerta tático.

---

## 4. O Impacto Estratégico e Próximos Passos (2 min)
*   **Escalabilidade:** "Podemos processar milhares de missões por dia com o mesmo custo operacional."
*   **Confiança do Cliente:** "Garantia de que o centavo pago é por trabalho verificado por inteligência."
*   **Próximos Passos:** 
    1.  Integração total com o fluxo de pagamentos (Pay-only-if-verified).
    2.  Adoção de Bio-validação facial baseada no score de risco.

---

## 5. Walkthrough: Demonstração ao Vivo
1.  **Abra o Dashboard (http://localhost:8501).**
2.  **Destaque o indicador "API Conectada"** (Sinal de saúde do sistema).
3.  **Filtre por "Bloqueado"** no menu lateral para focar nos casos críticos.
4.  **Gere o Relatório PDF** para mostrar a capacidade de reporte executivo instantâneo.
5.  **Finalize mostrando a aba de ROI** para ancorar o valor financeiro da solução.

---

**Frase de Encerramento:** "O SENTINEL não é apenas segurança; é a garantia de que o Mission Brasil é o marketplace de trabalho mais eficiente e confiável do mercado."
