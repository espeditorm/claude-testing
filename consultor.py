"""Consultor de investimentos com Claude.

Uso:
    python consultor.py                      # usa perfil.json
    python consultor.py --perfil meu.json    # outro perfil
    python consultor.py --offline --sem-claude   # teste com dados sintéticos, sem APIs

As chaves de API podem ficar num arquivo .env na mesma pasta (veja .env.exemplo).
"""

import sys

if sys.version_info < (3, 10):
    sys.exit(f"Este programa precisa do Python 3.10 ou mais novo (você está usando {sys.version.split()[0]}).")

import argparse
import getpass
import json
import os
from datetime import datetime
from pathlib import Path

PASTA = Path(__file__).resolve().parent

try:
    import anthropic
    import requests  # noqa: F401  (usado em dados.py)
except ImportError as erro:
    sys.exit(
        f"Falta instalar a biblioteca '{erro.name}'. Rode no terminal do VS Code:\n"
        f'    "{sys.executable}" -m pip install -r requirements.txt'
    )

import analise
import dados
import recomendador


def carregar_env() -> None:
    """Lê chaves do arquivo .env (formato NOME=valor), sem sobrescrever variáveis já definidas."""
    arquivo = PASTA / ".env"
    if not arquivo.exists():
        return
    for linha in arquivo.read_text(encoding="utf-8-sig").splitlines():
        linha = linha.strip()
        if linha and not linha.startswith("#") and "=" in linha:
            nome, valor = linha.split("=", 1)
            os.environ.setdefault(nome.strip(), valor.strip().strip('"').strip("'"))


def exigir_chave(nome: str, onde_obter: str) -> None:
    if os.environ.get(nome):
        return
    print(f"A variável {nome} não está definida ({onde_obter}).")
    valor = getpass.getpass(f"Cole sua {nome} (não aparece na tela) e tecle Enter: ").strip()
    if not valor:
        sys.exit(f"Sem {nome} não dá para continuar. Coloque-a no arquivo .env.")
    os.environ[nome] = valor


PESO_MAXIMO_POR_PERFIL = {"conservador": 0.20, "moderado": 0.30, "arrojado": 0.40}


def arredondar(valor):
    return round(valor, 4) if isinstance(valor, float) else valor


def main() -> int:
    parser = argparse.ArgumentParser(description="Recomenda uma carteira de ações usando Claude.")
    parser.add_argument("--perfil", default="perfil.json", help="arquivo JSON com o perfil do investidor")
    parser.add_argument("--offline", action="store_true", help="usa dados sintéticos (teste, não são reais)")
    parser.add_argument("--sem-claude", action="store_true", help="mostra só a análise quantitativa")
    args = parser.parse_args()
    carregar_env()
    if not args.offline:
        exigir_chave("ALPHAVANTAGE_API_KEY", "chave grátis em alphavantage.co/support/#api-key")
    if not args.sem_claude:
        exigir_chave("ANTHROPIC_API_KEY", "crie em console.anthropic.com")

    caminho_perfil = Path(args.perfil)
    if not caminho_perfil.is_absolute():
        caminho_perfil = PASTA / caminho_perfil
    if not caminho_perfil.exists():
        caminho_perfil = PASTA / "perfil.exemplo.json"
        print(f"'{args.perfil}' não encontrado; usando {caminho_perfil}.")
    perfil = json.loads(caminho_perfil.read_text(encoding="utf-8"))
    tickers = perfil.get("ativos_de_interesse") or []
    if not tickers:
        print("Informe pelo menos um ticker em 'ativos_de_interesse' no perfil (ex.: \"WEGE3.SA\").")
        return 1
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

    saida = PASTA / Path(f"relatorio-{contexto['data_analise']}.md")
    saida.write_text(relatorio, encoding="utf-8")
    print(relatorio)
    print(f"\nRelatório salvo em {saida}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
