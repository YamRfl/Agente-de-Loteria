# 🍀 Agente de IA - Analista de Loterias SaaS (v6.0)

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-UI-ff4b4b.svg)](https://streamlit.io/)
[![SQLite](https://img.shields.io/badge/SQLite-3.x-003b57.svg)](https://sqlite.org/)
[![Machine Learning](https://img.shields.io/badge/Machine%20Learning-Scikit--Learn-F7931E.svg)](https://scikit-learn.org/)
[![Security](https://img.shields.io/badge/Security-OWASP_PBKDF2-success.svg)](#)
[![Dotenv](https://img.shields.io/badge/Environment-.env-ECD53F.svg)](#)
[![SMTP](https://img.shields.io/badge/Email-SMTP-EA4335.svg)](#)

O **Agente de IA - Analista de Loterias** é uma plataforma SaaS (Software as a Service) Freemium de alta performance para engenharia de dados e análise combinatória. Suporta o portfólio completo da Caixa (**Mega-Sena, Lotofácil, Quina, Lotomania, Dupla Sena, Timemania, +Milionária e Dia de Sorte**).

---

## 🚀 1. Novidades da Versão 6.0

- **📧 Recuperação de Senha via E-mail (OTP):** Motor SMTP nativo que envia Tokens de 6 dígitos com validade de 15 minutos.
- **🛡️ Cofre de Segurança (.env):** Credenciais sensíveis (E-mail, Senhas de API e Admin) blindadas contra vazamentos.
- **⚡ Sincronização em Lote (Batch Sync):** Atualização ultra-rápida do histórico completo usando `executemany`.
- **🎨 UX/UI Otimizada:** Design compacto (redução de 30% no padding), scrollbar persistente e botão de Logout no topo.
- **🚪 Logout Global:** Atalhos para encerramento de sessão tanto na barra lateral quanto no cabeçalho principal.

---

## 🔐 2. Segurança e Autenticação (Nível OWASP)

### Hashing e Proteção
- **Algoritmo:** `PBKDF2-HMAC-SHA256` com Salt dinâmico de 32 bytes e 210.000 iterações.
- **Tokens Temporários:** Armazenamento em tabela SQL específica com timestamp de expiração para garantir que tokens de e-mail não sejam reutilizados.
- **Blindagem .env:** O arquivo de senhas é carregado apenas em memória e nunca é versionado no Git.

---

## ⚙️ 3. Guia de Instalação e Configuração

### Passo 1: Clonar e Preparar
```bash
git clone [https://github.com/YamRfl/Agente-de-Loteria.git](https://github.com/YamRfl/Agente-de-Loteria.git)
cd Agente-de-Loteria
python -m venv venv
# Windows
venv\Scripts\activate
pip install -r requirements.txt

Passo 2: Configurar o Cofre (.env)
Crie um arquivo chamado .env na raiz e preencha:

Snippet de código
# Servidor de Disparo (Gmail)
EMAIL_REMETENTE=seu.email@gmail.com
SENHA_APP=suasenhaappsemespaços

# Credenciais Iniciais do Admin (Semente)
ADMIN_EMAIL=jarafael@protonmail.com
ADMIN_SENHA=To100senha
Passo 3: Inicialização Crítica
Se você estiver vindo de uma versão anterior, delete o arquivo loterias_caixa.db para que o sistema crie as novas tabelas de segurança (Tokens de E-mail) e o novo usuário Admin.

📁 4. Estrutura de Pastas do Projeto
Plaintext
Agente-de-Loteria/
├── run.bat               # Atalho de inicialização rápida
├── app.py                # Interface Principal (Streamlit)
├── .env                  # Cofre de senhas (NÃO VERSIONAR)
├── .env.example          # Modelo público das variáveis
├── .gitignore            # Regras de exclusão (Blindagem de segurança)
├── requirements.txt      # Bibliotecas necessárias
├── loterias_caixa.db     # Banco de Dados Local (Gerado no 1º boot)
└── src/                  # Pasta de código-fonte modular
    ├── auth.py           # Core de Segurança e Gestão de Tokens
    ├── mailer.py         # Microserviço de envio de e-mails SMTP
    ├── database.py       # Conexão SQL, Tabelas e Tarifas
    ├── collector.py      # Raspagem de dados (Batch & Delta)
    ├── generator.py      # Motor de IA e Filtros Combinatórios
    ├── analyzer.py       # Dashboards Estatísticos (Plotly)
    ├── checker.py        # Conferência de apostas vs resultados
    └── ml_engine.py      # Algoritmos de Machine Learning (K-Means)

📊 5. Funcionalidades de Inteligência Artificial
K-Means Clustering: Agrupa resultados históricos para identificar padrões de sorteio.

DNA Matemático: Filtra jogos baseando-se em Soma, Primos, Fibonacci, Moldura e Múltiplos.

Paywall VIP: Recursos avançados de IA são exclusivos para usuários com chave de licença ativa.

📄 Licença
Distribuído sob a licença MIT. Uso livre para fins acadêmicos e pessoais.
