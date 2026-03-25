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

def extrair_features(lista_dezenas):
    """Extrai o 'DNA' de um jogo (Soma, Pares, Primos e Dispersão)."""
    soma = sum(lista_dezenas)
    pares = sum(1 for x in lista_dezenas if x % 2 == 0)
    primos = sum(1 for x in lista_dezenas if eh_primo(x))
    dispersao = float(np.std(lista_dezenas)) if len(lista_dezenas) > 0 else 0.0
    return [soma, pares, primos, dispersao]

def treinar_modelo_loteria(loteria):
    """Treina o K-Means com o histórico e encontra o perfil que mais sai."""
    conn = obter_conexao()
    df = pd.read_sql_query("SELECT dezenas FROM resultados WHERE loteria = ?", conn, params=(loteria,))
    conn.close()

    if len(df) < 50:
        return None # Histórico insuficiente para IA

    # Converte os dados do banco para o formato matemático da IA
    jogos = df['dezenas'].apply(lambda x: [int(d) for d in x.split(',')]).tolist()
    X = np.array([extrair_features(j) for j in jogos])

    # Agrupa os jogos em 3 "Perfis" (Clusters)
    kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
    kmeans.fit(X)

    # Descobre qual dos 3 perfis tem a maior quantidade de sorteios reais
    labels = pd.Series(kmeans.labels_)
    cluster_campeao = labels.value_counts().idxmax()

    return kmeans, cluster_campeao

def jogo_aprovado_pela_ia(jogo, kmeans, cluster_campeao):
    """Avalia se o jogo gerado aleatoriamente pertence ao grupo vitorioso."""
    features_jogo = np.array(extrair_features(jogo)).reshape(1, -1)
    cluster_previsto = kmeans.predict(features_jogo)[0]
    
    # Só aprova se o jogo tiver o DNA do cluster campeão
    return cluster_previsto == cluster_campeao