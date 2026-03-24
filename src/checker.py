import pandas as pd
from .database import obter_conexao

def conferir_resultados(loteria):
    """
    Compara as apostas registradas pelo usuário com o banco oficial da Caixa.
    """
    conn = obter_conexao()
    
    # SEGURANÇA: Prevenção absoluta de SQL Injection utilizando query parametrizada.
    query_apostas = "SELECT concurso_alvo, dezenas_jogadas FROM apostas_usuario WHERE loteria = ?"
    apostas_df = pd.read_sql_query(query_apostas, conn, params=(loteria,))
    
    if apostas_df.empty:
        conn.close()
        return None

    resultados_formatados = []
    
    # Itera sobre os jogos salvos do usuário
    for _, aposta in apostas_df.iterrows():
        concurso = aposta['concurso_alvo']
        # Converte a string salva "01, 02, 03" para um Set de inteiros para comparação rápida
        dezenas_jogadas_set = set(map(int, aposta['dezenas_jogadas'].replace(' ', '').split(',')))
        
        # SEGURANÇA: Novamente, uso rigoroso de parâmetros (?, ?) para o SELECT interno
        query_oficial = "SELECT dezenas FROM resultados WHERE loteria = ? AND id_concurso = ?"
        resultado_oficial_df = pd.read_sql_query(query_oficial, conn, params=(loteria, concurso))
        
        if not resultado_oficial_df.empty:
            # Converte as dezenas sorteadas para um Set
            sorteio_oficial_str = resultado_oficial_df.iloc[0]['dezenas']
            dezenas_oficiais_set = set(map(int, sorteio_oficial_str.split(',')))
            
            # Cálculo de Intersecção (Acertos)
            acertos = dezenas_jogadas_set.intersection(dezenas_oficiais_set)
            
            resultados_formatados.append({
                "Concurso": concurso,
                "Seu Jogo": aposta['dezenas_jogadas'],
                "Sorteio Oficial": sorteio_oficial_str,
                "Acertos (Qtd)": len(acertos),
                "Números Acertados": ", ".join(map(str, sorted(acertos))) if acertos else "Nenhum acerto"
            })
        else:
            # Caso o concurso alvo do usuário ainda não tenha sido sorteado/baixado
            resultados_formatados.append({
                "Concurso": concurso,
                "Seu Jogo": aposta['dezenas_jogadas'],
                "Sorteio Oficial": "Sorteio Pendente",
                "Acertos (Qtd)": "-",
                "Números Acertados": "-"
            })

    conn.close()
    
    # Retorna o DataFrame que o Streamlit irá renderizar na tela
    return pd.DataFrame(resultados_formatados)