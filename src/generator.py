import math
import secrets
from .analyzer import carregar_dados
from .database import obter_conexao
from .ml_engine import treinar_modelo_loteria, jogo_aprovado_pela_ia, eh_primo

# Constante Matemática
FIBONACCI = {1, 2, 3, 5, 8, 13, 21, 34, 55, 89}

def calcular_custo_jogos(loteria, qtd_jogos, dezenas_por_jogo):
    """Calcula o custo real considerando desdobramentos matemáticos."""
    conn = obter_conexao()
    res = conn.execute("SELECT preco_base, dez_min FROM tarifas WHERE loteria = ?", (loteria,)).fetchone()
    conn.close()
    if not res: return 0.0
    preco_base, min_dezenas = res
    try:
        multiplicador = math.comb(dezenas_por_jogo, min_dezenas)
    except ValueError:
        multiplicador = 1
    return (preco_base * multiplicador) * qtd_jogos

def obter_ultimo_sorteio(loteria):
    """Busca o último concurso no banco para o filtro de dezenas repetidas."""
    conn = obter_conexao()
    res = conn.execute("SELECT dezenas FROM resultados WHERE loteria = ? ORDER BY id_concurso DESC LIMIT 1", (loteria,)).fetchone()
    conn.close()
    if res:
        return set(int(x) for x in res[0].split(','))
    return set()

def sugerir_jogo(loteria, qtd_jogos, dezenas_por_jogo, usar_ia=False, 
                 filtro_soma=(0, 1000), filtro_pares=(0, 100), filtro_primos=(0, 100),
                 filtro_fibo=(0, 100), filtro_mult3=(0, 100), filtro_moldura=(0, 100),
                 filtro_repetidas=(0, 100), limite_linha=10, limite_coluna=10):
    
    limites = {"megasena": 60, "lotofacil": 25, "quina": 80, "lotomania": 99, "duplasena": 50, "timemania": 80}
    max_num = limites.get(loteria, 60)
    offset = 0 if loteria == "lotomania" else 1
    pool_de_numeros = list(range(offset, max_num + 1))
    
    # Mapeamento da Grade (Grid) do volante para Linhas, Colunas e Moldura
    cols = 5 if loteria == "lotofacil" else 10
    rows = max_num // cols if loteria != "lotomania" else 10

    def get_grid_pos(n):
        # Lotomania trata o 00 como posição 100 no volante
        val = 100 if n == 0 and loteria == "lotomania" else n
        r = (val - 1) // cols
        c = (val - 1) % cols
        return r, c

    def is_moldura(r, c):
        return r == 0 or r == rows - 1 or c == 0 or c == cols - 1

    ultimo_sorteio = obter_ultimo_sorteio(loteria)
    gerador_seguro = secrets.SystemRandom()
    jogos_gerados = []
    
    modelo_ia = None
    cluster_campeao = None
    if usar_ia:
        resultado_ia = treinar_modelo_loteria(loteria)
        if resultado_ia:
            modelo_ia, cluster_campeao = resultado_ia

    for _ in range(qtd_jogos):
        tentativas = 0
        tentativas_maximas = 5000  # Aumentado devido à rigidez de 8 filtros combinados
        jogo_valido = False
        
        while tentativas < tentativas_maximas:
            jogo = gerador_seguro.sample(pool_de_numeros, k=dezenas_por_jogo)
            jogo.sort()
            
            # --- 1. Filtros Matemáticos e Quantitativos ---
            if not (filtro_soma[0] <= sum(jogo) <= filtro_soma[1]):
                tentativas += 1; continue

            if not (filtro_pares[0] <= sum(1 for n in jogo if n % 2 == 0) <= filtro_pares[1]):
                tentativas += 1; continue

            if not (filtro_primos[0] <= sum(1 for n in jogo if eh_primo(n)) <= filtro_primos[1]):
                tentativas += 1; continue
                
            if not (filtro_fibo[0] <= sum(1 for n in jogo if n in FIBONACCI) <= filtro_fibo[1]):
                tentativas += 1; continue
                
            if not (filtro_mult3[0] <= sum(1 for n in jogo if n > 0 and n % 3 == 0) <= filtro_mult3[1]):
                tentativas += 1; continue
                
            # --- 2. Filtro de Repetidas do Concurso Anterior ---
            if ultimo_sorteio:
                repetidas = len(set(jogo).intersection(ultimo_sorteio))
                if not (filtro_repetidas[0] <= repetidas <= filtro_repetidas[1]):
                    tentativas += 1; continue

            # --- 3. Filtros Espaciais (Geometria do Volante) ---
            moldura_count = 0
            linhas_count = {}
            colunas_count = {}
            grid_invalido = False

            for n in jogo:
                r, c = get_grid_pos(n)
                if is_moldura(r, c): moldura_count += 1
                
                linhas_count[r] = linhas_count.get(r, 0) + 1
                colunas_count[c] = colunas_count.get(c, 0) + 1
                
                if linhas_count[r] > limite_linha or colunas_count[c] > limite_coluna:
                    grid_invalido = True
                    break
                    
            if grid_invalido or not (filtro_moldura[0] <= moldura_count <= filtro_moldura[1]):
                tentativas += 1; continue
                
            # --- 4. Filtro Básico de Sequências ---
            sequencias_longas = False
            for i in range(len(jogo) - 3):
                if jogo[i] == jogo[i+1]-1 == jogo[i+2]-2 == jogo[i+3]-3:
                    sequencias_longas = True; break
            if sequencias_longas:
                tentativas += 1; continue
                
            # --- 5. Filtro de Machine Learning (Opcional) ---
            if usar_ia and modelo_ia is not None:
                if not jogo_aprovado_pela_ia(jogo, modelo_ia, cluster_campeao):
                    tentativas += 1; continue
            
            # Aprovação Final
            if jogo not in jogos_gerados:
                jogos_gerados.append(jogo)
                jogo_valido = True
                break
                
            tentativas += 1
            
        # Circuit Breaker: Entrega aleatório se filtros forem impossíveis
        if not jogo_valido:
            jogo_fallback = gerador_seguro.sample(pool_de_numeros, k=dezenas_por_jogo)
            jogo_fallback.sort()
            jogos_gerados.append(jogo_fallback)
            
    return jogos_gerados