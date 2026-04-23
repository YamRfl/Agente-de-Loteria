# 🍀 Agente de IA - Analista de Loterias SaaS (v5.0)

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-UI-ff4b4b.svg)](https://streamlit.io/)
[![SQLite](https://img.shields.io/badge/SQLite-3.x-003b57.svg)](https://sqlite.org/)
[![Machine Learning](https://img.shields.io/badge/Machine%20Learning-Scikit--Learn-F7931E.svg)](https://scikit-learn.org/)
[![Plotly](https://img.shields.io/badge/Data%20Viz-Plotly-3F4F75.svg)](https://plotly.com/)
[![Security](https://img.shields.io/badge/Security-OWASP_PBKDF2-success.svg)](#)

O **Agente de IA - Analista de Loterias** evoluiu para uma plataforma SaaS (Software as a Service) Freemium de engenharia de dados, ciência preditiva e análise combinatória. Suportando o portfólio completo da Caixa (**Mega-Sena, Lotofácil, Quina, Lotomania, Dupla Sena, Timemania, +Milionária e Dia de Sorte**), o sistema combina coleta em tempo real, segurança criptográfica estrita, paywall automatizado e modelos de **Machine Learning** para otimização de apostas.

---

## 🚀 Novidades da Versão 5.0 (SaaS & Autenticação)

### 💳 Arquitetura SaaS Freemium e Paywall
- **Controle de Acesso:** Divisão clara entre usuários *Free* (geração de jogos aleatórios) e assinantes *VIP* (acesso total à Inteligência Artificial e Filtros Avançados).
- **Simulação de Pagamento:** Fluxo integrado para emissão e validação de Chaves de Licença (UUID).
- **Painel Admin:** Centro de Comando exclusivo para gerenciar a base de clientes e ajustar os preços base e limites de dezenas globais do sistema.

### 🔐 Segurança e Criptografia Nível OWASP
- **Hashing de Senhas:** Implementação do algoritmo `PBKDF2-HMAC-SHA256` com Salt dinâmico e 210.000 iterações, mitigando ataques de força bruta e *Rainbow Tables*.
- **Validação Estrita:** Expressões Regulares (Regex) que obrigam e-mails válidos e senhas fortes (mínimo de 8 caracteres, maiúsculas, minúsculas e números).
- **Gestão de Credenciais:** Fluxos completos e seguros para atualização de senhas logadas e recuperação de senhas esquecidas.

---

## ⚡ Funcionalidades Principais Herdadas

### 🧠 Inteligência Artificial Preditiva
- **K-Means Clustering:** A IA treina um modelo não-supervisionado com o histórico completo da loteria.
- **Análise de DNA do Jogo:** Algoritmo que extrai *features* complexas (Soma, Pares/Ímpares, Primos e Dispersão).
- **Filtro Preditivo Automático:** Aprova apenas jogos que pertencem ao cluster matemático com maior índice histórico de vitórias.

### 🛠️ Filtros Matemáticos Manuais e Avançados
Controle cirúrgico para apostadores limitarem o espaço amostral de combinações:
- **Quantitativos:** Limites exatos de Soma das Dezenas, Pares, Primos, Múltiplos de 3 e sequência de Fibonacci.
- **Espaciais:** Regras de preenchimento do volante (Proporção Moldura vs. Miolo, e máximo de dezenas permitidas por Linha/Coluna).
- **Repetidas:** Força o sistema a incluir/excluir dezenas que saíram no concurso imediatamente anterior.

### 📊 Engenharia de Dados, Visualização e Exportação
- **Sincronização Oficial:** Consumo de API para manter os resultados em paridade com os sorteios oficiais da Caixa Econômica.
- **Dashboards Interativos Plotly:** Gráficos vetoriais (Frequência e Atrasos) alternáveis com tabelas de dados brutos.
- **Exportação Profissional:** Baixe suas apostas prontas e formatadas em **Excel (.xlsx)**.
- **Conferência Automatizada:** Salve jogos no banco local para verificar acertos de forma automática e celebre com animações gamificadas (*Balloons*).

---

## 🛠️ Tecnologias e Arquitetura

Projeto modularizado baseado em Clean Code:
- **Frontend:** `Streamlit` para uma UI reativa.
- **Data & AI Engine:** `Pandas`, `NumPy` e `Scikit-Learn` para modelagem.
- **Data Viz:** `Plotly` para gráficos dinâmicos.
- **Storage:** `SQLite` nativo (Protegido via `.gitignore`).
- **Security:** `hashlib`, `os.urandom` (CSPRNG) e `re` (Regex).

---

## 📁 Estrutura do Repositório

```text
├── run.bat               # Inicializador nativo (Ambiente Virtual + Streamlit)
├── app.py                # Ponto de entrada da aplicação (UI e Abas)
├── .gitignore            # Proteção contra vazamento de banco de dados e senhas
├── requirements.txt      # Dependências do projeto
├── src/                  # Núcleo da lógica de negócio
│   ├── auth.py           # Motor de Segurança, Criptografia PBKDF2 e Autenticação
│   ├── database.py       # Esquema SQLite, CRUD, Controle de Tarifas e Histórico
│   ├── collector.py      # Comunicação com a API da Caixa
│   ├── generator.py      # Motor Combinatório com Filtros e Paywall
│   ├── analyzer.py       # Estatísticas de Frequência e Atraso
│   ├── checker.py        # Auditoria de Acertos contra resultados oficiais
│   └── ml_engine.py      # Motor de Machine Learning e clusterização (K-Means)
