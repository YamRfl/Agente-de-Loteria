# 🍀 Agente de IA - Analista de Loterias (v3.0)

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-UI-ff4b4b.svg)](https://streamlit.io/)
[![SQLite](https://img.shields.io/badge/SQLite-3.x-003b57.svg)](https://sqlite.org/)
[![Security](https://img.shields.io/badge/Security-Hardened-success.svg)](#)

O **Agente de IA - Analista de Loterias** é uma plataforma completa de engenharia de dados e análise estatística voltada para as loterias da Caixa (**Mega-Sena, Lotofácil, Quina, Lotomania, Dupla Sena e Timemania**). O sistema combina coleta em tempo real, persistência em banco de dados relacional e algoritmos de sugestão baseados em tendências históricas.

---

## 🚀 Funcionalidades Principais

### 🛡️ Segurança e Integridade (Novidade v3.0)
- **Criptografia CSPRNG:** Motor de geração de jogos movido pelo módulo `secrets` do SO, garantindo total imprevisibilidade criptográfica (sem uso do vulnerável `random`).
- **Prevenção SQLi e XSS:** Arquitetura de dados 100% blindada utilizando *Prepared Statements* (consultas parametrizadas) nas integrações com o SQLite.
- **Checksum de Arquivos:** Geração de hash **SHA-256** no momento do download para atestar a integridade das apostas geradas (Prevenção MITM).
- **Anti-DoS e OOM:** *Circuit Breakers* aplicados aos algoritmos de filtragem de jogos e uso de bibliotecas C-nativas para evitar estouro de memória em cálculos combinatórios.

### 📡 Coleta & Sincronização
- **Update em Tempo Real:** Conexão direta com a API da Caixa Econômica Federal.
- **Barra de Incremento Visual:** Monitoramento do progresso de download concurso a concurso.
- **Arquitetura Incremental:** O sistema identifica o último sorteio no banco e baixa apenas o que falta.

### 📈 Inteligência Estatística (Aba dedicada)
- **Análise de Incidência:** Ranking dinâmico dos números mais sorteados com barras de frequência.
- **Heatmap de Atraso:** Mapa de calor que identifica há quantos concursos cada dezena não é sorteada (identificação visual de números "frios" e "atrasados").
- **Paridade e Tendência:** Algoritmos que filtram jogos baseados no equilíbrio entre pares e ímpares.

### 🎯 Gerador & Gestão de Apostas
- **Motor de Sugestão:** Criação de jogos respeitando frequências e evitando sequências óbvias (ex: 01, 02, 03).
- **Sistema de Carrinho:** Adicione múltiplos jogos de diferentes loterias e visualize o custo total antes de confirmar.
- **Exportação CSV:** Gere listas de apostas prontas para conferência ou impressão.
- **Banco de Apostas:** Salve seus jogos gerados no banco de dados para conferência automática futura.

### 💰 Gestão Financeira & Customização
- **Painel de Tarifas:** Ajuste o valor da aposta simples e o limite de dezenas diretamente pela interface (Sidebar).
- **Cálculo de Desdobramentos:** Estimativa real do custo de jogos com marcações superiores à mínima (ex: jogar 15 números na Lotofácil).

---

## 🛠️ Tecnologias e Arquitetura

O projeto foi construído seguindo princípios de modularização e Clean Code:
- **Frontend:** `Streamlit` para uma UI reativa e moderna.
- **Data Engine:** `Pandas` para processamento de matrizes e cálculos estatísticos.
- **Storage:** `SQLite` para armazenamento persistente e rápido.
- **Security:** Módulos nativos `hashlib` e `secrets` para compliance de segurança.
- **API Rest:** Protocolo HTTP para consumo de dados governamentais.

---

## 📁 Estrutura do Repositório

```text
├── app.py                # Ponto de entrada da aplicação (UI e Abas)
├── .gitignore            # Proteção contra arquivos temporários e bancos locais
├── requirements.txt      # Dependências do projeto
├── src/                  # Núcleo da lógica de negócio
│   ├── analyzer.py       # Algoritmos de frequência, atraso e processamento de dados
│   ├── checker.py        # Motor de conferência de acertos contra resultados oficiais
│   ├── collector.py      # Script de comunicação com a API e barra de progresso
│   ├── database.py       # Esquema do banco, CRUD de apostas e gestão de tarifas
│   └── generator.py      # Lógica matemática (CSPRNG) para geração de jogos
└── loterias_caixa.db     # Banco de dados SQLite (Gerado automaticamente)
⚙️ Instalação e Execução
Preparar Ambiente:

Bash
python -m venv venv

# No Linux/Mac:
source venv/bin/activate

# No Windows:
.\venv\Scripts\activate
Instalar Dependências:

Bash
pip install -r requirements.txt
Iniciar Agente:

Bash
streamlit run app.py
⚠️ Nota Legal
Este software é uma ferramenta de análise probabilística e estudo estatístico. Ele visa auxiliar o usuário na escolha de dezenas através de dados históricos, porém não garante ganhos financeiros. Loterias são jogos de azar; jogue com responsabilidade e consciência.

Desenvolvido como um agente inteligente e seguro de análise de dados. 🍀
