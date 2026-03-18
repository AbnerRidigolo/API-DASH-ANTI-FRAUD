"""
integration_test.py — Prova end-to-end do fluxo Mission Brasil
Simula exatamente o que vai acontecer quando a API original estiver pronta:

  API Mission → webhook → fraud engine → POST approve/reject → API Mission

Roda contra a API local (mock) e valida que o resultado correto é devolvido.
Quando a API real ligar: ajuste BASE_URL e as asserções continuam valendo.

Uso:
  # Com servidor rodando (uvicorn app:app --port 8000):
  python integration_test.py
"""

import json
import time
import urllib.request
import urllib.error
from datetime import datetime

BASE_URL = "http://localhost:8000"

VERDE  = "\033[92m"
AMARELO = "\033[93m"
VERMELHO = "\033[91m"
RESET  = "\033[0m"
NEGRITO = "\033[1m"


def req(method, path, body=None):
    url = BASE_URL + path
    data = json.dumps(body).encode() if body else None
    headers = {"Content-Type": "application/json"} if data else {}
    r = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(r, timeout=10) as resp:
        return json.loads(resp.read())


def sep(titulo=""):
    linha = "═" * 60
    if titulo:
        print(f"\n{NEGRITO}{linha}{RESET}")
        print(f"{NEGRITO}  {titulo}{RESET}")
        print(f"{NEGRITO}{linha}{RESET}")
    else:
        print(f"  {'─'*56}")


def ok(msg):  print(f"  {VERDE}✅  {msg}{RESET}")
def warn(msg): print(f"  {AMARELO}⚠️   {msg}{RESET}")
def err(msg):  print(f"  {VERMELHO}❌  {msg}{RESET}")
def info(msg): print(f"      {msg}")


# ── Cenários de teste ────────────────────────────────────────────────────────

