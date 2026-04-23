import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from .database import obter_conexao

def eh_primo(n):
    if n <= 1: return False
    if n <= 3: return True
    if n % 2 == 0 or n % 3 == 0: return False
    i = 5
    while i * i <= n:
        if n % i == 0 or n % (i + 2) == 0:
            return False
        i += 6
    return True

def extrair_features(dezenas):
    soma = sum(dezenas)
    pares = sum(1 for d in dezenas if d % 2 == 0)
    primos = sum(1 for d in dezenas if eh_primo(d))
    return [soma, pares, primos]

def treinar_modelo_loteria(loteria):
    conn = obter_conexao()
    df = pd.read_sql_query("SELECT dezenas FROM resultados WHERE loteria = ? ORDER BY id_concurso DESC LIMIT 500", conn, params=(loteria,))
    conn.close()

    if len(df) < 50:
        return None

    X = []
    for dezenas_str in df['dezenas']:
        dezenas = [int(x) for x in dezenas_str.split(',')]
        X.append(extrair_features(dezenas))
    
    X = np.array(X)
    kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
    kmeans.fit(X)
    
    unique, counts = np.unique(kmeans.labels_, return_counts=True)
    cluster_campeao = unique[np.argmax(counts)]
    
    return kmeans, cluster_campeao

def jogo_aprovado_pela_ia(jogo, modelo_ia, cluster_campeao):
    features = np.array([extrair_features(jogo)])
    cluster_previsto = modelo_ia.predict(features)[0]
    return cluster_previsto == cluster_campeao