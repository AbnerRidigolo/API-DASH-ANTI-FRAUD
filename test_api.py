"""
test_api.py — Testa os 4 endpoints da Anti-Fraud API
Rode DEPOIS de subir o servidor: uvicorn app:app --reload --port 8000

Uso:  python test_api.py
"""

import json
import urllib.request
import urllib.error

BASE = "http://localhost:8000"
PASS = "✅"
FAIL = "❌"


def req(method, path, body=None):
    url = BASE + path
    data = json.dumps(body).encode() if body else None
    headers = {"Content-Type": "application/json"} if data else {}
    r = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(r) as resp:
        return json.loads(resp.read())


def titulo(txt):
    print(f"\n{'─'*55}")
    print(f"  {txt}")
    print(f"{'─'*55}")


# ── MU do caso real (Aline — check-in antes da criação + duração zero) ────────
MU_REAL = {
    "mu_id": "MU-1442951",
    "status": "Validando Dados",
    "missao": {
        "id": "MB-1009259",
        "nome": "Hostess | Seg–Sáb | Turnos de 8h",
        "descricao": "Realizar ação de ESPECIALISTA DENGO. Atendimento ao cliente.",
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
        "lat": -23.5718,
        "lng": -46.6858,
    },
    "atividades": [
        {"tipo": "check_in",  "timestamp": "2026-03-16T14:00:00", "lat": -23.5718, "lng": -46.6858},
        {"tipo": "check_out", "timestamp": "2026-03-16T22:00:00", "lat": -23.5718, "lng": -46.6858},
        {"tipo": "iniciou",   "timestamp": "2026-03-17T09:27:00", "lat": -23.5718, "lng": -46.6858},
        {"tipo": "finalizou", "timestamp": "2026-03-17T09:27:00", "lat": -23.5718, "lng": -46.6858},
    ],
}

MU_NORMAL = {
    "mu_id": "MU-9999999",
    "status": "Aprovado",
    "missao": {
        "id": "MB-1003412",
        "nome": "Repositor de Gôndola | 6h",
        "descricao": "Reposição de produtos nas gôndolas. Check-in obrigatório.",
        "duracao_esperada_horas": 6,
        "criado_em": "2026-03-17T07:00:00",
        "recompensa": {"dinheiro": 90.0, "pontos": 0},
        "assinatura": "FREE",
    },
    "missionario": {
        "id": "USR-9999999",
        "nome": "Carlos Eduardo Moura",
        "historico_missoes": 35,
        "historico_reprovacoes": 1,
    },
    "localizacao": {
        "endereco": "Av. Paulista, 1374 - Bela Vista, SP",
        "lat": -23.5631,
        "lng": -46.6544,
    },
    "atividades": [
        {"tipo": "check_in",  "timestamp": "2026-03-17T08:00:00", "lat": -23.5633, "lng": -46.6547},
        {"tipo": "check_out", "timestamp": "2026-03-17T14:05:00", "lat": -23.5633, "lng": -46.6547},
        {"tipo": "iniciou",   "timestamp": "2026-03-17T08:02:00", "lat": -23.5633, "lng": -46.6547},
        {"tipo": "finalizou", "timestamp": "2026-03-17T14:03:00", "lat": -23.5633, "lng": -46.6547},
    ],
}

MU_GHOST = {
    "mu_id": "MU-8888888",
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
        "id": "USR-8888888",
        "nome": "Roberto Alves Pereira",
        "historico_missoes": 8,
        "historico_reprovacoes": 3,
    },
    "localizacao": {
        "endereco": "Av. Santo Amaro, 3000 - Santo Amaro, SP",
        "lat": -23.6502,
        "lng": -46.6963,
    },
    "atividades": [
        {"tipo": "check_in",  "timestamp": "2026-03-17T09:00:00", "lat": -23.5631, "lng": -46.6544},
        {"tipo": "check_out", "timestamp": "2026-03-17T13:10:00", "lat": -23.5631, "lng": -46.6544},
        {"tipo": "iniciou",   "timestamp": "2026-03-17T09:05:00", "lat": -23.5631, "lng": -46.6544},
        {"tipo": "finalizou", "timestamp": "2026-03-17T13:08:00", "lat": -23.5631, "lng": -46.6544},
    ],
}


def test_health():
    titulo("Teste 0 — Health check")
    r = req("GET", "/")
    ok = r.get("status") == "ok"
    print(f"  {PASS if ok else FAIL}  GET /  →  status={r.get('status')}")
    return ok


