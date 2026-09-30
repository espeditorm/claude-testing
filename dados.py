"""Coleta de dados de mercado.

- Cotações diárias: Alpha Vantage (listada em public-apis/Finance). Ações da B3 usam o sufixo .SA.
- Taxa livre de risco: Selic meta via API SGS do Banco Central (série 432).
"""

import os
import random
import time
from datetime import date, timedelta

import requests

ALPHA_VANTAGE_URL = "https://www.alphavantage.co/query"
BCB_SELIC_URL = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.432/dados/ultimos/1?formato=json"

# Plano gratuito da Alpha Vantage: 5 requisições por minuto, 25 por dia.
INTERVALO_ENTRE_CHAMADAS = 13


class ErroDados(Exception):
    pass


def buscar_precos(ticker: str) -> list[tuple[str, float]]:
    """Retorna [(data, fechamento)] em ordem cronológica (~100 pregões)."""
    chave = os.environ.get("ALPHAVANTAGE_API_KEY")
    if not chave:
        raise ErroDados("Defina a variável ALPHAVANTAGE_API_KEY (chave grátis em alphavantage.co).")

    resp = requests.get(
        ALPHA_VANTAGE_URL,
        params={
            "function": "TIME_SERIES_DAILY",
            "symbol": ticker,
            "outputsize": "compact",
            "apikey": chave,
        },
        timeout=30,
    )
    resp.raise_for_status()
    dados = resp.json()
    serie = dados.get("Time Series (Daily)")
    if not serie:
        msg = dados.get("Note") or dados.get("Information") or dados.get("Error Message") or dados
        raise ErroDados(f"Alpha Vantage não retornou dados para {ticker}: {msg}")

    return sorted((dia, float(valores["4. close"])) for dia, valores in serie.items())


def buscar_selic() -> float:
    """Selic meta anual em fração (ex.: 0.15 para 15% a.a.)."""
    resp = requests.get(BCB_SELIC_URL, timeout=30)
    resp.raise_for_status()
    return float(resp.json()[-1]["valor"].replace(",", ".")) / 100


def buscar_todos(tickers: list[str]) -> dict[str, list[tuple[str, float]]]:
    precos = {}
    for i, ticker in enumerate(tickers):
        if i:
            time.sleep(INTERVALO_ENTRE_CHAMADAS)
        print(f"  baixando {ticker}...")
        precos[ticker] = buscar_precos(ticker)
    return precos


def dados_sinteticos(tickers: list[str], dias: int = 100) -> dict[str, list[tuple[str, float]]]:
    """Séries aleatórias para testar o programa sem chave de API. NÃO são dados reais."""
    rng = random.Random(42)
    inicio = date.today() - timedelta(days=dias * 7 // 5)
    precos = {}
    for ticker in tickers:
        preco = rng.uniform(10, 60)
        tendencia = rng.uniform(-0.001, 0.0015)
        vol = rng.uniform(0.01, 0.03)
        serie = []
        for d in range(dias):
            preco *= 1 + rng.gauss(tendencia, vol)
            serie.append(((inicio + timedelta(days=d * 7 // 5)).isoformat(), round(preco, 2)))
        precos[ticker] = serie
    return precos
