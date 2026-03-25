# 🍀 Agente de IA - Analista de Loterias (v4.6)

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-UI-ff4b4b.svg)](https://streamlit.io/)
[![SQLite](https://img.shields.io/badge/SQLite-3.x-003b57.svg)](https://sqlite.org/)
[![Machine Learning](https://img.shields.io/badge/Machine%20Learning-Scikit--Learn-F7931E.svg)](https://scikit-learn.org/)
[![Plotly](https://img.shields.io/badge/Data%20Viz-Plotly-3F4F75.svg)](https://plotly.com/)
[![Security](https://img.shields.io/badge/Security-Hardened-success.svg)](#)

O **Agente de IA - Analista de Loterias** é uma plataforma de engenharia de dados, ciência preditiva e análise combinatória voltada para as loterias da Caixa (**Mega-Sena, Lotofácil, Quina, Lotomania, Dupla Sena e Timemania**). O sistema combina coleta em tempo real, segurança criptográfica, modelos de **Machine Learning** e visualização de dados interativa para otimização de apostas.

---

## 🚀 Funcionalidades Principais

### ⚡ Alta Performance e Engenharia de Dados (v4.6)
- **Memoização e Caching:** Otimização profunda do Streamlit via `@st.cache_data` para renderização instantânea de gráficos e tabelas.
- **Estruturas O(1):** Uso de *Hash Maps* e *Sets* pré-calculados no gerador, permitindo a validação de milhares de jogos em milissegundos.

### 🧠 Inteligência Artificial Preditiva (v4.0)
- **K-Means Clustering:** A IA treina um modelo não-supervisionado com o histórico completo da loteria.
- **Análise de DNA do Jogo:** Algoritmo que extrai *features* complexas (Soma, Pares/Ímpares, Primos e Dispersão).
- **Filtro Preditivo Automático:** Aprova apenas jogos que pertencem ao grupo (cluster) matemático com maior índice histórico de vitórias.

### 🛠️ Filtros Matemáticos Manuais e Avançados (v4.5)
Controle cirúrgico para apostadores profissionais limitarem o espaço amostral de combinações:
- **Quantitativos:** Limites exatos de Soma das Dezenas, Pares, Primos, Múltiplos de 3 e sequência de Fibonacci.
- **Espaciais:** Regras de preenchimento do volante (Proporção Moldura vs. Miolo, e máximo de dezenas permitidas por Linha/Coluna).
- **Repetidas:** Força o sistema a incluir/excluir dezenas que saíram no concurso imediatamente anterior.

### 🎨 UX e Acessibilidade - A11y (v4.6)
- **Design Inclusivo:** Paletas de cores de alto contraste (Azul/Laranja) otimizadas para usuários com daltonismo (Protanopia/Deuteranopia).
- **Gamificação:** Celebração visual (*Balloons*) ativada automaticamente ao conferir acertos premiados.
- **Notificações Modernas:** Alertas em formato *Toast* flutuantes para não quebrar a responsividade da interface.
- **Suporte a Leitores de Tela:** Labels descritivas (Aria-labels) implementadas em todos os controles e botões.

### 📊 Visualização Interativa de Dados (v4.5)
- **Dashboards Plotly:** Gráficos vetoriais interativos (Top 20 Dezenas Mais Sorteadas e Maiores Atrasos) com *tooltips* ao passar o mouse.
- **Alternância de Visão:** Toggle limpo para trocar entre o modo gráfico e a visualização de tabelas completas.

### 🎯 Gerador, Exportação e Conferência (v4.5)
- **Motor de Sugestão:** Gera milhares de jogos em milissegundos respeitando os filtros, com *Circuit Breakers* para evitar travamento em regras impossíveis.
- **Exportação Profissional:** Baixe suas apostas prontas e formatadas em **Excel (.xlsx)**.
- **Conferência Automatizada:** Salve jogos no banco local para verificar acertos de forma automática e limpe o histórico quando desejar.

### 🛡️ Segurança e Integridade (v3.0)
- **Criptografia CSPRNG:** Motor movido pelo módulo `secrets` do SO (sem uso de *pseudo-random* vulnerável).
- **Blindagem SQLi e XSS:** Arquitetura 100% blindada via *Prepared Statements* no SQLite.
- **Checksum de Arquivos:** Assinatura digital (Hash SHA-256) atestando a integridade dos arquivos Excel gerados.

---

## 🛠️ Tecnologias e Arquitetura

Projeto modularizado baseado em Clean Code:
- **Frontend:** `Streamlit` para uma UI reativa e moderna.
- **Data & AI Engine:** `Pandas`, `NumPy` e `Scikit-Learn` para modelagem e clusterização.
- **Data Viz:** `Plotly` para gráficos ricos e dinâmicos.
- **Storage:** `SQLite` nativo.
- **File System:** `io` e `openpyxl` para manipulação em memória.
- **Security:** `hashlib` e `secrets`.

---

## 📁 Estrutura do Repositório

```text
├── app.py                # Ponto de entrada da aplicação (UI e Abas)
├── .gitignore            # Proteção contra arquivos temporários e bancos
├── requirements.txt      # Dependências do projeto
├── src/                  # Núcleo da lógica de negócio
│   ├── analyzer.py       # Frequência e processamento de dados
│   ├── checker.py        # Conferência de acertos contra resultados oficiais
│   ├── collector.py      # Comunicação com a API Caixa
│   ├── database.py       # Esquema SQLite, CRUD e Limpeza de histórico
│   ├── generator.py      # Motor CSPRNG com Filtros Manuais Avançados
│   └── ml_engine.py      # Motor de Machine Learning e extração de features
└── loterias_caixa.db     # Banco de dados (Gerado no 1º acesso)