CENARIOS = [
    {
        "nome": "MU legítima — deve ser APROVADA",
        "esperado_nivel": "ok",
        "esperado_acao": "Aprovar automaticamente.",
        "mu": {
            "mu_id": "MU-LEGIT-001",
            "status": "Validando Dados",
            "missao": {
                "id": "MB-1003412",
                "nome": "Repositor de Gôndola | 6h",
                "descricao": "Reposição de produtos nas gôndolas.",
                "duracao_esperada_horas": 6,
                "criado_em": "2026-03-17T07:00:00",
                "recompensa": {"dinheiro": 90.0, "pontos": 0},
                "assinatura": "FREE",
            },
            "missionario": {
                "id": "USR-LEGIT-001",
                "nome": "Fernanda Lima Santos",
                "historico_missoes": 42,
                "historico_reprovacoes": 1,
            },
            "localizacao": {"endereco": "Av. Paulista, 1374 - SP", "lat": -23.5631, "lng": -46.6544},
            "atividades": [
                {"tipo": "check_in",  "timestamp": "2026-03-17T08:00:00", "lat": -23.5633, "lng": -46.6547},
                {"tipo": "check_out", "timestamp": "2026-03-17T14:05:00", "lat": -23.5633, "lng": -46.6547},
                {"tipo": "iniciou",   "timestamp": "2026-03-17T08:02:00", "lat": -23.5633, "lng": -46.6547},
                {"tipo": "finalizou", "timestamp": "2026-03-17T14:03:00", "lat": -23.5633, "lng": -46.6547},
            ],
        },
    },
    {
        "nome": "Check-in antes da criação + duração zero — BLOQUEADA (caso real Aline)",
        "esperado_nivel": "bloqueado",
        "esperado_acao": "Bloquear pagamento e notificar compliance imediatamente.",
        "mu": {
            "mu_id": "MU-1442951",
            "status": "Validando Dados",
            "missao": {
                "id": "MB-1009259",
                "nome": "Hostess | Turnos de 8h",
                "descricao": "Realizar ação ESPECIALISTA DENGO. Atendimento ao cliente.",
                "duracao_esperada_horas": 8,
                "criado_em": "2026-03-17T09:03:00",
                "recompensa": {"dinheiro": 140.0, "pontos": 0},
                "assinatura": "FREE",
            },
            "missionario": {
                "id": "USR-1442951",
                "nome": "Aline da Silva Elias",
                "historico_missoes": 12,
                "historico_reprovacoes": 1,
            },
            "localizacao": {
                "endereco": "Av. Brig. Faria Lima, 2232 - Jardim Paulistano, SP",
                "lat": -23.5718, "lng": -46.6858,
            },
            "atividades": [
                {"tipo": "check_in",  "timestamp": "2026-03-16T14:00:00", "lat": -23.5718, "lng": -46.6858},
                {"tipo": "check_out", "timestamp": "2026-03-16T22:00:00", "lat": -23.5718, "lng": -46.6858},
                {"tipo": "iniciou",   "timestamp": "2026-03-17T09:27:00", "lat": -23.5718, "lng": -46.6858},
                {"tipo": "finalizou", "timestamp": "2026-03-17T09:27:00", "lat": -23.5718, "lng": -46.6858},
            ],
        },
    },
    {
        "nome": "Ghost worker — GPS 15km do local — SUSPEITA",
        "esperado_nivel": "suspeito",
        "esperado_acao": "Bloquear pagamento — enviar para análise manual.",
        "mu": {
            "mu_id": "MU-GHOST-001",
            "status": "Validando Dados",
            "missao": {
                "id": "MB-1007881",
                "nome": "Promotor iFood | 4h",
                "descricao": "Ação promocional iFood em supermercado.",
                "duracao_esperada_horas": 4,
                "criado_em": "2026-03-17T06:00:00",
                "recompensa": {"dinheiro": 80.0, "pontos": 0},
                "assinatura": "FREE",
            },
            "missionario": {
                "id": "USR-GHOST-001",
                "nome": "Roberto Alves Pereira",
                "historico_missoes": 8,
                "historico_reprovacoes": 3,
            },
            "localizacao": {
                "endereco": "Av. Santo Amaro, 3000 - Santo Amaro, SP",
                "lat": -23.6502, "lng": -46.6963,
            },
            "atividades": [
                # GPS completamente diferente do local esperado
                {"tipo": "check_in",  "timestamp": "2026-03-17T09:00:00", "lat": -23.5100, "lng": -46.6100},
                {"tipo": "check_out", "timestamp": "2026-03-17T13:10:00", "lat": -23.5100, "lng": -46.6100},
                {"tipo": "iniciou",   "timestamp": "2026-03-17T09:05:00", "lat": -23.5100, "lng": -46.6100},
                {"tipo": "finalizou", "timestamp": "2026-03-17T13:08:00", "lat": -23.5100, "lng": -46.6100},
            ],
        },
    },
    {
        "nome": "Checkout antecipado (ficou 30% do tempo) — ATENÇÃO",
        "esperado_nivel": "atencao",
        "esperado_acao": "Monitorar — enviar para fila de revisão leve.",
        "mu": {
            "mu_id": "MU-EARLY-001",
            "status": "Validando Dados",
            "missao": {
                "id": "MB-1011004",
                "nome": "Picking & Packing | Noturno 8h",
                "descricao": "Separação e embalagem de pedidos e-commerce.",
                "duracao_esperada_horas": 8,
                "criado_em": "2026-03-17T18:00:00",
                "recompensa": {"dinheiro": 160.0, "pontos": 0},
                "assinatura": "FREE",
            },
            "missionario": {
                "id": "USR-EARLY-001",
                "nome": "Diego Mendes Ramos",
                "historico_missoes": 20,
                "historico_reprovacoes": 2,
            },
            "localizacao": {
                "endereco": "Av. Vergueiro, 500 - Liberdade, SP",
                "lat": -23.5684, "lng": -46.6379,
            },
            "atividades": [
                {"tipo": "check_in",  "timestamp": "2026-03-17T20:00:00", "lat": -23.5684, "lng": -46.6379},
                # Ficou só 2.4h de 8h esperadas (30%)
                {"tipo": "check_out", "timestamp": "2026-03-17T22:24:00", "lat": -23.5684, "lng": -46.6379},
                {"tipo": "iniciou",   "timestamp": "2026-03-17T20:02:00", "lat": -23.5684, "lng": -46.6379},
                {"tipo": "finalizou", "timestamp": "2026-03-17T22:20:00", "lat": -23.5684, "lng": -46.6379},
            ],
        },
    },
]

# ── Simulação do fluxo com a API Mission real ────────────────────────────────

