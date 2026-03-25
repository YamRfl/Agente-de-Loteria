import math
import secrets
from .analyzer import carregar_dados
from .database import obter_conexao
from .ml_engine import treinar_modelo_loteria, jogo_aprovado_pela_ia

def calcular_custo_jogos(loteria, qtd_jogos, dezenas_por_jogo):
    """Calcula o custo real considerando desdobramentos matemáticos."""
    conn = obter_conexao()
    res = conn.execute("SELECT preco_base, dez_min FROM tarifas WHERE loteria = ?", (loteria,)).fetchone()
    conn.close()
    
    if not res:
        return 0.0
        
    preco_base, min_dezenas = res
    
    try:
        multiplicador = math.comb(dezenas_por_jogo, min_dezenas)
    except ValueError:
        multiplicador = 1
        
    return (preco_base * multiplicador) * qtd_jogos

def sugerir_jogo(loteria, qtd_jogos, dezenas_por_jogo, usar_ia=False):
    """Gera apostas seguras. Se usar_ia=True, aplica o modelo preditivo K-Means."""
    limites = {
        "megasena": 60, "lotofacil": 25, "quina": 80, 
        "lotomania": 99, "duplasena": 50, "timemania": 80
    }
    max_num = limites.get(loteria, 60)
    offset = 0 if loteria == "lotomania" else 1
    pool_de_numeros = list(range(offset, max_num + 1))
    
    gerador_seguro = secrets.SystemRandom()
    jogos_gerados = []
    
    modelo_ia = None
    cluster_campeao = None
    
    # Treina a IA uma única vez antes de começar a gerar os jogos
    if usar_ia:
        resultado_ia = treinar_modelo_loteria(loteria)
        if resultado_ia:
            modelo_ia, cluster_campeao = resultado_ia

    for _ in range(qtd_jogos):
        tentativas = 0
        tentativas_maximas = 3000 
        jogo_valido = False
        
        while tentativas < tentativas_maximas:
            jogo = gerador_seguro.sample(pool_de_numeros, k=dezenas_por_jogo)
            jogo.sort()
            
            # --- FILTRO 1: PARIDADE ---
            pares = sum(1 for n in jogo if n % 2 == 0)
            if abs(pares - (len(jogo) - pares)) > (dezenas_por_jogo / 2 + 1):
                tentativas += 1
                continue
                
            # --- FILTRO 2: SEQUÊNCIAS ---
            sequencias_longas = False
            for i in range(len(jogo) - 3):
                if jogo[i] == jogo[i+1]-1 == jogo[i+2]-2 == jogo[i+3]-3:
                    sequencias_longas = True
                    break
            if sequencias_longas:
                tentativas += 1
                continue
                
            # --- FILTRO 3: MACHINE LEARNING (K-MEANS) ---
            if usar_ia and modelo_ia is not None:
                if not jogo_aprovado_pela_ia(jogo, modelo_ia, cluster_campeao):
                    tentativas += 1
                    continue # Rejeita o jogo se não tiver o "DNA" vitorioso
            
            if jogo not in jogos_gerados:
                jogos_gerados.append(jogo)
                jogo_valido = True
                break
                
            tentativas += 1
            
        # Circuit Breaker de Segurança
        if not jogo_valido:
            jogo_fallback = gerador_seguro.sample(pool_de_numeros, k=dezenas_por_jogo)
            jogo_fallback.sort()
            jogos_gerados.append(jogo_fallback)
            
    return jogos_gerados