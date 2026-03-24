import pandas as pd
from .database import obter_conexao

def carregar_dados(loteria):
    """
    SEGURANÇA: Utilização de params=(loteria,) no Pandas para delegar a sanitização ao DB-API.
    """
    conn = obter_conexao()
    df = pd.read_sql_query(
        "SELECT dezenas FROM resultados WHERE loteria = ? ORDER BY id_concurso DESC LIMIT 50", 
        conn, params=(loteria,)
    )
    conn.close()

    if not df.empty:
        df['dezenas_list'] = df['dezenas'].apply(lambda x: [int(d) for d in x.split(',')])
    
    return df

def obter_estatisticas_completas(loteria):
    conn = obter_conexao()
    df = pd.read_sql_query(
        "SELECT dezenas, id_concurso FROM resultados WHERE loteria = ? ORDER BY id_concurso DESC", 
        conn, params=(loteria,)
    )
    conn.close()

    if df.empty:
        return None, None

    todas_dezenas = []
    for lista in df['dezenas']:
        todas_dezenas.extend([int(d) for d in lista.split(',')])
    
    total_concursos = len(df)
    freq = pd.Series(todas_dezenas).value_counts().sort_index().reset_index()
    freq.columns = ['Número', 'Sorteios']
    freq['Frequência (%)'] = ((freq['Sorteios'] / total_concursos) * 100).round(2)
    freq = freq.sort_values(by='Sorteios', ascending=False)

    max_num = {
        "megasena": 60, "lotofacil": 25, "quina": 80,
        "lotomania": 99, "duplasena": 50, "timemania": 80
    }.get(loteria, 60)
    
    atraso_lista = []
    ultimo_concurso = df['id_concurso'].max()
    range_inicio = 0 if loteria == "lotomania" else 1

    for i in range(range_inicio, max_num + 1):
        num_str = str(i).zfill(2)
        # SEGURANÇA: Regex controlada internamente, impossível ser injetada pelo usuário
        sub_df = df[df['dezenas'].str.contains(fr'\b{num_str}\b', regex=True)]
        
        if not sub_df.empty:
            atraso = ultimo_concurso - sub_df['id_concurso'].max()
        else:
            atraso = total_concursos
            
        numero_exibicao = "00" if loteria == "lotomania" and i == 0 else i
        atraso_lista.append({"Número": numero_exibicao, "Atraso": atraso})
    
    df_atraso = pd.DataFrame(atraso_lista).sort_values(by="Atraso", ascending=False)
    
    return freq, df_atraso