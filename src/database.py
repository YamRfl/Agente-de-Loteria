import sqlite3

def obter_conexao():
    return sqlite3.connect('loterias_caixa.db', check_same_thread=False)

def inicializar_bd():
    conn = obter_conexao()
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS resultados (
        loteria TEXT, id_concurso INTEGER, data_sorteio TEXT, dezenas TEXT, 
        premiacao_principal REAL, local_sorteio TEXT, acumulou INTEGER, 
        PRIMARY KEY (loteria, id_concurso))''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS apostas_usuario (
        id INTEGER PRIMARY KEY AUTOINCREMENT, loteria TEXT, 
        concurso_alvo INTEGER, dezenas_jogadas TEXT)''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS tarifas (
        loteria TEXT PRIMARY KEY, preco_base REAL, dez_min INTEGER, dez_max INTEGER)''')
    
    # Tabela de controle para o botão PARAR
    cursor.execute('CREATE TABLE IF NOT EXISTS controle_sessao (id INTEGER PRIMARY KEY, status TEXT)')
    cursor.execute('INSERT OR IGNORE INTO controle_sessao (id, status) VALUES (1, "ok")')
    
    conn.commit()
    conn.close()

def status_parada():
    conn = obter_conexao()
    res = conn.execute("SELECT status FROM controle_sessao WHERE id=1").fetchone()[0]
    conn.close()
    return res == "parar"

def definir_parada(status):
    conn = obter_conexao()
    conn.execute("UPDATE controle_sessao SET status=? WHERE id=1", (status,))
    conn.commit()
    conn.close()

def obter_ultimo_concurso_db(loteria):
    conn = obter_conexao()
    res = conn.execute("SELECT MAX(id_concurso) FROM resultados WHERE loteria = ?", (loteria,)).fetchone()[0]
    conn.close()
    return res if res else 0