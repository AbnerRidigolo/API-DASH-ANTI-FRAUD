"""
app.py — API Anti-Fraude Mission Brasil (FastAPI)
Endpoints:
  POST /analyze              — analisa uma MU e retorna fraud score
  GET  /mission-units        — lista MUs com filtros
  GET  /report               — relatório batch com resumo
  POST /webhook              — simula recebimento de evento da API Mission

Rodar localmente:
  pip install fastapi uvicorn pydantic
  uvicorn app:app --reload --port 8000

Docs interativos: http://localhost:8000/docs
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum
import math
import random

# ── App ──────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Mission Brasil — Anti-Fraud API",
    description=(
        "API de análise anti-fraude para missões de Staff on Demand. "
        "Detecta ghost workers, checkout antecipado, manipulação de timestamp e GPS divergente."
    ),
    version="1.0.0",
    contact={"name": "Mission Brasil Product Data Team"},
)

# ── Enums ────────────────────────────────────────────────────────────────────

class FraudNivel(str, Enum):
    ok        = "ok"
    atencao   = "atencao"
    suspeito  = "suspeito"
    bloqueado = "bloqueado"

class StatusMU(str, Enum):
    aprovado        = "Aprovado"
    reprovado       = "Reprovado"
    validando       = "Validando Dados"
    em_andamento    = "Em Andamento"

class TipoAtividade(str, Enum):
    check_in  = "check_in"
    check_out = "check_out"
    iniciou   = "iniciou"
    finalizou = "finalizou"

# ── Pydantic Models (Request / Response) ─────────────────────────────────────

class AtividadeIn(BaseModel):
    tipo:      TipoAtividade
    timestamp: datetime
    lat:       Optional[float] = None
    lng:       Optional[float] = None

    model_config = {"json_schema_extra": {"example": {
        "tipo": "check_in",
        "timestamp": "2026-03-16T14:00:00",
        "lat": -23.5718,
        "lng": -46.6858,
    }}}

class RecompensaIn(BaseModel):
    dinheiro: float = Field(..., ge=0, description="Valor em R$")
    pontos:   int   = Field(0,  ge=0)

class MissaoIn(BaseModel):
    id:                      str
    nome:                    str
    descricao:               str
    duracao_esperada_horas:  float = Field(..., gt=0)
    recompensa:              RecompensaIn
    criado_em:               datetime
    categoria:               Optional[str] = None
    assinatura:              str = "FREE"

class MissionarioIn(BaseModel):
    id:                    str
    nome:                  str
    historico_missoes:     int = 0
    historico_reprovacoes: int = 0

class LocalizacaoIn(BaseModel):
    endereco: str
    lat:      float
    lng:      float

class AnalyzeRequest(BaseModel):
    mu_id:       str
    missao:      MissaoIn
    missionario: MissionarioIn
    localizacao: LocalizacaoIn
    status:      StatusMU
    atividades:  List[AtividadeIn]

    model_config = {"json_schema_extra": {"example": {
        "mu_id": "MU-1442951",
        "status": "Validando Dados",
        "missao": {
            "id": "MB-1009259",
            "nome": "Hostess | Seg–Sáb | Turnos de 8h",
            "descricao": "Realizar ação de ESPECIALISTA DENGO. Atendimento ao cliente, organização e limpeza de loja.",
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
    }}}

class FlagDetalhe(BaseModel):
    regra:    str
    descricao: str
    pontos:   float

class AnalyzeResponse(BaseModel):
    mu_id:        str
    fraud_score:  float = Field(..., description="Score 0–100")
    fraud_nivel:  FraudNivel
    flags:        List[FlagDetalhe]
    recomendacao: str
    analisado_em: datetime

class MissionUnitSummary(BaseModel):
    mu_id:              str
    missionario_nome:   str
    missao_nome:        str
    recompensa_rs:      float
    status:             str
    fraud_score:        float
    fraud_nivel:        FraudNivel
    n_flags:            int

class ReportResponse(BaseModel):
    gerado_em:          datetime
    total_mus:          int
    ok:                 int
    atencao:            int
    suspeito:           int
    bloqueado:          int
    valor_total_rs:     float
    valor_em_risco_rs:  float
    taxa_fraude_pct:    float
    top_flags:          List[dict]
    mus_criticas:       List[MissionUnitSummary]

class WebhookEvent(BaseModel):
    event_type: str = Field(..., description="Ex: mu.created, mu.checkin, mu.checkout, mu.finalized")
    mu_id:      str
    timestamp:  datetime
    payload:    dict

    model_config = {"json_schema_extra": {"example": {
        "event_type": "mu.checkin",
        "mu_id": "MU-1442951",
        "timestamp": "2026-03-16T14:00:00",
        "payload": {
            "missionario_id": "USR-1442951",
            "lat": -23.5718,
            "lng": -46.6858,
        }
    }}}

class WebhookResponse(BaseModel):
    received:   bool
    mu_id:      str
    event_type: str
    acao:       str

# ── Fraud Engine (inline) ────────────────────────────────────────────────────

def _haversine(lat1, lng1, lat2, lng2) -> float:
    R, p = 6371, math.pi / 180
    a = (math.sin((lat2-lat1)*p/2)**2 +
         math.cos(lat1*p)*math.cos(lat2*p)*math.sin((lng2-lng1)*p/2)**2)
    return 2*R*math.asin(math.sqrt(a))

def _get(atividades, tipo):
    return next((a for a in atividades if a.tipo == tipo), None)

def _analisar(req: AnalyzeRequest) -> AnalyzeResponse:
    flags  = []
    score  = 0.0

    ci = _get(req.atividades, "check_in")
    co = _get(req.atividades, "check_out")
    ini = _get(req.atividades, "iniciou")
    fin = _get(req.atividades, "finalizou")

    # Regra 1 — check-in antes da criação
    if ci and ci.timestamp < req.missao.criado_em:
        delta_h = (req.missao.criado_em - ci.timestamp).total_seconds() / 3600
        pts = 40.0
        flags.append(FlagDetalhe(
            regra="checkin_antes_criacao",
            descricao=f"check_in {delta_h:.1f}h antes da criação da missão",
            pontos=pts,
        ))
        score += pts

    # Regra 2 — duração zero ou impossível
    if ini and fin:
        dur_s = (fin.timestamp - ini.timestamp).total_seconds()
        if dur_s <= 0:
            pts = 35.0
            flags.append(FlagDetalhe(
                regra="duracao_zero",
                descricao="iniciou e finalizou no mesmo instante (duração = 0s)",
                pontos=pts,
            ))
            score += pts
        elif dur_s < 60:
            pts = 30.0
            flags.append(FlagDetalhe(
                regra="duracao_impossivel",
                descricao=f"execução em {dur_s:.0f}s — impossível para essa missão",
                pontos=pts,
            ))
            score += pts

    # Regra 3 — checkout antecipado
    if ci and co:
        dur_real_h = (co.timestamp - ci.timestamp).total_seconds() / 3600
        dur_esp_h  = req.missao.duracao_esperada_horas
        if dur_real_h < 0:
            pts = 45.0
            flags.append(FlagDetalhe(
                regra="checkout_antes_checkin",
                descricao="checkout anterior ao check-in (impossível)",
                pontos=pts,
            ))
            score += pts
        elif dur_esp_h > 0:
            pct = dur_real_h / dur_esp_h
            if pct < 0.70:
                pts = round(25.0 + (0.70 - pct) * 40, 1)
                flags.append(FlagDetalhe(
                    regra="checkout_antecipado",
                    descricao=f"ficou {dur_real_h:.1f}h de {dur_esp_h:.0f}h esperadas ({pct*100:.0f}%)",
                    pontos=pts,
                ))
                score += pts

    # Regra 4 — GPS fora do local
    if ci and ci.lat is not None:
        dist = _haversine(ci.lat, ci.lng, req.localizacao.lat, req.localizacao.lng)
        if dist > 0.5:
            pts = round(20.0 + min(dist * 8, 30.0), 1)
            flags.append(FlagDetalhe(
                regra="gps_fora_do_local",
                descricao=f"GPS do check-in {dist:.2f}km do local esperado",
                pontos=pts,
            ))
            score += pts

    # Regra 5 — GPS check-in vs checkout divergente
    if ci and co and ci.lat is not None and co.lat is not None:
        dist = _haversine(ci.lat, ci.lng, co.lat, co.lng)
        if dist > 1.0:
            pts = 20.0
            flags.append(FlagDetalhe(
                regra="gps_checkout_divergente",
                descricao=f"check-in e check-out em locais {dist:.2f}km distantes",
                pontos=pts,
            ))
            score += pts

    # Regra 6 — histórico de reprovações
    total = req.missionario.historico_missoes
    reprov = req.missionario.historico_reprovacoes
    if total >= 3 and (reprov / total) > 0.30:
        pct_r = reprov / total
        pts = round(15.0 + pct_r * 20, 1)
        flags.append(FlagDetalhe(
            regra="historico_reprovacoes",
            descricao=f"{reprov} reprovações em {total} missões ({pct_r*100:.0f}%)",
            pontos=pts,
        ))
        score += pts

    # Regra 7 — atividades obrigatórias ausentes
    tipos_presentes = {a.tipo for a in req.atividades}
    ausentes = {"check_in", "check_out", "finalizou"} - tipos_presentes
    if ausentes:
        pts = 15.0 * len(ausentes)
        flags.append(FlagDetalhe(
            regra="atividades_ausentes",
            descricao=f"atividades obrigatórias ausentes: {', '.join(sorted(ausentes))}",
            pontos=pts,
        ))
        score += pts

    score = min(round(score, 1), 100.0)

    if score <= 20:    nivel = FraudNivel.ok
    elif score <= 45:  nivel = FraudNivel.atencao
    elif score <= 70:  nivel = FraudNivel.suspeito
    else:              nivel = FraudNivel.bloqueado

    recomendacoes = {
        FraudNivel.ok:        "Aprovar automaticamente.",
        FraudNivel.atencao:   "Monitorar — enviar para fila de revisão leve.",
        FraudNivel.suspeito:  "Bloquear pagamento — enviar para análise manual.",
        FraudNivel.bloqueado: "Bloquear pagamento e notificar compliance imediatamente.",
    }

    return AnalyzeResponse(
        mu_id=req.mu_id,
        fraud_score=score,
        fraud_nivel=nivel,
        flags=flags,
        recomendacao=recomendacoes[nivel],
        analisado_em=datetime.now(),
    )

# ── Mock database (para GET /mission-units e GET /report) ────────────────────

def _gerar_mock_db():
    """Gera 50 MUs sintéticas para demonstração dos endpoints GET."""
    random.seed(42)
    mus = []
    missoes_ref = [
        ("MB-1009259", "Hostess | Turnos de 8h",         8, 140),
        ("MB-1003412", "Repositor de Gôndola | 6h",      6,  90),
        ("MB-1007881", "Promotor iFood | 4h",             4,  80),
        ("MB-1011004", "Picking & Packing | Noturno 8h",  8, 160),
        ("MB-1018550", "Pesquisa de Preços | 2h",         2,  40),
    ]
    nomes = ["Ana Lima","Carlos Moura","Fernanda Santos","Roberto Pereira",
             "Juliana Ferreira","Diego Ramos","Camila Souza","Thiago Lima"]
    niveis_dist = (["ok"]*30 + ["atencao"]*10 + ["suspeito"]*6 + ["bloqueado"]*4)
    random.shuffle(niveis_dist)

    for i in range(50):
        m = random.choice(missoes_ref)
        nivel = niveis_dist[i]
        score = {"ok": random.uniform(0,20), "atencao": random.uniform(21,45),
                 "suspeito": random.uniform(46,70), "bloqueado": random.uniform(71,100)}[nivel]
        mus.append(MissionUnitSummary(
            mu_id=f"MU-{1000000+i}",
            missionario_nome=random.choice(nomes),
            missao_nome=m[1],
            recompensa_rs=float(m[3]),
            status="Validando Dados" if nivel != "ok" else "Aprovado",
            fraud_score=round(score, 1),
            fraud_nivel=FraudNivel(nivel),
            n_flags={"ok":0,"atencao":1,"suspeito":2,"bloqueado":3}[nivel],
        ))
    return mus

_MOCK_DB = _gerar_mock_db()

# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.post(
    "/analyze",
    response_model=AnalyzeResponse,
    summary="Analisar uma MU — retorna fraud score e flags",
    tags=["Análise"],
)
def analyze(req: AnalyzeRequest):
    """
    Recebe os dados completos de uma Mission Unit (MU) e retorna:
    - **fraud_score**: 0–100
    - **fraud_nivel**: ok | atencao | suspeito | bloqueado
    - **flags**: lista de anomalias detectadas com pontuação
    - **recomendacao**: ação sugerida

    Detecta: check-in antes da criação, duração zero, checkout antecipado,
    GPS fora do local, GPS divergente, histórico de reprovações, atividades ausentes.
    """
    return _analisar(req)


@app.get(
    "/mission-units",
    response_model=List[MissionUnitSummary],
    summary="Listar MUs com filtros",
    tags=["Consulta"],
)
def list_mission_units(
    fraud_nivel: Optional[FraudNivel] = Query(None, description="Filtrar por nível de risco"),
    min_score:   float                = Query(0,    description="Score mínimo"),
    max_score:   float                = Query(100,  description="Score máximo"),
    limit:       int                  = Query(20,   ge=1, le=100),
    offset:      int                  = Query(0,    ge=0),
):
    """
    Lista mission units com filtros opcionais de nível de risco e score.
    Dados sintéticos — substituir pela query no banco real quando disponível.
    """
    mus = _MOCK_DB
    if fraud_nivel:
        mus = [m for m in mus if m.fraud_nivel == fraud_nivel]
    mus = [m for m in mus if min_score <= m.fraud_score <= max_score]
    return mus[offset: offset + limit]


@app.get(
    "/report",
    response_model=ReportResponse,
    summary="Relatório batch — resumo de fraude",
    tags=["Relatório"],
)
def report():
    """
    Retorna resumo executivo do batch atual:
    - Contagem por nível de risco
    - Valor total e valor em risco (R$)
    - Taxa de fraude (%)
    - Top flags mais frequentes
    - MUs críticas (bloqueado + suspeito)
    """
    mus = _MOCK_DB
    niveis = {n: sum(1 for m in mus if m.fraud_nivel == FraudNivel(n))
              for n in ["ok", "atencao", "suspeito", "bloqueado"]}
    valor_total   = sum(m.recompensa_rs for m in mus)
    valor_em_risco = sum(m.recompensa_rs for m in mus
                         if m.fraud_nivel in (FraudNivel.suspeito, FraudNivel.bloqueado))
    taxa = round((niveis["suspeito"] + niveis["bloqueado"]) / len(mus) * 100, 1)

    top_flags = [
        {"flag": "checkin_antes_criacao",  "ocorrencias": 10, "impacto_rs": 1400},
        {"flag": "duracao_zero",           "ocorrencias": 7,  "impacto_rs": 980},
        {"flag": "checkout_antecipado",    "ocorrencias": 6,  "impacto_rs": 540},
        {"flag": "gps_fora_do_local",      "ocorrencias": 4,  "impacto_rs": 480},
    ]

    criticas = [m for m in mus if m.fraud_nivel in (FraudNivel.bloqueado, FraudNivel.suspeito)]
    criticas.sort(key=lambda x: -x.fraud_score)

    return ReportResponse(
        gerado_em=datetime.now(),
        total_mus=len(mus),
        ok=niveis["ok"],
        atencao=niveis["atencao"],
        suspeito=niveis["suspeito"],
        bloqueado=niveis["bloqueado"],
        valor_total_rs=round(valor_total, 2),
        valor_em_risco_rs=round(valor_em_risco, 2),
        taxa_fraude_pct=taxa,
        top_flags=top_flags,
        mus_criticas=criticas[:10],
    )


@app.post(
    "/webhook",
    response_model=WebhookResponse,
    summary="Receber evento da API Mission Brasil",
    tags=["Webhook"],
)
def webhook(event: WebhookEvent):
    """
    Simula o recebimento de eventos em tempo real da API Mission Brasil.

    Tipos de evento suportados:
    - **mu.created**   → registra nova missão
    - **mu.checkin**   → registra check-in (valida GPS imediatamente)
    - **mu.checkout**  → registra check-out
    - **mu.finalized** → dispara análise completa de fraude

    Na produção: este endpoint será chamado pelo webhook da API Mission.
    """
    acoes = {
        "mu.created":   "Missão registrada. Aguardando check-in.",
        "mu.checkin":   "Check-in recebido. GPS validado. Monitorando duração.",
        "mu.checkout":  "Check-out recebido. Calculando duração real.",
        "mu.finalized": "Finalização recebida. Análise de fraude disparada.",
    }
    acao = acoes.get(event.event_type, f"Evento '{event.event_type}' registrado.")

    return WebhookResponse(
        received=True,
        mu_id=event.mu_id,
        event_type=event.event_type,
        acao=acao,
    )


@app.get("/", include_in_schema=False)
def root():
    return {"status": "ok", "docs": "/docs", "version": "1.0.0"}
