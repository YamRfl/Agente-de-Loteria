import pandas as pd
from .database import obter_conexao

def conferir_resultados(loteria):
    conn = obter_conexao()
    
    apostas = pd.read_sql_query("SELECT concurso_alvo, dezenas_jogadas FROM apostas_usuario WHERE loteria = ?", conn, params=(loteria,))
    resultados = pd.read_sql_query("SELECT id_concurso, dezenas FROM resultados WHERE loteria = ?", conn, params=(loteria,))
    conn.close()

    if apostas.empty or resultados.empty:
        return None

    resultados['dezenas_set'] = resultados['dezenas'].apply(lambda x: set(int(d) for d in x.split(',')))
    
    conferencias = []
    
    for _, aposta in apostas.iterrows():
        concurso = aposta['concurso_alvo']
        dezenas_jogadas = set(int(d) for d in str(aposta['dezenas_jogadas']).split(','))
        
        resultado_oficial = resultados[resultados['id_concurso'] == concurso]
        
        if not resultado_oficial.empty:
            dezenas_oficiais = resultado_oficial.iloc[0]['dezenas_set']
            acertos = dezenas_jogadas.intersection(dezenas_oficiais)
            qtd_acertos = len(acertos)
            
            conferencias.append({
                "Concurso": concurso,
                "Suas Dezenas": ", ".join(str(d) for d in sorted(dezenas_jogadas)),
                "Sorteio Oficial": ", ".join(str(d) for d in sorted(dezenas_oficiais)),
                "Qtd. Acertos": qtd_acertos,
                "Dezenas Acertadas": ", ".join(str(d) for d in sorted(acertos)) if qtd_acertos > 0 else "-"
            })
        else:
             conferencias.append({
                "Concurso": concurso,
                "Suas Dezenas": ", ".join(str(d) for d in sorted(dezenas_jogadas)),
                "Sorteio Oficial": "Aguardando Sorteio",
                "Qtd. Acertos": "-",
                "Dezenas Acertadas": "-"
            })

    return pd.DataFrame(conferencias)