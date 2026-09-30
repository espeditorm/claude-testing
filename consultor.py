"""Consultor de investimentos com Claude.

Uso:
    python consultor.py                      # usa perfil.json
    python consultor.py --perfil meu.json    # outro perfil
    python consultor.py --offline --sem-claude   # teste com dados sintéticos, sem APIs
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

import anthropic

import analise
import dados
import recomendador

PESO_MAXIMO_POR_PERFIL = {"conservador": 0.20, "moderado": 0.30, "arrojado": 0.40}


def arredondar(valor):
    return round(valor, 4) if isinstance(valor, float) else valor


def main() -> int:
    parser = argparse.ArgumentParser(description="Recomenda uma carteira de ações usando Claude.")
    parser.add_argument("--perfil", default="perfil.json", help="arquivo JSON com o perfil do investidor")
    parser.add_argument("--offline", action="store_true", help="usa dados sintéticos (teste, não são reais)")
    parser.add_argument("--sem-claude", action="store_true", help="mostra só a análise quantitativa")
    args = parser.parse_args()

    caminho_perfil = Path(args.perfil)
    if not caminho_perfil.exists():
        caminho_perfil = Path("perfil.exemplo.json")
        print(f"'{args.perfil}' não encontrado; usando {caminho_perfil}.")
    perfil = json.loads(caminho_perfil.read_text(encoding="utf-8"))
    tickers = perfil["ativos_de_interesse"]
    peso_maximo = PESO_MAXIMO_POR_PERFIL.get(perfil.get("perfil_de_risco", "moderado"), 0.30)
    peso_maximo = max(peso_maximo, 1 / len(tickers))

    print("1/3 Coletando dados de mercado...")
    try:
        if args.offline:
            precos, selic = dados.dados_sinteticos(tickers), 0.15
        else:
            precos, selic = dados.buscar_todos(tickers), dados.buscar_selic()
    except (dados.ErroDados, OSError) as erro:
        print(f"Erro ao coletar dados: {erro}")
        return 1

    print("2/3 Calculando métricas e pesos de máximo Sharpe...")
    contexto = {
        "data_analise": datetime.now().date().isoformat(),
        "dados_sinteticos_de_teste": args.offline,
        "selic_meta_anual": selic,
        "ativos": {t: {k: arredondar(v) for k, v in analise.metricas(s).items()} for t, s in precos.items()},
        "pesos_sugeridos_max_sharpe": analise.otimizar_sharpe(precos, selic, peso_maximo),
        "peso_maximo_por_ativo": peso_maximo,
    }
    print(json.dumps(contexto, ensure_ascii=False, indent=2))

    if args.sem_claude:
        return 0

    print("3/3 Pedindo a recomendação ao Claude (pode levar alguns minutos)...")
    try:
        relatorio = recomendador.recomendar(perfil, contexto)
    except anthropic.AuthenticationError:
        print("Chave da Anthropic inválida ou ausente. Defina ANTHROPIC_API_KEY.")
        return 1
    except (anthropic.APIError, RuntimeError) as erro:
        print(f"Erro ao consultar o Claude: {erro}")
        return 1

    saida = Path(f"relatorio-{contexto['data_analise']}.md")
    saida.write_text(relatorio, encoding="utf-8")
    print(relatorio)
    print(f"\nRelatório salvo em {saida}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
