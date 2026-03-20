import random
import math
import pandas as pd
from .database import obter_conexao
from .analyzer import carregar_dados

def calcular_custo_jogos(loteria, qtd_jogos, qtd_dezenas):
    """
    Calcula o custo real baseado na tabela oficial da CAIXA.
    Lê o preço base e o mínimo de dezenas do banco de dados.
    """
    conn = obter_conexao()
    cursor = conn.cursor()
    cursor.execute("SELECT preco_base, dez_min FROM tarifas WHERE loteria = ?", (loteria,))
    dados = cursor.fetchone()
    conn.close()

    if not dados:
        return 0.0

    preco_base, dez_min = dados
    
    # Se o usuário tentar marcar menos que o mínimo permitido
    if qtd_dezenas < dez_min:
        return 0.0

    # Fórmula de Combinação Simples C(n, p) usada pela CEF
    # n = dezenas marcadas | p = dezenas da aposta mínima
    num_combinacoes = math.comb(qtd_dezenas, dez_min)
    
    # Custo = (Total de combinações simples dentro do jogo) * (Preço da aposta simples)
    return (num_combinacoes * preco_base) * qtd_jogos

def tem_sequencia_longa(jogo, max_consecutivos=3):
    """Evita jogos com muitos números seguidos (ex: 01, 02, 03, 04)."""
    sequencia_atual = 1
    for i in range(1, len(jogo)):
        if jogo[i] == jogo[i-1] + 1:
            sequencia_atual += 1
            if sequencia_atual > max_consecutivos:
                return True
        else:
            sequencia_atual = 1
    return False

def sugerir_jogo(loteria, qtd_jogos=1, dezenas_por_jogo=None):
    """Gera jogos baseados em frequência e filtros de paridade/sequência."""
    conn = obter_conexao()
    cursor = conn.cursor()
    cursor.execute("SELECT dez_min, dez_max FROM tarifas WHERE loteria = ?", (loteria,))
    limites = cursor.fetchone()
    conn.close()

    if not limites:
        return []

    min_dez, max_dez = limites
    qtd_dezenas = dezenas_por_jogo if dezenas_por_jogo else min_dez
    
    # Configuração de limites do volante
    total_numeros = {"megasena": 60, "lotofacil": 25, "quina": 80}.get(loteria, 60)
    
    df = carregar_dados(loteria)
    
    # Se houver dados, prioriza os números "quentes", senão usa o volante todo
    if df is not None and not df.empty:
        todas = [n for lista in df['dezenas_list'] for n in lista]
        pool = pd.Series(todas).value_counts().index.tolist()
    else:
        pool = list(range(1, total_numeros + 1))

    # Garantia de amostragem
    if len(pool) < qtd_dezenas:
        pool = list(range(1, total_numeros + 1))

    jogos_gerados = []
    par_ideal = qtd_dezenas // 2

    for _ in range(qtd_jogos):
        jogo_encontrado = False
        for _ in range(300): # Tentativas de encontrar jogo equilibrado
            sugestao = sorted(random.sample(pool, qtd_dezenas))
            pares = len([n for n in sugestao if n % 2 == 0])
            
            # Filtros de IA
            if pares in [par_ideal, par_ideal + 1]:
                if not tem_sequencia_longa(sugestao):
                    jogos_gerados.append(sugestao)
                    jogo_encontrado = True
                    break
        
        if not jogo_encontrado:
            jogos_gerados.append(sorted(random.sample(pool, qtd_dezenas)))
            
    return jogos_gerados