import sqlite3

def obter_conexao():
    """
    SEGURANÇA: Retorna a conexão com restrições pragmáticas de integridade ativadas.
    O parâmetro check_same_thread=False é exigido pelo Streamlit, mas as transações 
    são isoladas via gerenciamento de cursores locais.
    """
    conn = sqlite3.connect('loterias_caixa.db', check_same_thread=False)
    # Ativa verificação estrita de chaves estrangeiras para evitar dados órfãos/corrompidos
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def inicializar_bd():
    conn = obter_conexao()
    cursor = conn.cursor()
    
    # Criação de tabelas utilizando prepared statements estruturais
    cursor.execute('''CREATE TABLE IF NOT EXISTS resultados (
        loteria TEXT, id_concurso INTEGER, data_sorteio TEXT, dezenas TEXT, 
        premiacao_principal REAL, local_sorteio TEXT, acumulou INTEGER, 
        PRIMARY KEY (loteria, id_concurso))''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS apostas_usuario (
        id INTEGER PRIMARY KEY AUTOINCREMENT, loteria TEXT, 
        concurso_alvo INTEGER, dezenas_jogadas TEXT)''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS tarifas (
        loteria TEXT PRIMARY KEY, preco_base REAL, dez_min INTEGER, dez_max INTEGER)''')
    
    # Loterias mantidas fielmente
    tarifas = [
        ('megasena', 5.0, 6, 20),
        ('lotofacil', 3.0, 15, 20),
        ('quina', 2.5, 5, 15),
        ('lotomania', 3.0, 50, 50),
        ('duplasena', 2.5, 6, 15),
        ('timemania', 3.5, 10, 10)
    ]
    
    # SEGURANÇA: Inserção de dados paramétrica para evitar SQLi
    cursor.executemany('INSERT OR IGNORE INTO tarifas VALUES (?, ?, ?, ?)', tarifas)
    
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
    # SEGURANÇA: Uso obrigatório de tuple (status,) protegendo contra injeção direta
    conn.execute("UPDATE controle_sessao SET status=? WHERE id=1", (status,))
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
    """
    Remove todas as apostas salvas pelo usuário para uma loteria específica.
    """
    conn = obter_conexao()
    conn.execute("DELETE FROM apostas_usuario WHERE loteria = ?", (loteria,))
    conn.commit()
    conn.close()