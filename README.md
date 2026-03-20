# 🍀 Agente de IA - Analista de Loterias

[](https://www.python.org/)
[](https://streamlit.io/)
[](https://sqlite.org/)

O **Agente de IA - Analista de Loterias** é uma plataforma completa de engenharia de dados e análise estatística voltada para as loterias da Caixa (Mega-Sena, Lotofácil e Quina). O sistema combina coleta em tempo real, persistência em banco de dados relacional e algoritmos de sugestão baseados em tendências históricas.

-----

## 🚀 Funcionalidades Principais

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
  - **Cálculo de Desdobramentos:** Estimativa real do custo de jogos com marcações superiores à mínima (ex: jogar 15 números na Mega-Sena).

-----

## 🛠️ Tecnologias e Arquitetura

O projeto foi construído seguindo princípios de modularização:

  - **Frontend:** [Streamlit](https://streamlit.io/) para uma UI reativa e moderna.
  - **Data Engine:** [Pandas](https://pandas.pydata.org/) para processamento de matrizes e cálculos estatísticos.
  - **Storage:** [SQLite](https://sqlite.org/) para armazenamento persistente e rápido.
  - **API Rest:** Protocolo HTTP para consumo de dados governamentais.

-----

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
│   └── generator.py      # Lógica matemática para geração de jogos e custos
└── loterias_caixa.db     # Banco de dados SQLite (Gerado automaticamente)
```

-----

## ⚙️ Instalação e Execução

1.  **Preparar Ambiente:**

    ```bash
    python -m venv venv
    source venv/bin/activate  # Linux/Mac
    .\venv\Scripts\activate   # Windows
    ```

2.  **Instalar Dependências:**

    ```bash
    pip install -r requirements.txt
    ```

3.  **Iniciar Agente:**

    ```bash
    streamlit run app.py
    ```

-----

## ⚠️ Nota Legal

Este software é uma ferramenta de **análise probabilística e estudo estatístico**. Ele visa auxiliar o usuário na escolha de dezenas através de dados históricos, porém **não garante ganhos financeiros**. Loterias são jogos de azar; jogue com responsabilidade e consciência.

-----

**Desenvolvido como um agente inteligente de análise de dados.** 🍀

