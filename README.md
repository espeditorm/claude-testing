# Consultor de investimentos com Claude

Programa que monta uma recomendação de carteira de ações da B3 para o seu perfil:

1. **Dados de mercado.** Busca cerca de 100 pregões de cotações na [Alpha Vantage](https://www.alphavantage.co/), API da lista [public-apis](https://github.com/public-apis/public-apis#finance). Também busca a Selic no Banco Central.
2. **Análise quantitativa.** Calcula retorno, volatilidade, drawdown e médias móveis de cada ativo. Depois sugere os pesos da carteira que teriam o maior índice de Sharpe histórico, com um limite máximo por ativo que depende do seu perfil.
3. **Recomendação do Claude.** O Claude pesquisa na web as notícias e os fundamentos recentes de cada ativo e ajusta os pesos. Para cada ação, ele estima um **preço justo** e um **preço-teto de compra** (com margem de segurança). O relatório inclui cenários para 1 e 12 meses comparados ao CDI.

O resultado é salvo em `relatorio-AAAA-MM-DD.md`.

## Como usar

```bash
pip install -r requirements.txt

export ANTHROPIC_API_KEY=...        # console.anthropic.com
export ALPHAVANTAGE_API_KEY=...     # grátis em alphavantage.co/support/#api-key

cp perfil.exemplo.json perfil.json  # edite com seu valor, perfil de risco e ações
python consultor.py
```

Para testar sem gastar nada, rode `python consultor.py --offline --sem-claude`. Esse comando usa dados **sintéticos** e só mostra a parte quantitativa.

### Perfil (`perfil.json`)

| Campo | Exemplo |
|---|---|
| `valor_disponivel_reais` | `10000` |
| `aporte_mensal_reais` | `1000` |
| `horizonte` | `"3 anos"` |
| `perfil_de_risco` | `conservador`, `moderado` ou `arrojado` (limite de 20%, 30% ou 40% por ativo) |
| `objetivo` | texto livre |
| `ja_possui`, `evitar_setores` | listas |
| `ativos_de_interesse` | tickers com sufixo `.SA`, ex.: `"WEGE3.SA"` |

O plano grátis da Alpha Vantage permite 25 consultas por dia. Por isso, use no máximo cerca de 20 ativos por execução. Cada execução do Claude custa alguns centavos de dólar, porque o programa faz buscas na web e usa raciocínio estendido.

## Limitações (leia antes de investir)

- **Ninguém prevê o retorno de um mês.** O Claude trabalha com cenários, não com promessas. O otimizador usa só cerca de 5 meses de histórico, e retorno passado não garante retorno futuro.
- O preço justo é uma estimativa e varia bastante conforme as premissas usadas.
- Isto é uma ferramenta de apoio à decisão, **não** uma recomendação formal de um analista CNPI. A decisão e o risco são seus.
