import sqlite3

def obter_conexao():
    conn = sqlite3.connect('loterias_caixa.db', check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def inicializar_bd():
    conn = obter_conexao()
    cursor = conn.cursor()
    
    # Histórico de Sorteios
    cursor.execute('''CREATE TABLE IF NOT EXISTS resultados (
        loteria TEXT, id_concurso INTEGER, data_sorteio TEXT, dezenas TEXT, 
        premiacao_principal REAL, local_sorteio TEXT, acumulou INTEGER, 
        PRIMARY KEY (loteria, id_concurso))''')
    
    # Apostas dos Usuários
    cursor.execute('''CREATE TABLE IF NOT EXISTS apostas_usuario (
        id INTEGER PRIMARY KEY AUTOINCREMENT, loteria TEXT, 
        concurso_alvo INTEGER, dezenas_jogadas TEXT)''')
    
    # Configuração de Tarifas e Limites
    cursor.execute('''CREATE TABLE IF NOT EXISTS tarifas (
        loteria TEXT PRIMARY KEY, preco_base REAL, dez_min INTEGER, dez_max INTEGER)''')
    
    tarifas = [
        ('megasena', 5.0, 6, 20),
        ('lotofacil', 3.0, 15, 20),
        ('quina', 2.5, 5, 15),
        ('lotomania', 3.0, 50, 50),
        ('duplasena', 2.5, 6, 15),
        ('timemania', 3.5, 10, 10),
        ('maismilionaria', 6.0, 6, 12),
        ('diadesorte', 2.5, 7, 15)
    ]
    cursor.executemany('INSERT OR IGNORE INTO tarifas VALUES (?, ?, ?, ?)', tarifas)
    
    # Controle de Sessão
    cursor.execute('CREATE TABLE IF NOT EXISTS controle_sessao (id INTEGER PRIMARY KEY, status TEXT)')
    cursor.execute('INSERT OR IGNORE INTO controle_sessao (id, status) VALUES (1, "ok")')
    
    conn.commit()
    conn.close()

def obter_ultimo_concurso_db(loteria):
    conn = obter_conexao()
    res = conn.execute("SELECT MAX(id_concurso) FROM resultados WHERE loteria = ?", (loteria,)).fetchone()[0]
    conn.close()
    return res if res else 0

def atualizar_preco_banco(loteria, preco, dez_max):
    conn = obter_conexao()
    conn.execute("UPDATE tarifas SET preco_base = ?, dez_max = ? WHERE loteria = ?", (preco, dez_max, loteria))
    conn.commit()
    conn.close()

def limpar_apostas_banco(loteria):
    conn = obter_conexao()
    conn.execute("DELETE FROM apostas_usuario WHERE loteria = ?", (loteria,))
    conn.commit()
    conn.close()