import pandas as pd
import json
import gzip
from pathlib import Path

def extrair_andamento(caminho_gz):
    """Lê o andamento municipal a partir dos ficheiros compactados."""
    conteudo = gzip.decompress(caminho_gz.read_bytes())
    dados = json.loads(conteudo)
    return {
        a["cdabr"]: {
            "secoes_total": int(a["s"]["ts"]),
            "secoes_apuradas": int(a["s"]["st"]),
            "eleitorado_total": int(a["e"]["te"]),
            "eleitorado_apurado": int(a["e"]["est"])
        }
        for a in dados.get("abr", []) if a.get("tpabr") == "mun"
    }

def construir_dataset(pasta_snapshot, candidatos_alvo):
    """
    Constrói a base de dados do instante, cruzando municípios com os totais de UF
    para detetar os atrasos de propagação do TSE.
    """
    registos = []
    
    for ficheiro in pasta_snapshot.glob("*-ab.json.gz"):
        uf = ficheiro.name.split("-")[0]
        andamentos = extrair_andamento(ficheiro)
        
        for cod_mun, dados_mun in andamentos.items():
            registos.append({
                "uf": uf,
                "municipio": cod_mun,
                **dados_mun
            })
            
    df = pd.DataFrame(registos)
    
    # Prepara as colunas dos candidatos (serão preenchidas com merge dos votos)
    for cand in candidatos_alvo:
        df[cand] = 0
        
    return df

# A integração com o modelo ocorre extraindo o DF mais recente:
# df_atual = construir_dataset(Path("data/raw/20261025_180000"), ["LULA", "FLAVIO BOLSONARO"])