def test_analyze_real():
    titulo("Teste 1 — POST /analyze  (caso real MU-1442951 — Aline)")
    r = req("POST", "/analyze", MU_REAL)
    score   = r["fraud_score"]
    nivel   = r["fraud_nivel"]
    n_flags = len(r["flags"])
    ok = nivel == "bloqueado" and score >= 70

    print(f"  {PASS if ok else FAIL}  fraud_score  : {score}")
    print(f"  {'  '} fraud_nivel  : {nivel}")
    print(f"  {'  '} flags ({n_flags})   :")
    for f in r["flags"]:
        print(f"        • [{f['pontos']:>5.1f}pts]  {f['descricao']}")
    print(f"  {'  '} recomendação : {r['recomendacao']}")
    return ok


def test_analyze_normal():
    titulo("Teste 2 — POST /analyze  (MU normal — sem fraude)")
    r = req("POST", "/analyze", MU_NORMAL)
    score = r["fraud_score"]
    nivel = r["fraud_nivel"]
    ok    = nivel == "ok" and score <= 20

    print(f"  {PASS if ok else FAIL}  fraud_score : {score}")
    print(f"  {'  '} fraud_nivel : {nivel}")
    print(f"  {'  '} flags       : {len(r['flags'])} — {[f['regra'] for f in r['flags']] or '—'}")
    return ok


def test_analyze_ghost():
    titulo("Teste 3 — POST /analyze  (ghost worker — GPS errado + histórico ruim)")
    r = req("POST", "/analyze", MU_GHOST)
    score = r["fraud_score"]
    nivel = r["fraud_nivel"]
    ok    = score > 20

    print(f"  {PASS if ok else FAIL}  fraud_score : {score}")
    print(f"  {'  '} fraud_nivel : {nivel}")
    for f in r["flags"]:
        print(f"        • [{f['pontos']:>5.1f}pts]  {f['descricao']}")
    return ok


def test_list_mus():
    titulo("Teste 4 — GET /mission-units  (filtro: bloqueado)")
    r = req("GET", "/mission-units?fraud_nivel=bloqueado&limit=5")
    ok = isinstance(r, list) and len(r) > 0

    print(f"  {PASS if ok else FAIL}  {len(r)} MUs retornadas")
    for mu in r[:3]:
        print(f"        {mu['mu_id']}  score={mu['fraud_score']}  {mu['fraud_nivel']}  {mu['missionario_nome']}")
    return ok


def test_report():
    titulo("Teste 5 — GET /report")
    r = req("GET", "/report")
    ok = r["total_mus"] > 0

    print(f"  {PASS if ok else FAIL}  Total MUs      : {r['total_mus']}")
    print(f"       ok         : {r['ok']}")
    print(f"       atenção    : {r['atencao']}")
    print(f"       suspeito   : {r['suspeito']}")
    print(f"       bloqueado  : {r['bloqueado']}")
    print(f"       valor total: R$ {r['valor_total_rs']:,.2f}")
    print(f"       em risco   : R$ {r['valor_em_risco_rs']:,.2f}")
    print(f"       taxa fraude: {r['taxa_fraude_pct']}%")
    return ok


def test_webhook():
    titulo("Teste 6 — POST /webhook  (evento mu.checkin)")
    payload = {
        "event_type": "mu.checkin",
        "mu_id": "MU-1442951",
        "timestamp": "2026-03-16T14:00:00",
        "payload": {"missionario_id": "USR-1442951", "lat": -23.5718, "lng": -46.6858},
    }
    r = req("POST", "/webhook", payload)
    ok = r["received"] is True

    print(f"  {PASS if ok else FAIL}  received    : {r['received']}")
    print(f"       event_type : {r['event_type']}")
    print(f"       ação       : {r['acao']}")
    return ok


if __name__ == "__main__":
    print("\n" + "═"*55)
    print("  Mission Brasil — Anti-Fraud API · Test Suite")
    print("═"*55)

    testes = [
        test_health,
        test_analyze_real,
        test_analyze_normal,
        test_analyze_ghost,
        test_list_mus,
        test_report,
        test_webhook,
    ]

    resultados = []
    for t in testes:
        try:
            resultados.append(t())
        except urllib.error.URLError:
            print(f"\n  {FAIL}  Servidor não está rodando!")
            print("     Suba o servidor primeiro:  uvicorn app:app --reload --port 8000")
            break
        except Exception as e:
            print(f"  {FAIL}  Erro inesperado: {e}")
            resultados.append(False)

    total  = len(resultados)
    passou = sum(resultados)
    print(f"\n{'═'*55}")
    print(f"  Resultado: {passou}/{total} testes passaram  {'🎉' if passou == total else '⚠️'}")
    print(f"{'═'*55}\n")
