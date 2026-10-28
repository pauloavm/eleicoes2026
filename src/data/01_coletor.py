import asyncio
import aiohttp
import json
import gzip
from pathlib import Path
from datetime import datetime

BASE_URL = "https://resultados.tse.jus.br/oficial/ele2026"
ELEICAO = "6258"
CARGO = "c0001"
UFS = ["ac", "al", "am", "ap", "ba", "ce", "df", "es", "go", "ma", "mg", "ms",
       "mt", "pa", "pb", "pe", "pi", "pr", "rj", "rn", "ro", "rr", "rs", "sc",
       "se", "sp", "to", "zz"]

PASTA_RAW = Path(__file__).parent.parent.parent / "data" / "raw"

async def buscar_json(session, url, retries=3):
    """Realiza o fetch assíncrono com tolerância a falhas."""
    for i in range(retries):
        try:
            async with session.get(url, timeout=15) as response:
                response.raise_for_status()
                return await response.read()
        except Exception:
            if i == retries - 1:
                return None
            await asyncio.sleep(1)

async def coletar_ciclo():
    """Baixa os andamentos (-ab) e totais (-u) em paralelo."""
    agora = datetime.now().strftime("%Y%m%d_%H%M%S")
    pasta_destino = PASTA_RAW / agora
    pasta_destino.mkdir(parents=True, exist_ok=True)
    
    async with aiohttp.ClientSession() as session:
        # Tarefas de andamento por UF
        urls_ab = {uf: f"{BASE_URL}/{ELEICAO}/dados/{uf}/{uf}-e{ELEICAO.zfill(6)}-ab.json" for uf in UFS}
        tarefas_ab = [buscar_json(session, url) for url in urls_ab.values()]
        resultados_ab = await asyncio.gather(*tarefas_ab)
        
        # Guarda ficheiros compactados
        for uf, bruto in zip(urls_ab.keys(), resultados_ab):
            if bruto:
                (pasta_destino / f"{uf}-ab.json.gz").write_bytes(gzip.compress(bruto))
                
        # Total Nacional
        url_br = f"{BASE_URL}/{ELEICAO}/dados/br/br-{CARGO}-e{ELEICAO.zfill(6)}-u.json"
        bruto_br = await buscar_json(session, url_br)
        if bruto_br:
            (pasta_destino / "br-total.json").write_bytes(bruto_br)
            
        # Sinaliza fim do ciclo para o pipeline
        (pasta_destino / "ok").touch()
        print(f"Ciclo {agora} concluído com sucesso.")

if __name__ == "__main__":
    asyncio.run(coletar_ciclo())