import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path
import time

# Configuração da página para ocupar todo o ecrã
st.set_page_config(page_title="Eleições 2026 - Projeção 2º Turno", layout="wide")

PASTA_SAIDA = Path(__file__).parent.parent.parent / "outputs"
ARQUIVO_HISTORICO = PASTA_SAIDA / "historico_2026.csv"

def carregar_dados():
    """Lê o histórico de projeções gerado pelo modelo."""
    if not ARQUIVO_HISTORICO.exists():
        return None
    df = pd.read_csv(ARQUIVO_HISTORICO, sep=";", decimal=",")
    df['momento'] = pd.to_datetime(df['momento'])
    return df

def desenhar_grafico_projecao(df, candidato, cor):
    """Cria o gráfico de linhas com a margem de incerteza (faixa 90%)."""
    df_cand = df[df['candidato'] == candidato].sort_values('momento')
    
    fig = go.Figure()
    
    # Faixa de Incerteza (p5 a p95)
    fig.add_trace(go.Scatter(
        x=df_cand['momento'].tolist() + df_cand['momento'].tolist()[::-1],
        y=df_cand['p95'].tolist() + df_cand['p5'].tolist()[::-1],
        fill='toself',
        fillcolor=f"rgba{cor}",
        line=dict(color='rgba(255,255,255,0)'),
        name='Margem de Erro (90%)'
    ))
    
    # Linha Central da Projeção
    fig.add_trace(go.Scatter(
        x=df_cand['momento'],
        y=df_cand['pct_projetado'],
        mode='lines',
        line=dict(color=f"rgb{cor}", width=3),
        name=f'Projeção {candidato}'
    ))
    
    # Placar Apurado (Contagem Real)
    fig.add_trace(go.Scatter(
        x=df_cand['momento'],
        y=df_cand['pct_apurado'],
        mode='lines',
        line=dict(color='gray', width=2, dash='dot'),
        name='Apurado (TSE)'
    ))
    
    fig.update_layout(
        title=f"Evolução da Projeção - {candidato}",
        yaxis_title="% Votos Válidos",
        xaxis_title="Hora",
        hovermode="x unified",
        template="plotly_white"
    )
    return fig

# --- Layout do Painel ---
st.title("🗳️ Projeção em Tempo Real - 2º Turno 2026")

df_hist = carregar_dados()

if df_hist is None:
    st.warning("A aguardar os primeiros dados do TSE...")
else:
    # Filtra o último instante para os KPIs
    ultimo_instante = df_hist['momento'].max()
    df_atual = df_hist[df_hist['momento'] == ultimo_instante]
    urnas_apuradas = df_atual.iloc[0]['pct_secoes_apuradas']
    
    st.markdown(f"**Última atualização:** {ultimo_instante.strftime('%H:%M:%S')} | **Urnas apuradas:** {urnas_apuradas:.2f}%")
    
    # Separa os candidatos (assumindo a estrutura do ficheiro fornecido)
    cand_A = df_atual.iloc[0]
    cand_B = df_atual.iloc[1]
    
    # Cartões de Destaque
    col1, col2 = st.columns(2)
    
    with col1:
        st.info(f"### {cand_A['candidato']}")
        st.metric(label="Projeção Final do Modelo", value=f"{cand_A['pct_projetado']:.2f}%")
        st.caption(f"Placar atual: {cand_A['pct_apurado']:.2f}% | Margem: {cand_A['p5']:.1f}% - {cand_A['p95']:.1f}%")
        
    with col2:
        st.error(f"### {cand_B['candidato']}")
        st.metric(label="Projeção Final do Modelo", value=f"{cand_B['pct_projetado']:.2f}%")
        st.caption(f"Placar atual: {cand_B['pct_apurado']:.2f}% | Margem: {cand_B['p5']:.1f}% - {cand_B['p95']:.1f}%")
    
    st.divider()
    
    # Gráficos da Evolução
    st.subheader("Tendência da Apuração vs Projeção")
    graf_col1, graf_col2 = st.columns(2)
    
    with graf_col1:
        st.plotly_chart(desenhar_grafico_projecao(df_hist, cand_A['candidato'], "(37, 99, 235, 0.2)"), use_container_width=True)
    with graf_col2:
        st.plotly_chart(desenhar_grafico_projecao(df_hist, cand_B['candidato'], "(220, 38, 38, 0.2)"), use_container_width=True)

# Lógica de auto-refresh nativa do Streamlit (recarrega a cada 60s)
time.sleep(60)
st.rerun()