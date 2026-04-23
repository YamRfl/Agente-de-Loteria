import requests
import time
from .database import obter_conexao, obter_ultimo_concurso_db

def atualizar_resultados(loteria, barra_progresso=None):
    ultimo_banco = obter_ultimo_concurso_db(loteria)
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    url_base = f"https://loteriascaixa-api.herokuapp.com/api/{loteria}"
    try:
        response = requests.get(f"{url_base}/latest", headers=headers, timeout=10)
        if response.status_code != 200:
            return
        
        ultimo_oficial = response.json().get('concurso', ultimo_banco)
        
        if ultimo_banco >= ultimo_oficial:
            if barra_progresso: barra_progresso.progress(1.0, text="Banco de dados já está atualizado!")
            return
            
        conn = obter_conexao()
        total_para_baixar = ultimo_oficial - ultimo_banco
        atual = 0

        for concurso in range(ultimo_banco + 1, ultimo_oficial + 1):
            res = requests.get(f"{url_base}/{concurso}", headers=headers, timeout=10)
            if res.status_code == 200:
                dados = res.json()
                dezenas_str = ",".join([str(int(d)) for d in dados.get('dezenas', [])])
                
                # Ignora trevos da milionária ou meses do dia de sorte para matriz principal
                conn.execute('''
                    INSERT OR IGNORE INTO resultados 
                    (loteria, id_concurso, data_sorteio, dezenas, premiacao_principal, local_sorteio, acumulou)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    loteria, dados.get('concurso'), dados.get('data'), dezenas_str,
                    0.0, dados.get('local', 'SÃO PAULO, SP'), 1 if dados.get('acumulou') else 0
                ))
                conn.commit()
            
            atual += 1
            if barra_progresso:
                progresso = min(atual / total_para_baixar, 1.0)
                barra_progresso.progress(progresso, text=f"Baixando concurso {concurso}...")
            time.sleep(0.5) 
            
        conn.close()
    except Exception as e:
        print(f"Erro ao sincronizar {loteria}: {e}")