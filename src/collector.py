import requests
import time
from .database import obter_conexao, obter_ultimo_concurso_db

def atualizar_resultados(loteria, barra_progresso=None):
    ultimo_banco = obter_ultimo_concurso_db(loteria)
    headers = {'User-Agent': 'Mozilla/5.0'}
    url_base = f"https://loteriascaixa-api.herokuapp.com/api/{loteria}"

    try:
        # 1. Verifica o último concurso oficial
        res_latest = requests.get(f"{url_base}/latest", headers=headers, timeout=10)
        if res_latest.status_code != 200: return
        ultimo_oficial = res_latest.json().get('concurso', ultimo_banco)

        if ultimo_banco >= ultimo_oficial:
            if barra_progresso: barra_progresso.progress(1.0, text=f"{loteria.upper()} já atualizada!")
            return

        conn = obter_conexao()
        defasagem = ultimo_oficial - ultimo_banco

        # 2. CARGA RÁPIDA (Batch) - Se faltam mais de 10 concursos, puxa a base de dados inteira de uma vez
        if defasagem > 10:
            if barra_progresso: barra_progresso.progress(0.3, text=f"Baixando carga em lote de {loteria.upper()}...")
            res_all = requests.get(url_base, headers=headers, timeout=30)
            
            if res_all.status_code == 200:
                todos_sorteios = res_all.json()
                novos_dados = []

                # Filtra apenas o que não temos no banco
                for dados in todos_sorteios:
                    if dados.get('concurso') > ultimo_banco:
                        dezenas_str = ",".join([str(int(d)) for d in dados.get('dezenas', [])])
                        novos_dados.append((
                            loteria, dados.get('concurso'), dados.get('data'), dezenas_str,
                            0.0, dados.get('local', 'SÃO PAULO, SP'), 1 if dados.get('acumulou') else 0
                        ))

                if barra_progresso: barra_progresso.progress(0.7, text=f"Gravando {len(novos_dados)} sorteios...")
                
                # Injeção em massa no banco de dados (Altíssima Performance)
                conn.executemany('''
                    INSERT OR IGNORE INTO resultados
                    (loteria, id_concurso, data_sorteio, dezenas, premiacao_principal, local_sorteio, acumulou)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', novos_dados)
                conn.commit()

        # 3. CARGA DELTA (Sequencial) - Se for apenas a atualização do dia
        else:
            atual = 0
            for concurso in range(ultimo_banco + 1, ultimo_oficial + 1):
                res = requests.get(f"{url_base}/{concurso}", headers=headers, timeout=10)
                if res.status_code == 200:
                    dados = res.json()
                    dezenas_str = ",".join([str(int(d)) for d in dados.get('dezenas', [])])
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
                    progresso = min(atual / defasagem, 1.0)
                    barra_progresso.progress(progresso, text=f"Sincronizando {concurso} de {loteria.upper()}...")
                time.sleep(0.3)

        if barra_progresso: barra_progresso.progress(1.0, text=f"{loteria.upper()} concluída!")
        conn.close()
    except Exception as e:
        print(f"Erro ao sincronizar {loteria}: {e}")

def sincronizar_todas_loterias(barra_progresso=None, texto_status=None):
    """Sincroniza as 8 modalidades de loteria de uma só vez usando a lógica Batch."""
    loterias = ["megasena", "lotofacil", "quina", "lotomania", "duplasena", "timemania", "maismilionaria", "diadesorte"]
    total = len(loterias)
    for i, loteria in enumerate(loterias):
        if texto_status: texto_status.caption(f"⏳ Processando **{loteria.upper()}** ({i+1}/{total})...")
        atualizar_resultados(loteria)
        if barra_progresso: barra_progresso.progress((i + 1) / total)