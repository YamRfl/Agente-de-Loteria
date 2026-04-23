import sqlite3
import os
import hashlib
import binascii
import uuid
import re
from .database import obter_conexao

# Regras de validação estritas (OWASP)
EMAIL_REGEX = re.compile(r"^[\w\.-]+@[\w\.-]+\.\w+$")
# Regex: Mínimo 8 chars, pelo menos 1 maiúscula, 1 minúscula e 1 número
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
            licenca TEXT UNIQUE
        )
    ''')
    
    admin = conn.execute("SELECT id FROM usuarios WHERE email = 'admin@agente.com'").fetchone()
    if not admin:
        senha_hash_admin = gerar_hash_senha('Admin123!')
        licenca_master = str(uuid.uuid4())
        conn.execute(
            "INSERT INTO usuarios (nome, email, senha_hash, role, licenca) VALUES (?, ?, ?, ?, ?)",
            ('Administrador', 'admin@agente.com', senha_hash_admin, 'admin', licenca_master)
        )
    
    conn.commit()
    conn.close()

def validar_regras_senha(senha):
    if not SENHA_REGEX.match(senha):
        return False, "A senha deve ter no mínimo 8 caracteres, contendo pelo menos 1 letra maiúscula, 1 minúscula e 1 número."
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

def redefinir_senha_esquecida(email, nova_senha):
    if not EMAIL_REGEX.match(email):
        return False, "E-mail inválido."
        
    conn = obter_conexao()
    user = conn.execute("SELECT id FROM usuarios WHERE email = ?", (email,)).fetchone()
    if not user:
        conn.close()
        return False, "E-mail não encontrado na base de dados."
        
    valido, msg_senha = validar_regras_senha(nova_senha)
    if not valido:
        conn.close()
        return False, msg_senha
        
    novo_hash = gerar_hash_senha(nova_senha)
    conn.execute("UPDATE usuarios SET senha_hash = ? WHERE email = ?", (novo_hash, email))
    conn.commit()
    conn.close()
    return True, "Senha redefinida com sucesso! Proceda para o login."

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