"""Métricas de risco/retorno e sugestão quantitativa de pesos (máximo índice de Sharpe)."""

import math
import random
import statistics

PREGOES_ANO = 252


def retornos_diarios(serie: list[tuple[str, float]]) -> list[float]:
    fechamentos = [p for _, p in serie]
    return [b / a - 1 for a, b in zip(fechamentos, fechamentos[1:])]


def media_movel(valores: list[float], janela: int) -> float | None:
    if len(valores) < janela:
        return None
    return sum(valores[-janela:]) / janela


def metricas(serie: list[tuple[str, float]]) -> dict:
    fechamentos = [p for _, p in serie]
    rets = retornos_diarios(serie)
    atual = fechamentos[-1]

    def variacao(dias: int) -> float | None:
        return atual / fechamentos[-dias - 1] - 1 if len(fechamentos) > dias else None

    pico, drawdown_max = fechamentos[0], 0.0
    for p in fechamentos:
        pico = max(pico, p)
        drawdown_max = min(drawdown_max, p / pico - 1)

    return {
        "data_ultima_cotacao": serie[-1][0],
        "preco_atual": round(atual, 2),
        "variacao_1m": variacao(21),
        "variacao_3m": variacao(63),
        "retorno_anualizado": statistics.fmean(rets) * PREGOES_ANO,
        "volatilidade_anualizada": statistics.stdev(rets) * math.sqrt(PREGOES_ANO),
        "drawdown_maximo": drawdown_max,
        "media_movel_20": media_movel(fechamentos, 20),
        "media_movel_50": media_movel(fechamentos, 50),
        "minima_periodo": min(fechamentos),
        "maxima_periodo": max(fechamentos),
    }


def otimizar_sharpe(
    precos: dict[str, list[tuple[str, float]]],
    taxa_livre_risco: float,
    peso_maximo: float,
    simulacoes: int = 20000,
) -> dict[str, float]:
    """Busca por Monte Carlo a carteira long-only de maior Sharpe histórico,
    respeitando um peso máximo por ativo (diversificação)."""
    tickers = list(precos)
    n = len(tickers)
    if n * peso_maximo < 1:
        raise ValueError(f"Com {n} ativos, o peso máximo {peso_maximo:.0%} não soma 100%.")

    rets = [retornos_diarios(precos[t]) for t in tickers]
    tamanho = min(len(r) for r in rets)
    rets = [r[-tamanho:] for r in rets]
    medias = [statistics.fmean(r) * PREGOES_ANO for r in rets]
    cov = [[statistics.covariance(a, b) * PREGOES_ANO for b in rets] for a in rets]

    rng = random.Random(0)
    melhor_pesos, melhor_sharpe = [1 / n] * n, -math.inf
    for _ in range(simulacoes):
        brutos = [rng.expovariate(1) for _ in range(n)]
        total = sum(brutos)
        pesos = [b / total for b in brutos]
        if max(pesos) > peso_maximo:
            continue
        retorno = sum(w * m for w, m in zip(pesos, medias))
        variancia = sum(pesos[i] * pesos[j] * cov[i][j] for i in range(n) for j in range(n))
        sharpe = (retorno - taxa_livre_risco) / math.sqrt(variancia) if variancia > 0 else -math.inf
        if sharpe > melhor_sharpe:
            melhor_pesos, melhor_sharpe = pesos, sharpe

    return {t: round(w, 4) for t, w in zip(tickers, melhor_pesos)}
