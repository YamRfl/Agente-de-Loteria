import math
import secrets # SEGURANÇA: Módulo de criptografia forte para geração de números imprevisíveis
from .analyzer import carregar_dados
from .database import obter_conexao

def calcular_custo_jogos(loteria, qtd_jogos, dezenas_por_jogo):
    """
    Calcula o custo real considerando desdobramentos (Combinatória Matemática).
    """
    conn = obter_conexao()
    # SEGURANÇA: Query parametrizada.
    res = conn.execute("SELECT preco_base, dez_min FROM tarifas WHERE loteria = ?", (loteria,)).fetchone()
    conn.close()
    
    if not res:
        return 0.0
        
    preco_base, min_dezenas = res
    
    # SEGURANÇA (Prevenção OOM): Uso da biblioteca C nativa math.comb para cálculo otimizado.
    try:
        multiplicador = math.comb(dezenas_por_jogo, min_dezenas)
    except ValueError:
        multiplicador = 1 # Fallback de segurança se houver erro matemático
        
    return (preco_base * multiplicador) * qtd_jogos

def sugerir_jogo(loteria, qtd_jogos, dezenas_por_jogo):
    """
    Gera apostas seguras e filtradas (paridade e sequências).
    """
    # Limites definidos para as loterias conhecidas
    limites = {
        "megasena": 60, "lotofacil": 25, "quina": 80, 
        "lotomania": 99, "duplasena": 50, "timemania": 80
    }
    max_num = limites.get(loteria, 60)
    
    # A lotomania começa do 00, o restante do 01
    offset = 0 if loteria == "lotomania" else 1
    pool_de_numeros = list(range(offset, max_num + 1))
    
    # Cria uma instância segura de aleatoriedade
    # SEGURANÇA: SystemRandom utiliza o /dev/urandom ou CryptGenRandom do SO.
    gerador_seguro = secrets.SystemRandom()
    
    jogos_gerados = []
    
    for _ in range(qtd_jogos):
        # SEGURANÇA (Anti-DoS): Evita loops infinitos se os filtros forem muito restritos
        tentativas = 0
        tentativas_maximas = 2000 
        
        while tentativas < tentativas_maximas:
            # Seleção criptográfica sem repetição
            jogo = gerador_seguro.sample(pool_de_numeros, k=dezenas_por_jogo)
            jogo.sort()
            
            # --- FILTRO 1: PARIDADE (Equilíbrio Par/Ímpar) ---
            pares = sum(1 for n in jogo if n % 2 == 0)
            impares = len(jogo) - pares
            # Exige que a diferença entre pares e ímpares não seja absurda (ex: tudo par)
            if abs(pares - impares) > (dezenas_por_jogo / 2 + 1):
                tentativas += 1
                continue
                
            # --- FILTRO 2: SEQUÊNCIAS ---
            # Evita jogos com mais de 3 números seguidos (ex: 4, 5, 6, 7)
            sequencias_longas = False
            for i in range(len(jogo) - 3):
                if jogo[i] == jogo[i+1]-1 == jogo[i+2]-2 == jogo[i+3]-3:
                    sequencias_longas = True
                    break
                    
            if sequencias_longas:
                tentativas += 1
                continue
                
            # Adiciona ao carrinho e encerra a tentativa para este jogo
            if jogo not in jogos_gerados:
                jogos_gerados.append(jogo)
                break
                
            tentativas += 1
            
        # Fallback de Segurança: Se não encontrar um jogo ideal após 2000 tentativas, 
        # gera um puramente aleatório para não travar a aplicação (Circuit Breaker).
        if tentativas >= tentativas_maximas:
            jogo_fallback = gerador_seguro.sample(pool_de_numeros, k=dezenas_por_jogo)
            jogo_fallback.sort()
            jogos_gerados.append(jogo_fallback)
            
    return jogos_gerados