def simular_webhook_e_decisao(mu_data: dict) -> dict:
    """
    Simula o fluxo completo que vai acontecer em produção:
    1. API Mission dispara webhook mu.finalized
    2. Nossa API recebe o evento
    3. Roda análise de fraude
    4. Devolve decisão (approve/reject) para a API Mission
    """
    # Passo 1 — receber webhook de finalização
    webhook_payload = {
        "event_type": "mu.finalized",
        "mu_id": mu_data["mu_id"],
        "timestamp": datetime.now().isoformat(),
        "payload": {"status": "Validando Dados"},
    }
    webhook_resp = req("POST", "/webhook", webhook_payload)
    assert webhook_resp["received"] is True

    # Passo 2 — analisar a MU
    analise = req("POST", "/analyze", mu_data)

    # Passo 3 — decisão que seria enviada de volta à API Mission
    decisao = {
        "mu_id": analise["mu_id"],
        "acao": "APROVAR" if analise["fraud_nivel"] == "ok" else "REPROVAR",
        "motivo": analise["recomendacao"],
        "fraud_score": analise["fraud_score"],
        "fraud_nivel": analise["fraud_nivel"],
        "flags": [f["regra"] for f in analise["flags"]],
    }

    return {"analise": analise, "decisao": decisao}


# ── Runner ────────────────────────────────────────────────────────────────────

def rodar():
    sep("Mission Brasil — Teste de Integração End-to-End")
    print(f"  Servidor : {BASE_URL}")
    print(f"  Data     : {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"\n  Fluxo testado:")
    print(f"  API Mission → webhook → fraud engine → approve/reject → API Mission\n")

    resultados = []

    for i, cenario in enumerate(CENARIOS, 1):
        sep(f"Cenário {i}: {cenario['nome']}")
        try:
            r = simular_webhook_e_decisao(cenario["mu"])
            analise = r["analise"]
            decisao = r["decisao"]

            nivel_correto = analise["fraud_nivel"] == cenario["esperado_nivel"]
            acao_correta  = analise["recomendacao"] == cenario["esperado_acao"]
            passou = nivel_correto and acao_correta

            # Score e nível
            cor = VERDE if passou else VERMELHO
            print(f"  {cor}{'✅' if passou else '❌'}  fraud_score  : {analise['fraud_score']}{RESET}")
            print(f"      fraud_nivel  : {analise['fraud_nivel']}  (esperado: {cenario['esperado_nivel']})")

            # Flags detectadas
            if analise["flags"]:
                print(f"      flags ({len(analise['flags'])})   :")
                for f in analise["flags"]:
                    print(f"        • [{f['pontos']:>5.1f}pts] {f['descricao']}")
            else:
                print(f"      flags        : nenhuma")

            # Decisão final
            cor_acao = VERDE if decisao["acao"] == "APROVAR" else VERMELHO
            print(f"\n  {NEGRITO}DECISÃO ENVIADA À API MISSION:{RESET}")
            print(f"  {cor_acao}{NEGRITO}  ➤  {decisao['acao']}{RESET}")
            print(f"      Motivo: {decisao['motivo']}")

            resultados.append(passou)

        except urllib.error.URLError:
            err("Servidor não está rodando! Suba: uvicorn app:app --port 8000")
            return
        except Exception as e:
            err(f"Erro inesperado: {e}")
            resultados.append(False)

    # ── Resumo ────────────────────────────────────────────────────────────────
    sep("Resultado Final")
    passou_todos = sum(resultados)
    total        = len(resultados)
    tudo_ok      = passou_todos == total

    for i, (cenario, passou) in enumerate(zip(CENARIOS, resultados), 1):
        status = f"{VERDE}✅ PASSOU{RESET}" if passou else f"{VERMELHO}❌ FALHOU{RESET}"
        print(f"  {status}  Cenário {i}: {cenario['nome'][:45]}")

    print()
    if tudo_ok:
        print(f"  {VERDE}{NEGRITO}🎉  {passou_todos}/{total} cenários passaram{RESET}")
        print(f"\n  {NEGRITO}Quando a API Mission estiver pronta:{RESET}")
        print(f"  1. Edite .env → MOCK_MODE=false")
        print(f"  2. Adicione MISSION_API_URL e MISSION_API_KEY")
        print(f"  3. Rode este teste novamente — os cenários continuam valendo")
    else:
        print(f"  {VERMELHO}{NEGRITO}⚠️   {passou_todos}/{total} cenários passaram — verifique os falhos acima{RESET}")

    print(f"\n{'═'*60}\n")


if __name__ == "__main__":
    rodar()
