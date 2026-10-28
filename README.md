# 🗳️ Eleições 2026: Projeção em Tempo Real (Nowcasting)

Este repositório contém uma infraestrutura completa de engenharia de dados, modelagem preditiva e visualização para projetar o resultado final do 2º turno da eleição presidencial brasileira de 2026 a partir da apuração parcial do Tribunal Superior Eleitoral (TSE).

Diferente de acompanhar o placar parcial bruto, este modelo corrige os vieses geográficos da apuração (onde regiões com perfis de votação distintos apuram em velocidades diferentes) e antecipa o resultado final com base na transição de votos (swing) em relação ao 1º turno.

---

## 🧠 Como o Modelo Funciona

O modelo de *Nowcasting* prediz o comportamento das urnas que ainda não foram apuradas através dos seguintes passos:

1. **Regressão WLS (Mínimos Quadrados Ponderados) em Logit**: Comparamos a proporção de votos válidos entre os dois finalistas no 1º turno e no 2º turno em cada município já apurado, gerando uma taxa de "swing" nacional.
2. **Efeito de Estado (UF)**: Aplica um ajuste (*shrinkage*) para desvios regionais. Se um estado estiver a deslocar-se mais para um candidato do que a média nacional, isso é ponderado e aplicado aos municípios restantes desse estado.
3. **Simulação de Abstenção**: A taxa de comparecimento é um fator crítico. O modelo simula o comparecimento esperado do que falta apurar aplicando uma volatilidade estocástica baseada nas urnas já fechadas.
4. **Monte Carlo (Incerteza)**: Para cada instante da apuração, são executadas **2.000 simulações**. Cada simulação injeta ruído estatístico na regressão, nos efeitos estaduais e um *choque nacional dinâmico* (que reduz à medida que a apuração avança). Isso gera a nossa faixa de erro de 90% e a probabilidade de vitória.

---

## 🏗️ Arquitetura do Projeto

O código foi totalmente refatorado para garantir máxima resiliência e velocidade.

```text
eleicoes2026-nowcasting/
├── data/
│   ├── raw/                 # Snapshots brutos (.json.gz) coletados do TSE
│   ├── processed/           # Dados consolidados por município/UF
│   └── config/              # Dicionários de municípios do TSE
├── src/
│   ├── data/
│   │   ├── 01_coletor.py    # Crawler assíncrono (aiohttp) para puxar os snapshots
│   │   └── 02_pipeline.py   # Desidrata os JSONs e calcula atrasos TSE vs Município
│   ├── model/
│   │   └── 03_modelo.py     # Núcleo preditivo (Regressão, Logit e Monte Carlo)
│   └── view/
│   │   ├── 04_painel.py     # Dashboard interativo nativo em Streamlit
│   │   └── 05_graficos.py   # Exportador de gráficos de alta qualidade para redes sociais
├── outputs/                 # CSVs do histórico de projeção
├── assets/                  # Gráficos e imagens geradas (ex: linkedin_projecao_final.png)
└── requirements.txt
```

---

## 🚀 Instalação e Execução

### Pré-requisitos
* Python 3.10 ou superior.

### Instalação

1. Clone o repositório:
```bash
git clone https://github.com/seu-usuario/eleicoes2026-nowcasting.git
cd eleicoes2026-nowcasting
```

2. Instale as dependências:
```bash
pip install -r requirements.txt
```

### Como Rodar (Simulação ou Tempo Real)

O fluxo do projeto é modular. Durante a noite de apuração, você precisará de rodar processos em paralelo:

1. **Inicie o coletor de dados** (Em um terminal):
   *Irá buscar os pacotes JSON do TSE a cada minuto de forma assíncrona.*
   ```bash
   python src/data/01_coletor.py
   ```

2. **Inicie o Painel de Visualização** (Em outro terminal):
   *O Streamlit consome automaticamente os dados processados pelo modelo.*
   ```bash
   streamlit run src/view/04_painel.py
   ```

3. **Gerar gráficos estáticos para Redes Sociais** (Sob demanda):
   ```bash
   python src/view/05_graficos.py
   ```

---

## 📊 Vantagens da Nova Arquitetura
* **I/O Assíncrono:** O uso de `asyncio` e `aiohttp` impede o bloqueio de threads durante o *scraping* dos dados.
* **Painel Reativo:** Substituição da injeção de HTML puro pelo `Streamlit`, ganhando interatividade com o `Plotly`.
* **Rigor Estatístico Melhorado:** A antiga margem de "choque nacional" estática foi substituída por cálculos de variância dinâmicos, e a abstenção punitiva agora integra a matriz de simulações.

## 📜 Licença
Distribuído sob a licença MIT. Para mais informações, consulte o arquivo `LICENSE`.