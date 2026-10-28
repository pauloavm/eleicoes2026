import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
from pathlib import Path

# Configuração de caminhos e paleta
RAIZ = Path(__file__).parent.parent.parent
ARQUIVO_HISTORICO = RAIZ / "outputs" / "historico_2026.csv"
PASTA_ASSETS = RAIZ / "assets"

CORES = {
    "projecao": "#d6293e", # Vermelho
    "margem": "#d6293e",   # Vermelho (com alpha)
    "apurado": "#8a8f98",  # Cinza
    "texto": "#1d1f23",    # Quase preto
    "fundo_virada": "#f1f3f5"
}

def gerar_grafico_linkedin(candidato_foco="LULA"):
    """Gera um gráfico estático de alta resolução (150 DPI) otimizado para o LinkedIn."""
    PASTA_ASSETS.mkdir(parents=True, exist_ok=True)
    
    # Leitura e preparação de dados
    if not ARQUIVO_HISTORICO.exists():
        print(f"Ficheiro não encontrado: {ARQUIVO_HISTORICO}")
        return

    df = pd.read_csv(ARQUIVO_HISTORICO, sep=";", decimal=",")
    df = df[(df['candidato'] == candidato_foco) & (df['pct_secoes_apuradas'] > 0)]
    df = df.dropna(subset=['pct_projetado'])
    df = df.sort_values("momento").drop_duplicates("pct_secoes_apuradas", keep="last")
    
    x = df['pct_secoes_apuradas']
    y_proj = df['pct_projetado']
    y_real = df['pct_apurado']
    p5 = df['p5']
    p95 = df['p95']
    
    final_score = y_real.iloc[-1]
    
    # Inicialização do plot no estilo "The Economist"
    fig, ax = plt.subplots(figsize=(12, 6.75), dpi=150)
    fig.patch.set_facecolor("white")
    
    # 1. Faixa de Incerteza (Margem de 90%)
    ax.fill_between(x, p5, p95, color=CORES["margem"], alpha=0.12, lw=0, label="Margem (90% das simulações)")
    
    # 2. Linhas Principais
    ax.plot(x, y_proj, color=CORES["projecao"], lw=2.8, label="Projeção do modelo")
    ax.plot(x, y_real, color=CORES["apurado"], lw=2.2, ls="--", label="Placar oficial (TSE)")
    
    # 3. Referências Horizontais (Empate e Resultado Final)
    ax.axhline(50, color=CORES["apurado"], lw=0.8, alpha=0.5)
    ax.axhline(final_score, color=CORES["texto"], lw=1, alpha=0.6)
    ax.text(100, final_score + 0.15, f"Final: {final_score:.2f}%".replace(".", ","), 
            ha="right", va="bottom", fontsize=11, color=CORES["texto"], weight="bold")
    
    # 4. Zona de "Virada" (Quando o candidato foco estava atrás no placar)
    atras = df[df['pct_apurado'] < 50]
    if not atras.empty:
        a, b = atras['pct_secoes_apuradas'].min(), atras['pct_secoes_apuradas'].max()
        ax.axvspan(a, b, color=CORES["fundo_virada"], alpha=0.5, lw=0)
        ax.text((a + b) / 2, 46.5, "Placar mostrava\nadversário à frente", 
                ha="center", va="bottom", fontsize=10, color=CORES["apurado"])
    
    # Destaque com 10% apurado
    df_10 = df[df['pct_secoes_apuradas'] >= 10]
    if not df_10.empty:
        p10 = df_10.iloc[0]
        ax.annotate(f"Com 10% apurado:\nProjeção {p10['pct_projetado']:.1f}%".replace(".", ","),
                    xy=(p10['pct_secoes_apuradas'], p10['pct_projetado']), 
                    xytext=(14, 54.6), fontsize=10.5, color=CORES["projecao"], weight="bold",
                    arrowprops=dict(arrowstyle="-", color=CORES["projecao"], lw=1))

    # Formatação de Eixos
    ax.set_xlim(0, 100)
    ax.set_ylim(46, 57)
    ax.set_xlabel("% de urnas apuradas", fontsize=11, color=CORES["texto"])
    ax.set_ylabel(f"{candidato_foco.title()} - % dos votos válidos", fontsize=11, color=CORES["texto"])
    
    ax.xaxis.set_major_formatter(mtick.PercentFormatter(decimals=0))
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(decimals=0))
    
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)
    ax.tick_params(colors=CORES["texto"])
    ax.grid(axis="y", alpha=0.2)
    ax.legend(loc="upper right", frameon=False, fontsize=10)
    
    # Títulos e Metadados
    fig.suptitle("Projeção do 2º Turno: O modelo antecipou o resultado final", 
                 x=0.06, y=0.975, ha="left", fontsize=16, weight="bold", color=CORES["texto"])
    ax.set_title("Evolução da estimativa considerando a matriz de transferência e o histórico municipal", 
                 loc="left", fontsize=11, color=CORES["apurado"], pad=10)
    fig.text(0.06, 0.015, "Fonte: TSE (dados abertos). Elaboração própria.", fontsize=9, color=CORES["apurado"])
    
    fig.tight_layout(rect=(0.02, 0.03, 1, 0.97))
    
    caminho_saida = PASTA_ASSETS / "linkedin_projecao_final.png"
    fig.savefig(caminho_saida)
    print(f"Gráfico exportado para: {caminho_saida}")

if __name__ == "__main__":
    gerar_grafico_linkedin()