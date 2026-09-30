# Consultor de investimentos com Claude

Programa que monta uma recomendação de carteira de ações da B3 para o seu perfil:

1. **Dados de mercado.** Busca cerca de 100 pregões de cotações na [Alpha Vantage](https://www.alphavantage.co/), API da lista [public-apis](https://github.com/public-apis/public-apis#finance). Também busca a Selic no Banco Central.
2. **Análise quantitativa.** Calcula retorno, volatilidade, drawdown e médias móveis de cada ativo. Depois sugere os pesos da carteira que teriam o maior índice de Sharpe histórico, com um limite máximo por ativo que depende do seu perfil.
3. **Recomendação do Claude.** O Claude pesquisa na web as notícias e os fundamentos recentes de cada ativo e ajusta os pesos. Para cada ação, ele estima um **preço justo** e um **preço-teto de compra** (com margem de segurança). O relatório inclui cenários para 1 e 12 meses comparados ao CDI.

O resultado é salvo em `relatorio-AAAA-MM-DD.md`.

## Como usar no Windows com VS Code

**Pré-requisitos:** instale o [Python 3.10 ou mais novo](https://www.python.org/downloads/) e marque **"Add python.exe to PATH"** durante a instalação. No VS Code, instale a extensão **Python** da Microsoft.

1. No VS Code, abra a pasta do projeto (**Arquivo → Abrir Pasta**).
2. Abra o terminal (**Terminal → Novo Terminal**) e instale as dependências:
   ```powershell
   py -m pip install -r requirements.txt
   ```
   Se aparecer "py não é reconhecido", use `python` no lugar de `py`.
3. Crie o arquivo de chaves. Copie `.env.exemplo` para `.env` e cole as suas chaves:
   ```powershell
   copy .env.exemplo .env
   copy perfil.exemplo.json perfil.json
   ```
   Depois edite `.env` e `perfil.json` no próprio VS Code. Se você não criar o `.env`, o programa pede as chaves ao iniciar.
4. Teste sem chaves (usa dados **sintéticos** e não chama o Claude):
   ```powershell
   py consultor.py --offline --sem-claude
   ```
5. Rode para valer:
   ```powershell
   py consultor.py
   ```
   Outra opção é apertar **F5** e escolher *"Consultor: recomendação completa"*.

**Se aparecer "No module named anthropic":** o VS Code está usando outro Python. Aperte `Ctrl+Shift+P`, escolha **Python: Select Interpreter**, selecione o Python 3.10 ou mais novo e rode o passo 2 de novo.

### Linux / macOS

```bash
python3 -m pip install -r requirements.txt
cp .env.exemplo .env && cp perfil.exemplo.json perfil.json   # edite os dois
python3 consultor.py
```

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
