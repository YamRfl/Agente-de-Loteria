# 🍀 Agente de IA - Analista de Loterias SaaS (v6.1.1)

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-2026_Ready-ff4b4b.svg)](https://streamlit.io/)
[![SQLite](https://img.shields.io/badge/SQLite-3.x-003b57.svg)](https://sqlite.org/)
[![Machine Learning](https://img.shields.io/badge/Machine%20Learning-Scikit--Learn-F7931E.svg)](https://scikit-learn.org/)
[![Security](https://img.shields.io/badge/Security-OWASP_Hardened-success.svg)](#)
[![Dotenv](https://img.shields.io/badge/Environment-.env-ECD53F.svg)](#)
[![SMTP](https://img.shields.io/badge/Email-SMTP-EA4335.svg)](#)

O **Agente de IA - Analista de Loterias** é uma plataforma SaaS (Software as a Service) Freemium de alta performance para engenharia de dados e análise combinatória. Suporta o portfólio completo da Caixa (**Mega-Sena, Lotofacil, Quina, Lotomania, Dupla Sena, Timemania, +Milionária e Dia de Sorte**).

---

## 🚀 1. Novidades da Versão 6.1.1 (Security Hardening & Streamlit 2026)

- **🛡️ Firewall de Senha Temporária:** O reset pelo Administrador agora gera uma **senha única aleatória de 10 caracteres** que cumpre todos os requisitos de segurança (Maiúsculas, Minúsculas e Números), eliminando senhas padrão previsíveis.
- **🔒 Troca Obrigatória (Flag de Segurança):** Implementação de lógica de banco de dados que detecta resets administrativos e obriga o usuário a definir uma nova senha pessoal no primeiro login.
- **🚫 Bloqueio Anti-Brute Force:** O sistema de recuperação via Token (OTP) agora possui limite de **3 tentativas**. Após o erro excessivo, o token é deletado e o acesso é bloqueado por segurança.
- **📱 Compatibilidade Streamlit 2026:** Refatoração completa para remover avisos de depreciação de UI, utilizando o novo motor de renderização `width="stretch"`.
- **📉 Dashboards de Alta Densidade:** Ajuste fino no CSS para reduzir o padding em mais 15%, permitindo visualizar mais estatísticas sem necessidade de scroll.

---

## 🔐 2. Segurança e Autenticação (Nível OWASP)

### Hashing e Proteção
- **Algoritmo:** PBKDF2-HMAC-SHA256 com Salt dinâmico de 32 bytes e 210.000 iterações.
- **Gestão de Tokens:** Tabela de recuperação limpa automaticamente tokens expirados ou após 3 tentativas inválidas.
- **Blindagem .env:** Variáveis críticas de ambiente são protegidas e o arquivo `.env` é explicitamente ignorado pelo Git para evitar exposição de credenciais.

---

## ⚙️ 3. Guia de Instalação e Configuração

### Passo 1: Clonar e Preparar
    git clone https://github.com/YamRfl/Agente-de-Loteria.git
    cd Agente-de-Loteria
    python -m venv venv
    venv\Scripts\activate
    pip install -r requirements.txt

### Passo 2: Configurar o Cofre (.env)
Crie um arquivo chamado `.env` na raiz do projeto e preencha com suas credenciais:

    EMAIL_REMETENTE=seu.email@gmail.com
    SENHA_APP=suasenhaappsemespaços
    ADMIN_EMAIL=jarafael@protonmail.com
    ADMIN_SENHA=To100senha

### Passo 3: Inicialização
Se estiver vindo da v6.0 ou anterior, recomenda-se limpar o banco para garantir a nova estrutura de segurança:

    run.bat
    (Ou execute manualmente: streamlit run app.py)

---

## 📁 4. Estrutura de Pastas do Projeto

    Agente-de-Loteria/
    ├── run.bat                # Atalho de inicialização rápida
    ├── app.py                 # Interface Principal (Streamlit 2026 Ready)
    ├── .env                   # Cofre de senhas (NÃO VERSIONAR)
    ├── .env.example           # Modelo público das variáveis
    ├── .gitignore             # Regras de exclusão (Blindagem de segurança)
    ├── requirements.txt       # Bibliotecas necessárias
    ├── loterias_caixa.db      # Banco de Dados Local (Gerado no 1º boot)
    └── src/                   # Pasta de código-fonte modular
        ├── auth.py            # Core de Segurança: Reset Seguro e Flag de Troca
        ├── mailer.py          # Microserviço de envio de e-mails SMTP
        ├── database.py        # Conexão SQL, Tabelas e Tarifas
        ├── collector.py       # Raspagem de dados (Batch & Delta)
        ├── generator.py       # Motor de IA e Filtros Combinatórios
        ├── analyzer.py        # Dashboards Estatísticos (Plotly)
        ├── checker.py         # Conferência de apostas vs resultados
        └── ml_engine.py       # Algoritmos de Machine Learning (K-Means)

---

## 📊 5. Funcionalidades de Inteligência Artificial

- **K-Means Clustering:** Agrupa resultados históricos para identificar padrões de sorteio.
- **DNA Matemático:** Filtra jogos baseando-se em Soma, Primos, Fibonacci, Moldura e Múltiplos.
- **Controle de Licença:** Verificação automática de licenças via UUID para liberação de módulos premium.

---

## 📄 6. Licença
Distribuído sob a licença MIT. Uso livre para fins acadêmicos e pessoais.
