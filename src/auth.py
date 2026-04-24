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
    
    # Tabela principal de Usuários
    conn.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            senha_hash TEXT NOT NULL,
            role TEXT DEFAULT 'user',
            licenca TEXT UNIQUE
        )
    ''')
    
    # Tabela temporária para os Tokens de Recuperação enviados por e-mail
    conn.execute('''
        CREATE TABLE IF NOT EXISTS recuperacao_senha (
            email TEXT PRIMARY KEY,
            token TEXT NOT NULL,
            expira_em DATETIME NOT NULL
        )
    ''')
    
    # Puxa as credenciais mestres do .env de forma segura
    # (Se não achar no .env, usa um padrão de emergência)
    admin_email = os.getenv("ADMIN_EMAIL", "admin@agente.com")
    admin_senha = os.getenv("ADMIN_SENHA", "Admin123!")

    # Usuário Administrador Soberano
    admin = conn.execute("SELECT id FROM usuarios WHERE email = ?", (admin_email,)).fetchone()
    if not admin:
        senha_hash_admin = gerar_hash_senha(admin_senha)
        licenca_master = str(uuid.uuid4())
        conn.execute(
            "INSERT INTO usuarios (nome, email, senha_hash, role, licenca) VALUES (?, ?, ?, ?, ?)",
            ('Administrador', admin_email, senha_hash_admin, 'admin', licenca_master)
        )
    
    conn.commit()
    conn.close()

def validar_regras_senha(senha):
    if not SENHA_REGEX.match(senha):
        return False, "A senha deve ter no mínimo 8 caracteres, com 1 letra maiúscula, 1 minúscula e 1 número."
    return True, ""

def registrar_usuario(nome, email, senha):
    if not EMAIL_REGEX.match(email):
        return False, "Erro: Digite um e-mail válido (ex: nome@dominio.com)."
        
    valido, msg_senha = validar_regras_senha(senha)
    if not valido:
        return False, msg_senha

    senha_hash = gerar_hash_senha(senha)
    
    conn = obter_conexao()
    try:
        conn.execute("INSERT INTO usuarios (nome, email, senha_hash) VALUES (?, ?, ?)", (nome, email, senha_hash))
        conn.commit()
        return True, "Cadastro realizado com sucesso! Faça login."
    except sqlite3.IntegrityError:
        return False, "Erro: Este e-mail já está cadastrado."
    finally:
        conn.close()

def autenticar_usuario(email, senha):
    conn = obter_conexao()
    user = conn.execute("SELECT id, nome, email, senha_hash, role, licenca FROM usuarios WHERE email = ?", (email,)).fetchone()
    conn.close()
    
    if user and verificar_senha(user[3], senha):
        return True, {"id": user[0], "nome": user[1], "email": user[2], "role": user[4], "licenca": user[5]}
    return False, "E-mail ou senha inválidos."

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
    conn.execute("UPDATE usuarios SET senha_hash = ? WHERE email = ?", (novo_hash, email))
    conn.commit()
    conn.close()
    return True, "Senha alterada com segurança."

# ==========================================
# FLUXO DE RECUPERAÇÃO COM TOKEN
# ==========================================
def solicitar_token_recuperacao(email):
    if not EMAIL_REGEX.match(email):
        return False, "E-mail inválido."
        
    conn = obter_conexao()
    user = conn.execute("SELECT id FROM usuarios WHERE email = ?", (email,)).fetchone()
    
    if not user:
        conn.close()
        return True, "Se o e-mail existir na nossa base, um código será enviado."
        
    # Gera um Token de 6 dígitos aleatório
    token = ''.join(secrets.choice("0123456789") for _ in range(6))
    validade = (datetime.now() + timedelta(minutes=15)).strftime('%Y-%m-%d %H:%M:%S')
    
    # Grava o token no banco, sobrescrevendo se o usuário pedir duas vezes
    conn.execute("INSERT OR REPLACE INTO recuperacao_senha (email, token, expira_em) VALUES (?, ?, ?)", (email, token, validade))
    conn.commit()
    conn.close()
    
    # Dispara o E-mail usando o seu arquivo mailer.py
    enviado, msg_email = enviar_token_senha(email, token)
    
    if enviado:
        return True, "Código de segurança enviado para o seu e-mail!"
    else:
        return False, msg_email

def redefinir_senha_com_token(email, token, nova_senha):
    conn = obter_conexao()
    registro = conn.execute("SELECT token, expira_em FROM recuperacao_senha WHERE email = ?", (email,)).fetchone()
    
    if not registro:
        conn.close()
        return False, "Nenhum código foi solicitado para este e-mail."
        
    token_banco, expira_em = registro
    agora = datetime.now()
    data_expiracao = datetime.strptime(expira_em, '%Y-%m-%d %H:%M:%S')
    
    if agora > data_expiracao:
        conn.execute("DELETE FROM recuperacao_senha WHERE email = ?", (email,))
        conn.commit(); conn.close()
        return False, "Este código expirou. Solicite um novo."
        
    if token != token_banco:
        conn.close()
        return False, "Código incorreto."
        
    valido, msg_senha = validar_regras_senha(nova_senha)
    if not valido:
        conn.close()
        return False, msg_senha
        
    # Sucesso Total: Muda a senha e destroi o Token para não ser reusado
    novo_hash = gerar_hash_senha(nova_senha)
    conn.execute("UPDATE usuarios SET senha_hash = ? WHERE email = ?", (novo_hash, email))
    conn.execute("DELETE FROM recuperacao_senha WHERE email = ?", (email,))
    conn.commit()
    conn.close()
    return True, "Senha redefinida com sucesso! Você já pode fazer login."

def simular_pagamento_e_liberar_licenca(email):
    nova_licenca = str(uuid.uuid4())
    conn = obter_conexao()
    conn.execute("UPDATE usuarios SET licenca = ? WHERE email = ?", (nova_licenca, email))
    conn.commit()
    conn.close()
    return nova_licenca

def listar_todos_usuarios():
    conn = obter_conexao()
    usuarios = conn.execute("SELECT id, nome, email, role, licenca FROM usuarios ORDER BY id DESC").fetchall()
    conn.close()
    return usuarios