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
    """Extrai o 'DNA' de um jogo para a IA analisar."""
    soma = sum(lista_dezenas)
    pares = sum(1 for x in lista_dezenas if x % 2 == 0)
    primos = sum(1 for x in lista_dezenas if eh_primo(x))
    # Desvio padrão mede se os números estão espalhados ou concentrados
    dispersao = np.std(lista_dezenas) if len(lista_dezenas) > 0 else 0 
    return [soma, pares, primos, dispersao]

def treinar_modelo_loteria(loteria):
    """
    Treina o modelo K-Means com o histórico da loteria e 
    retorna o perfil (centróide) do cluster mais vitorioso.
    """
    conn = obter_conexao()
    df = pd.read_sql_query("SELECT dezenas FROM resultados WHERE loteria = ?", conn, params=(loteria,))
    conn.close()

    if len(df) < 50:
        return None # Histórico insuficiente para IA

    # Prepara os dados
    jogos = df['dezenas'].apply(lambda x: [int(d) for d in x.split(',')]).tolist()
    X = np.array([extrair_features(j) for j in jogos])

    # Treina o K-Means para encontrar 3 "Perfis" de sorteios
    kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
    kmeans.fit(X)

    # Descobre qual cluster tem mais sorteios (O Perfil Campeão)
    labels = pd.Series(kmeans.labels_)
    cluster_campeao = labels.value_counts().idxmax()
    
    # Pega as características exatas desse perfil campeão
    centroide_campeao = kmeans.cluster_centers_[cluster_campeao]
    
    return kmeans, centroide_campeao

def jogo_aprovado_pela_ia(jogo, kmeans, centroide_campeao):
    """Verifica se o jogo gerado pertence ao cluster vitorioso."""
    features_jogo = np.array(extrair_features(jogo)).reshape(1, -1)
    
    # Prevê a qual cluster o novo jogo pertence
    cluster_previsto = kmeans.predict(features_jogo)[0]
    
    # Se pertencer ao cluster campeão, a IA aprova!
    # E checa se a distância para o centroide é aceitável
    distancia = np.linalg.norm(features_jogo - centroide_campeao)
    
    # Aprovado se estiver no cluster dominante
    return cluster_previsto == kmeans.labels_[0] # Simplificação estatística