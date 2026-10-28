import numpy as np
import pandas as pd

MIN_MUN = 30
K_UF = 10
N_SIM = 2000
SEMENTE = 42

def logit(p):
    p = np.clip(p, 0.01, 0.99)
    return np.log(p / (1 - p))

def sigmoid(z):
    return 1 / (1 + np.exp(-z))

def ajustar_wls(x, y, w):
    """Regressão Linear Ponderada WLS para o swing nacional."""
    sw = w.sum()
    mx, my = (w * x).sum() / sw, (w * y).sum() / sw
    vx = (w * (x - mx) ** 2).sum() / sw
    if len(x) < MIN_MUN or vx < 1e-4:
        return my - mx, 1.0
    b = (w * (x - mx) * (y - my)).sum() / sw / vx
    return my - b * mx, b

def projetar_v3(df, candidatos, sigma_abstencao=0.03):
    """
    Nova projeção: inclui incerteza de abstenção e choque nacional dinâmico.
    """
    cand_A, cand_B = candidatos[0], candidatos[1]
    
    # 1. Preparação de Dados (Logit Transformation)
    A, B = df[cand_A].to_numpy(float), df[cand_B].to_numpy(float)
    obs2 = A + B
    est, te, st = df["est"].to_numpy(float), df["te"].to_numpy(float), df["st"].to_numpy(float)
    
    tem_t1 = df["vv1"].notna() & ((df[f"t1_{cand_A}"] + df[f"t1_{cand_B}"]) > 0)
    x = np.where(tem_t1, logit(df[f"t1_{cand_A}"] / (df[f"t1_{cand_A}"] + df[f"t1_{cand_B}"])), 0.0)
    
    apur = (est > 0) & (obs2 > 0)
    y = np.where(apur, logit(np.where(obs2 > 0, A / np.where(obs2 > 0, obs2, 1), 0.5)), 0.0)
    fit = apur & tem_t1.to_numpy()
    
    if fit.sum() == 0:
        return None, df
        
    # 2. Ajuste Nacional (WLS)
    alfa, beta = ajustar_wls(x[fit], y[fit], obs2[fit])
    resid = y - (alfa + beta * x)
    
    # 3. Efeito por Estado (UF) e Choque Dinâmico
    ufs = df["uf"].to_numpy()
    ef_uf, m_uf = {}, {}
    for uf in np.unique(ufs[fit]):
        sel = fit & (ufs == uf)
        m = sel.sum()
        bruto = (obs2[sel] * resid[sel]).sum() / obs2[sel].sum()
        ef_uf[uf] = bruto * m / (m + K_UF) # Shrinkage
        m_uf[uf] = m

    # O choque nacional (sigma_nac) agora é dinâmico com base na variância dos efeitos das UFs
    brutos_array = np.array(list(ef_uf.values()))
    sigma_nac_dinamico = np.std(brutos_array) if len(brutos_array) > 5 else 0.15
    
    efeito = np.array([ef_uf.get(u, 0.0) for u in ufs])
    resid2 = resid - efeito
    sigma_mun = float(np.sqrt((obs2[fit] * resid2[fit] ** 2).sum() / obs2[fit].sum()))

    # 4. Cálculo de Votos Pendentes (com simulação de comparecimento)
    vv1 = df["vv1"].fillna(0).to_numpy(float)
    eq_t1 = np.where(fit, vv1 * est / np.where(df["te0"] > 0, df["te0"], 1), 0)
    r_comparecimento = obs2[fit].sum() / eq_t1[fit].sum() if eq_t1[fit].sum() > 0 else 1.0
    
    resto = np.where(df["te0"] > 0, (te - est) / np.where(df["te0"] > 0, df["te0"], 1), 0.0)
    falta_base = np.where(apur, obs2 * (te - est) / np.where(est > 0, est, 1), 
                          np.where(tem_t1, vv1 * r_comparecimento * resto, 0.0))
    falta_base = np.maximum(falta_base, 0)

    # 5. Monte Carlo (Incerteza Total: Swing, UF, Nacional e Abstenção)
    rng = np.random.default_rng(SEMENTE)
    xf, yf, wf = x[fit], y[fit], obs2[fit]
    
    lista_uf = list(np.unique(ufs))
    idx_uf = np.array([lista_uf.index(u) for u in ufs])
    
    sim_A = np.zeros(N_SIM)
    sim_B = np.zeros(N_SIM)
    
    nao_apurado = 1 - est.sum() / df["te0"].sum()
    
    for i in range(N_SIM):
        # Bootstrap para variância da regressão
        w_sim = rng.multinomial(len(xf), np.full(len(xf), 1 / len(xf))) * wf
        a_sim, b_sim = ajustar_wls(xf, yf, w_sim) if len(xf) >= MIN_MUN else (alfa, 1.0)
        
        # Choques
        choque_uf = rng.normal([ef_uf.get(u, 0.0) for u in lista_uf], 0.05)[idx_uf]
        choque_nac = rng.normal(0, sigma_nac_dinamico * nao_apurado)
        ruido_mun = rng.normal(0, sigma_mun, size=len(x))
        
        # Simulação de Abstenção (Volatilidade no comparecimento do que falta)
        ruido_abstencao = rng.normal(1.0, sigma_abstencao, size=len(x))
        falta_sim = falta_base * ruido_abstencao
        
        z = a_sim + b_sim * x + choque_uf + choque_nac + ruido_mun
        s = sigmoid(z)
        
        sim_A[i] = A.sum() + (falta_sim * s).sum()
        sim_B[i] = B.sum() + (falta_sim * (1 - s)).sum()

    # 6. Agregação Final
    sim_pct_A = sim_A / (sim_A + sim_B)
    
    resumo = {
        "candidato_referencia": cand_A,
        "pct_central": np.mean(sim_pct_A) * 100,
        "p5": np.percentile(sim_pct_A, 5) * 100,
        "p95": np.percentile(sim_pct_A, 95) * 100,
        "prob_vitoria": (sim_pct_A > 0.5).mean() * 100,
        "sigma_nac_aplicado": sigma_nac_dinamico,
        "taxa_comparecimento_estimada": r_comparecimento
    }
    
    return resumo