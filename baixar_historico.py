import requests
import sqlite3
import urllib3
import time
from src.database import obter_conexao

# Desativa os avisos de segurança no terminal
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

API_URL = "https://servicebus2.caixa.gov.br/portaldeloterias/api/"

def sincronizar_historico_total(loteria):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    print(f"[*] A verificar o último concurso oficial da {loteria.upper()}...")
    try:
        # Pede à Caixa qual é o número do último sorteio
        res_latest = requests.get(f"{API_URL}{loteria}", headers=headers, verify=False, timeout=10)
        ultimo_oficial = res_latest.json().get('numero')
        print(f"[*] O último concurso realizado foi o {ultimo_oficial}.")
    except Exception as e:
        print(f"[!] Erro ao ligar à Caixa: {e}")
        return

    conn = obter_conexao()
    cursor = conn.cursor()

    # 1. Descobrir quais os concursos que JÁ TEMOS na base de dados
    cursor.execute(f"SELECT id_concurso FROM resultados WHERE loteria = '{loteria}'")
    concursos_salvos = {row[0] for row in cursor.fetchall()}

    # 2. Descobrir quais os concursos que FALTAM baixar
    todos_concursos = set(range(1, ultimo_oficial + 1))
    # Vamos baixar do mais recente para o mais antigo (reverse=True)
    concursos_faltantes = sorted(list(todos_concursos - concursos_salvos), reverse=True)

    if not concursos_faltantes:
        print("\n[V] O seu banco de dados já está 100% ATUALIZADO com todos os concursos!")
        conn.close()
        return

    print(f"[*] Faltam baixar {len(concursos_faltantes)} concursos. A iniciar transferência...")
    print("[!] ATENÇÃO: Como são muitos, pode demorar alguns minutos. Pode parar (Ctrl+C) a qualquer momento e continuar mais tarde.\n")

    baixados = 0
    for concurso in concursos_faltantes:
        url = f"{API_URL}{loteria}/{concurso}"
        try:
            response = requests.get(url, headers=headers, verify=False, timeout=15)
            if response.status_code == 200:
                dados = response.json()
                data_sorteio = dados.get('dataApuracao')
                
                # Tratamento das dezenas (Remove zeros à esquerda: "05" -> "5")
                dezenas_raw = dados.get('listaDezenas', [])
                dezenas = ",".join([str(int(d)) for d in dezenas_raw])
                
                # Tratamento dos prémios
                rateios = dados.get('listaRateioPremio', [])
                valor_premio = rateios[0].get('valorPremio', 0) if rateios else 0
                acumulado = 1 if dados.get('acumulado') else 0
                
                cursor.execute('''
                    INSERT INTO resultados (id_concurso, loteria, data_sorteio, dezenas, premiacao_principal, acumulado)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (concurso, loteria, data_sorteio, dezenas, valor_premio, acumulado))
                conn.commit()
                
                print(f"[+] Baixado: {loteria.upper()} {concurso} ({data_sorteio}) - Sorteio: {dezenas}")
                baixados += 1
            else:
                print(f"[!] Erro no concurso {concurso} (Status {response.status_code})")
            
            # PAUSA DE 1 SEGUNDO: Regra de ouro para a Caixa não bloquear o seu IP!
            time.sleep(1)
            
        except Exception as e:
            print(f"[!] Erro ao tentar baixar o concurso {concurso}: {e}")
            time.sleep(3) # Pausa maior se der erro de internet

    conn.close()
    print(f"\n[V] Concluído! {baixados} concursos foram adicionados ao Cérebro da IA.")

if __name__ == "__main__":
    print("--- SINCRONIZADOR TOTAL DE LOTERIAS ---")
    sincronizar_historico_total('megasena')