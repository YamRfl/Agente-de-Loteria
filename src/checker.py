import pandas as pd
from .database import obter_conexao

def conferir_resultados(loteria):
    """
    Compara as apostas do usuário salvas no banco com os resultados reais 
    que foram baixados da CAIXA.
    """
    conn = obter_conexao()
    
    # 1. Busca as apostas do usuário para a loteria selecionada
    query_apostas = "SELECT concurso_alvo, dezenas_jogadas FROM apostas_usuario WHERE loteria = ?"
    df_apostas = pd.read_sql_query(query_apostas, conn, params=(loteria,))
    
    # 2. Busca os resultados reais já baixados no banco
    query_resultados = "SELECT id_concurso, dezenas FROM resultados WHERE loteria = ?"
    df_resultados = pd.read_sql_query(query_resultados, conn, params=(loteria,))
    
    conn.close()

    if df_apostas.empty:
        return None

    relatorio = []

    for _, aposta in df_apostas.iterrows():
        concurso = aposta['concurso_alvo']
        jogadas = set(aposta['dezenas_jogadas'].split(','))
        
        # Procura o resultado oficial desse concurso no banco
        res_oficial = df_resultados[df_resultados['id_concurso'] == concurso]
        
        if not res_oficial.empty:
            sorteadas = set(res_oficial.iloc[0]['dezenas'].split(','))
            acertos = jogadas.intersection(sorteadas)
            qtd_acertos = len(acertos)
            
            relatorio.append({
                "Concurso": concurso,
                "Suas Dezenas": aposta['dezenas_jogadas'],
                "Sorteadas": res_oficial.iloc[0]['dezenas'],
                "Acertos": qtd_acertos,
                "Números Acertados": ",".join(sorted(list(acertos))) if acertos else "-"
            })
        else:
            # Caso o concurso ainda não tenha sido sorteado ou baixado
            relatorio.append({
                "Concurso": concurso,
                "Suas Dezenas": aposta['dezenas_jogadas'],
                "Sorteadas": "Aguardando sorteio...",
                "Acertos": 0,
                "Números Acertados": "N/A"
            })

    return pd.DataFrame(relatorio)