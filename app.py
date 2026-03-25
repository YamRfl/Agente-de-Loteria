import streamlit as st
import pandas as pd
import time
import hashlib
from src.database import inicializar_bd, obter_conexao, obter_ultimo_concurso_db, atualizar_preco_banco
from src.collector import atualizar_resultados
from src.generator import sugerir_jogo, calcular_custo_jogos
from src.checker import conferir_resultados
from src.analyzer import obter_estatisticas_completas

# Função de segurança para assinar arquivos com SHA-256
def gerar_hash_sha256(dados_bytes):
    return hashlib.sha256(dados_bytes).hexdigest()

st.set_page_config(page_title="Agente IA Loterias", layout="wide", page_icon="🍀")
inicializar_bd()

if 'carrinho' not in st.session_state:
    st.session_state.carrinho = []

st.title("🍀 Agente de IA - Analista de Loterias")

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Controle")
    loteria = st.selectbox("Loteria:", ["megasena", "lotofacil", "quina", "lotomania", "duplasena", "timemania"])
    
    st.divider()
    with st.expander("💰 Ajustar Preços e Limites"):
        conn = obter_conexao()
        dados_t = conn.execute("SELECT preco_base, dez_max FROM tarifas WHERE loteria=?", (loteria,)).fetchone()
        conn.close()
        
        if dados_t:
            novo_preco = st.number_input("Preço Aposta Simples:", value=float(dados_t[0]), step=0.50)
            nova_dez_max = st.number_input("Limite de Dezenas:", value=int(dados_t[1]), step=1)
            
            if st.button("Salvar Tarifas", width='stretch'):
                atualizar_preco_banco(loteria, novo_preco, nova_dez_max)
                st.success("Tarifas atualizadas com segurança!")
                time.sleep(1)
                st.rerun()

    st.divider()
    prog_place = st.empty()
    if st.button("🔄 Atualizar Resultados", width='stretch', type="primary"):
        barra = prog_place.progress(0, text="Iniciando...")
        atualizar_resultados(loteria, barra_progresso=barra)
        prog_place.success("Sincronizado!")
        time.sleep(1)
        prog_place.empty()
        st.rerun()
        
    st.info(f"Último Concurso: **{obter_ultimo_concurso_db(loteria)}**")

# --- DEFINIÇÃO DAS 4 ABAS (A LINHA QUE FALTAVA ESTÁ AQUI) ---
tab1, tab2, tab3, tab4 = st.tabs(["🎯 Gerador", "📊 Histórico", "🏆 Conferência", "📈 Estatísticas"])

# ABA 1: GERADOR & CARRINHO
with tab1:
    conn = obter_conexao()
    lim = conn.execute("SELECT dez_min, dez_max FROM tarifas WHERE loteria=?", (loteria,)).fetchone()
    conn.close()
    m_min, m_max = (lim[0], lim[1]) if lim else (6, 20)
    
    c1, c2 = st.columns(2)
    with c1: qtd_j = st.number_input("Qtd. Jogos:", 1, 100, 1)
    with c2: qtd_d = st.number_input(f"Dezenas ({m_min}-{m_max}):", m_min, m_max, m_min)
    
    # CHAVE DE ATIVAÇÃO DO MACHINE LEARNING
    usar_ia = st.toggle("🧠 Ativar Filtro de Inteligência Artificial (K-Means)", value=False, help="Treina um modelo na hora para sugerir jogos com o mesmo perfil matemático dos sorteios mais frequentes do passado.")
    
    if st.button("➕ Gerar e Adicionar ao Carrinho", width='stretch'):
        jogos = sugerir_jogo(loteria, qtd_j, qtd_d, usar_ia=usar_ia)
        custo_uni = calcular_custo_jogos(loteria, qtd_j, qtd_d) / qtd_j
        for j in jogos:
            st.session_state.carrinho.append({
                "Loteria": loteria.upper(), 
                "Dezenas": ", ".join(map(str, sorted(j))), 
                "Custo Unitário": custo_uni,
                "IA": "🤖 Sim" if usar_ia else "Aleatório"
            })
        st.rerun()

    if st.session_state.carrinho:
        st.divider()
        df_c = pd.DataFrame(st.session_state.carrinho)
        col_c1, col_c2 = st.columns([3, 1])
        with col_c1:
            st.dataframe(df_c, width='stretch', hide_index=True)
            st.metric("Total", f"R$ {df_c['Custo Unitário'].sum():.2f}")
        with col_c2:
            # Download Seguro com Hash SHA-256
            csv_dados = df_c.to_csv(index=False).encode('utf-8')
            hash_arquivo = gerar_hash_sha256(csv_dados)
            
            st.download_button("📥 Baixar Lista (CSV)", csv_dados, "meus_jogos.csv", "text/csv", width='stretch')
            st.caption(f"🔒 SHA-256: `{hash_arquivo[:12]}...`")
            
            if st.button("🗑️ Limpar Carrinho", width='stretch'):
                st.session_state.carrinho = []; st.rerun()
                
        if st.button("💾 CONFIRMAR E SALVAR NO BANCO", type="primary", width='stretch'):
            conn = obter_conexao(); prox = obter_ultimo_concurso_db(loteria) + 1
            for _, r in df_c.iterrows():
                conn.execute("INSERT INTO apostas_usuario (loteria, concurso_alvo, dezenas_jogadas) VALUES (?,?,?)", (r["Loteria"].lower(), prox, r["Dezenas"].replace(" ", "")))
            conn.commit(); conn.close(); st.session_state.carrinho = []; st.success("Salvo com segurança!"); st.rerun()

# ABA 2: HISTÓRICO
with tab2:
    conn = obter_conexao()
    df_h = pd.read_sql_query("SELECT id_concurso as Concurso, data_sorteio as Data, dezenas as Números FROM resultados WHERE loteria = ? ORDER BY id_concurso DESC", conn, params=(loteria,))
    conn.close()
    if not df_h.empty: st.dataframe(df_h, width='stretch', hide_index=True)

# ABA 3: CONFERÊNCIA
with tab3:
    conn = obter_conexao()
    df_p = pd.read_sql_query("SELECT concurso_alvo as Concurso, dezenas_jogadas as 'Suas Dezenas' FROM apostas_usuario WHERE loteria = ? ORDER BY id DESC", conn, params=(loteria,))
    conn.close()
    if not df_p.empty:
        st.dataframe(df_p, width='stretch', hide_index=True)
        if st.button("🔍 Conferir Acertos", width='stretch'):
            res = conferir_resultados(loteria)
            if res is not None: st.table(res)

# ABA 4: ESTATÍSTICAS
with tab4:
    st.header(f"Análise Estatística - {loteria.upper()}")
    df_freq, df_atraso = obter_estatisticas_completas(loteria)
    if df_freq is not None:
        ce1, ce2 = st.columns(2)
        with ce1:
            st.subheader("🔢 Frequência de Sorteio")
            st.dataframe(df_freq.style.bar(subset=['Sorteios'], color='#28a745'), width='stretch', hide_index=True)
        with ce2:
            st.subheader("⏳ Ranking de Atraso")
            st.dataframe(df_atraso.style.background_gradient(subset=['Atraso'], cmap='YlOrRd'), width='stretch', hide_index=True)
    else:
        st.warning("Atualize os resultados para ver as estatísticas.")