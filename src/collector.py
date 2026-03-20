import requests
import time
from .database import obter_conexao, obter_ultimo_concurso_db

def atualizar_resultados(loteria, barra_progresso=None):
    """
    Atualiza os resultados faltantes.
    barra_progresso: Objeto st.progress enviado pelo app.py
    """
    ultimo_db = obter_ultimo_concurso_db(loteria)
    
    try:
        # Busca o número do concurso mais recente na API
        url_recente = f"https://servicebus2.caixa.gov.br/portaldeloterias/api/{loteria}"
        res_api = requests.get(url_recente, timeout=10, verify=False).json()
        ultimo_oficial = res_api['numero']
    except Exception as e:
        print(f"Erro ao conectar com a API: {e}")
        return

    # Se já estiver atualizado, encerra
    if ultimo_db >= ultimo_oficial:
        return

    conn = obter_conexao()
    total_faltante = ultimo_oficial - ultimo_db
    
    # Loop de atualização incremental
    for i, n in enumerate(range(ultimo_db + 1, ultimo_oficial + 1)):
        try:
            # Atualiza a barra de incremento visual no Streamlit se ela existir
            if barra_progresso:
                percentual = (i + 1) / total_faltante
                barra_progresso.progress(percentual, text=f"Sincronizando concurso {n} de {ultimo_oficial}")

            url = f"https://servicebus2.caixa.gov.br/portaldeloterias/api/{loteria}/{n}"
            r = requests.get(url, timeout=10, verify=False).json()
            
            # Insere no banco de dados
            conn.execute('''
                INSERT INTO resultados (
                    loteria, id_concurso, data_sorteio, dezenas, 
                    premiacao_principal, local_sorteio, acumulou
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                loteria, r['numero'], r['dataApuracao'], ",".join(r['listaDezenas']),
                r['listaRateioPremio'][0]['valorPremio'], r['localSorteio'], 
                1 if r['acumulado'] else 0
            ))
            conn.commit()
            
            # Pequeno delay para suavizar a animação da barra e evitar bloqueio de IP
            time.sleep(0.05)
            
        except Exception as e:
            print(f"Erro no concurso {n}: {e}")
            continue
    
    conn.close()