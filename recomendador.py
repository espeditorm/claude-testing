"""Pede ao Claude uma recomendação de carteira a partir do perfil do investidor
e dos dados de mercado. O Claude usa busca na web para checar notícias e
fundamentos recentes antes de recomendar."""

import json

import anthropic

MODELO = "claude-opus-5-5"
MAX_CONTINUACOES = 5

SISTEMA = """Você é um analista de investimentos que atende investidores pessoa física no Brasil.
Sua tarefa é recomendar uma carteira concreta e acionável, em português, a partir do perfil
do investidor e dos dados de mercado fornecidos.

Como trabalhar:
- Use a busca na web para verificar, para cada ativo, notícias do último mês, resultados
  trimestrais recentes e indicadores de valuation (P/L, P/VP, dividend yield, dívida/EBITDA).
  Cite as fontes.
- Os dados de preço fornecidos são reais e mais confiáveis que preços achados na web; use a
  web para fundamentos e contexto.
- A sugestão quantitativa de pesos é só um ponto de partida baseado em ~5 meses de histórico;
  ajuste-a com base em fundamentos, diversificação setorial e no perfil do investidor.
  Você pode recomendar não comprar um ativo, ou manter parte em renda fixa (CDI/Tesouro Selic)
  se a relação risco/retorno das ações não compensar frente à Selic informada.
- Para cada ação recomendada, estime um preço justo (explique o método: múltiplos vs. pares,
  DCF simplificado, Gordon/Bazin para pagadoras de dividendos) e defina um PREÇO-TETO de compra
  com margem de segurança compatível com o perfil de risco.
- Seja honesto sobre incerteza: ninguém prevê o retorno de um mês. Dê cenários (pessimista,
  base, otimista) em vez de uma previsão única, e nunca prometa rentabilidade.

Formato da resposta (Markdown):
1. Resumo em 3-5 linhas.
2. Tabela da carteira: ativo | % | valor em R$ | quantidade aproximada de ações | preço atual |
   preço justo estimado | preço-teto de compra | tese em uma linha.
3. Parcela em renda fixa (se houver) e por quê.
4. Como executar: comprar tudo agora ou em parcelas, o que fazer se o preço estiver acima do teto.
5. Principais riscos e o que monitorar no próximo mês; quando rebalancear.
6. Cenários para 1 mês e 12 meses comparados ao CDI.
7. Aviso final curto de que isto não é recomendação formal de um analista credenciado CNPI."""


def recomendar(perfil: dict, contexto_mercado: dict) -> str:
    client = anthropic.Anthropic()

    pedido = (
        "Perfil do investidor:\n"
        f"{json.dumps(perfil, ensure_ascii=False, indent=2)}\n\n"
        "Dados de mercado e sugestão quantitativa:\n"
        f"{json.dumps(contexto_mercado, ensure_ascii=False, indent=2)}\n\n"
        "Monte a recomendação de carteira."
    )
    mensagens = [{"role": "user", "content": pedido}]

    for _ in range(MAX_CONTINUACOES):
        with client.beta.messages.stream(
            model=MODELO,
            max_tokens=64000,
            system=SISTEMA,
            thinking={"type": "adaptive"},
            output_config={"effort": "high"},
            tools=[{"type": "web_search_20260209", "name": "web_search", "max_uses": 15}],
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
            messages=mensagens,
        ) as stream:
            resposta = stream.get_final_message()

        if resposta.stop_reason == "refusal":
            motivo = resposta.stop_details.explanation if resposta.stop_details else "sem detalhes"
            raise RuntimeError(f"O Claude recusou o pedido: {motivo}")

        if resposta.stop_reason != "pause_turn":
            break
        # A busca na web pausou um turno longo: devolve o conteúdo para o Claude continuar.
        mensagens.append({"role": "assistant", "content": resposta.content})

    if resposta.stop_reason == "max_tokens":
        print("Aviso: a resposta foi cortada por limite de tokens.")

    return "".join(bloco.text for bloco in resposta.content if bloco.type == "text")
