import sqlite3
import os
import hashlib
import binascii
import uuid
import re
import secrets
from datetime import datetime, timedelta
from dotenv import load_dotenv
from .database import obter_conexao
from .mailer import enviar_token_senha 

# Carrega as variáveis ocultas do arquivo .env
load_dotenv()

# Regras de validação estritas (OWASP)
EMAIL_REGEX = re.compile(r"^[\w\.-]+@[\w\.-]+\.\w+$")
SENHA_REGEX = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$")

def gerar_hash_senha(senha: str) -> str:
    salt = os.urandom(32)
    pwd_hash = hashlib.pbkdf2_hmac('sha256', senha.encode('utf-8'), salt, 210000)
    return binascii.hexlify(salt + pwd_hash).decode('ascii')

def verificar_senha(senha_armazenada: str, senha_fornecida: str) -> bool:
    try:
        salt_and_hash = binascii.unhexlify(senha_armazenada.encode('ascii'))
        salt = salt_and_hash[:32]
        stored_hash = salt_and_hash[32:]
        pwd_hash = hashlib.pbkdf2_hmac('sha256', senha_fornecida.encode('utf-8'), salt, 210000)
        return pwd_hash == stored_hash
    except Exception:
        return False

def inicializar_bd_auth():
    conn = obter_conexao()
    
    conn.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            senha_hash TEXT NOT NULL,
            role TEXT DEFAULT 'user',
            licenca TEXT UNIQUE,
            trocar_senha INTEGER DEFAULT 0
        )
    ''')
    
    conn.execute('''
        CREATE TABLE IF NOT EXISTS recuperacao_senha (
            email TEXT PRIMARY KEY,
            token TEXT NOT NULL,
            expira_em DATETIME NOT NULL,
            tentativas INTEGER DEFAULT 0
        )
    ''')
    
    # Migrações retroativas de colunas de segurança
    try:
        conn.execute("ALTER TABLE usuarios ADD COLUMN trocar_senha INTEGER DEFAULT 0")
    except sqlite3.OperationalError: pass
    
    try:
        conn.execute("ALTER TABLE recuperacao_senha ADD COLUMN tentativas INTEGER DEFAULT 0")
    except sqlite3.OperationalError: pass
    
    admin_email = os.getenv("ADMIN_EMAIL", "admin@agente.com")
    admin_senha = os.getenv("ADMIN_SENHA", "Admin123!")

    admin = conn.execute("SELECT id FROM usuarios WHERE email = ?", (admin_email,)).fetchone()
    if not admin:
        senha_hash_admin = gerar_hash_senha(admin_senha)
        licenca_master = str(uuid.uuid4())
        conn.execute(
            "INSERT INTO usuarios (nome, email, senha_hash, role, licenca, trocar_senha) VALUES (?, ?, ?, ?, ?, ?)",
            ('Administrador', admin_email, senha_hash_admin, 'admin', licenca_master, 0)
        )
    
    conn.commit()
    conn.close()

def validar_regras_senha(senha):
    if not SENHA_REGEX.match(senha):
        return False, "A senha deve ter no mínimo 8 caracteres, com 1 letra maiúscula, 1 minúscula e 1 número."
    return True, ""

def registrar_usuario(nome, email, senha):
    if not EMAIL_REGEX.match(email):
        return False, "Erro: Digite um e-mail válido."
        
    valido, msg_senha = validar_regras_senha(senha)
    if not valido:
        return False, msg_senha

    senha_hash = gerar_hash_senha(senha)
    
    conn = obter_conexao()
    try:
        conn.execute("INSERT INTO usuarios (nome, email, senha_hash, trocar_senha) VALUES (?, ?, ?, 0)", (nome, email, senha_hash))
        conn.commit()
        return True, "Cadastro realizado com sucesso!"
    except sqlite3.IntegrityError:
        return False, "Erro: Este e-mail já está cadastrado."
    finally:
        conn.close()

def autenticar_usuario(email, senha):
    conn = obter_conexao()
    user = conn.execute("SELECT id, nome, email, senha_hash, role, licenca, trocar_senha FROM usuarios WHERE email = ?", (email,)).fetchone()
    conn.close()
    
    if user and verificar_senha(user[3], senha):
        return True, {
            "id": user[0], 
            "nome": user[1], 
            "email": user[2], 
            "role": user[4], 
            "licenca": user[5],
            "trocar_senha": user[6]
        }
    return False, "E-mail ou senha inválidos."

def solicitar_token_recuperacao(email):
    if not EMAIL_REGEX.match(email):
        return False, "E-mail inválido."
        
    conn = obter_conexao()
    user = conn.execute("SELECT id FROM usuarios WHERE email = ?", (email,)).fetchone()
    
    if not user:
        conn.close()
        return True, "Se o e-mail existir na base, um código será enviado."
        
    token = ''.join(secrets.choice("0123456789") for _ in range(6))
    validade = (datetime.now() + timedelta(minutes=15)).strftime('%Y-%m-%d %H:%M:%S')
    
    conn.execute("INSERT OR REPLACE INTO recuperacao_senha (email, token, expira_em, tentativas) VALUES (?, ?, ?, 0)", (email, token, validade))
    conn.commit()
    conn.close()
    
    enviado, msg_email = enviar_token_senha(email, token)
    
    if enviado:
        return True, "Código de segurança enviado para o seu e-mail!"
    else:
        print(f"[LOG SEGURANÇA] Token para {email}: {token}")
        return False, f"Falha no envio (Rede): {msg_email}. O administrador pode resetar sua conta manualmente."

def redefinir_senha_com_token(email, token, nova_senha):
    conn = obter_conexao()
    registro = conn.execute("SELECT token, expira_em, tentativas FROM recuperacao_senha WHERE email = ?", (email,)).fetchone()
    
    if not registro:
        conn.close()
        return False, "Nenhum código solicitado ou token cancelado por segurança."
        
    token_banco, expira_em, tentativas = registro
    
    if datetime.now() > datetime.strptime(expira_em, '%Y-%m-%d %H:%M:%S'):
        conn.execute("DELETE FROM recuperacao_senha WHERE email = ?", (email,))
        conn.commit()
        conn.close()
        return False, "Código expirado. Solicite um novo."
        
    if token != token_banco:
        novas_tentativas = tentativas + 1
        if novas_tentativas >= 3:
            conn.execute("DELETE FROM recuperacao_senha WHERE email = ?", (email,))
            conn.commit()
            conn.close()
            return False, "Limite de tentativas excedido. Solicite um novo código por segurança."
        else:
            conn.execute("UPDATE recuperacao_senha SET tentativas = ? WHERE email = ?", (novas_tentativas, email))
            conn.commit()
            conn.close()
            return False, f"Código incorreto. Você tem mais {3 - novas_tentativas} tentativa(s)."
        
    valido, msg_senha = validar_regras_senha(nova_senha)
    if not valido:
        conn.close()
        return False, msg_senha
        
    novo_hash = gerar_hash_senha(nova_senha)
    conn.execute("UPDATE usuarios SET senha_hash = ?, trocar_senha = 0 WHERE email = ?", (novo_hash, email))
    conn.execute("DELETE FROM recuperacao_senha WHERE email = ?", (email,))
    conn.commit()
    conn.close()
    return True, "Senha redefinida com sucesso!"

def resetar_senha_por_admin(email_alvo):
    """Gera uma senha temporária compatível com as regras de validação e força a troca."""
    conn = obter_conexao()
    user = conn.execute("SELECT id FROM usuarios WHERE email = ?", (email_alvo,)).fetchone()
    
    if not user:
        conn.close()
        return False, f"Usuário {email_alvo} não encontrado."
        
    alfabeto = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    while True:
        senha_temporaria = ''.join(secrets.choice(alfabeto) for _ in range(10))
        # Garante que a senha gerada passe na sua Regex de validação
        if (any(c.islower() for c in senha_temporaria) and 
            any(c.isupper() for c in senha_temporaria) and 
            any(c.isdigit() for c in senha_temporaria)):
            break
            
    novo_hash = gerar_hash_senha(senha_temporaria)
    
    conn.execute("UPDATE usuarios SET senha_hash = ?, trocar_senha = 1 WHERE email = ?", (novo_hash, email_alvo))
    conn.execute("DELETE FROM recuperacao_senha WHERE email = ?", (email_alvo,))
    conn.commit()
    conn.close()
    
    return True, senha_temporaria

def alterar_senha_usuario(email, senha_antiga, nova_senha):
    conn = obter_conexao()
    user = conn.execute("SELECT senha_hash FROM usuarios WHERE email = ?", (email,)).fetchone()
    
    if not user or not verificar_senha(user[0], senha_antiga):
        conn.close()
        return False, "A senha atual está incorreta."
        
    valido, msg_senha = validar_regras_senha(nova_senha)
    if not valido:
        conn.close()
        return False, msg_senha
        
    novo_hash = gerar_hash_senha(nova_senha)
    conn.execute("UPDATE usuarios SET senha_hash = ?, trocar_senha = 0 WHERE email = ?", (novo_hash, email))
    conn.commit()
    conn.close()
    return True, "Senha alterada com sucesso."

def simular_pagamento_e_liberar_licenca(email):
    nova_licenca = str(uuid.uuid4())
    conn = obter_conexao()
    conn.execute("UPDATE usuarios SET licenca = ? WHERE email = ?", (nova_licenca, email))
    conn.commit()
    conn.close()
    return nova_licenca

def listar_todos_usuarios():
    conn = obter_conexao()
    usuarios = conn.execute("SELECT id, nome, email, role, licenca, trocar_senha FROM usuarios ORDER BY id DESC").fetchall()
    conn.close()
    return usuarios