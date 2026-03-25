import streamlit as st
import pandas as pd
import time
import hashlib
import plotly.express as px
import io  

from src.database import inicializar_bd, obter_conexao, obter_ultimo_concurso_db, atualizar_preco_banco, limpar_apostas_banco
from src.collector import atualizar_resultados
from src.generator import sugerir_jogo, calcular_custo_jogos
from src.checker import conferir_resultados
from src.analyzer import obter_estatisticas_completas

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

# --- DEFINIÇÃO DAS 4 ABAS ---
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
    
    # --- PAINEL DE FILTROS MANUAIS COMPLETOS ---
    with st.expander("🛠️ Filtros Matemáticos Manuais (Avançado)"):
        st.caption("⚠️ Atenção: Combinar muitos filtros rígidos simultaneamente forçará o sistema a ignorar regras para evitar travamento. Deixe os limites abertos naquilo que não deseja filtrar.")
        cf1, cf2, cf3 = st.columns(3)
        with cf1:
            limite_soma = st.slider("Soma das Dezenas", min_value=0, max_value=800, value=(0, 800), step=1)
            limite_fibo = st.slider("Qtd. Fibonacci", min_value=0, max_value=m_max, value=(0, m_max), step=1)
            limite_repetidas = st.slider("Repetidas (Últ. Sorteio)", min_value=0, max_value=m_max, value=(0, m_max), step=1)
        with cf2:
            limite_pares = st.slider("Qtd. de Pares", min_value=0, max_value=m_max, value=(0, m_max), step=1)
            limite_mult3 = st.slider("Qtd. Múltiplos de 3", min_value=0, max_value=m_max, value=(0, m_max), step=1)
            max_linha = st.number_input("Max. dezenas por Linha", min_value=1, max_value=10, value=10)
        with cf3:
            limite_primos = st.slider("Qtd. de Primos", min_value=0, max_value=m_max, value=(0, m_max), step=1)
            limite_moldura = st.slider("Qtd. na Moldura", min_value=0, max_value=m_max, value=(0, m_max), step=1)
            max_coluna = st.number_input("Max. dezenas por Coluna", min_value=1, max_value=10, value=10)
    
    usar_ia = st.toggle("🧠 Ativar Filtro de Inteligência Artificial (K-Means)", value=False, help="Treina um modelo na hora para sugerir jogos com o mesmo perfil matemático dos sorteios mais frequentes do passado.")
    
    if st.button("➕ Gerar e Adicionar ao Carrinho", width='stretch', type="primary"):
        jogos = sugerir_jogo(
            loteria, qtd_j, qtd_d, 
            usar_ia=usar_ia,
            filtro_soma=limite_soma,
            filtro_pares=limite_pares,
            filtro_primos=limite_primos,
            filtro_fibo=limite_fibo,
            filtro_mult3=limite_mult3,
            filtro_moldura=limite_moldura,
            filtro_repetidas=limite_repetidas,
            limite_linha=max_linha,
            limite_coluna=max_coluna
        )
        
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
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df_c.to_excel(writer, index=False, sheet_name='Meus Jogos')
            excel_dados = buffer.getvalue()
            
            # O hash continua sendo gerado por segurança, mas não é mais exibido na tela
            hash_arquivo = gerar_hash_sha256(excel_dados)
            
            st.download_button(
                label="📥 Baixar Lista (Excel)", 
                data=excel_dados, 
                file_name="meus_jogos.xlsx", 
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", 
                width='stretch'
            )
            
            if st.button("🗑️ Limpar Carrinho", width='stretch'):
                st.session_state.carrinho = []; st.rerun()
                
        if st.button("💾 CONFIRMAR E SALVAR NO BANCO", width='stretch'):
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
        
        c_conf1, c_conf2 = st.columns(2)
        with c_conf1:
            if st.button("🔍 Conferir Acertos", width='stretch', type="primary"):
                res = conferir_resultados(loteria)
                if res is not None: st.table(res)
                
        with c_conf2:
            if st.button("🗑️ Apagar Histórico de Jogos", width='stretch'):
                limpar_apostas_banco(loteria)
                st.success("Jogos salvos foram apagados com sucesso!")
                time.sleep(1)
                st.rerun()
    else:
        st.info("Você ainda não tem jogos salvos para esta loteria. Vá até a aba 'Gerador' para adicionar!")

# ABA 4: ESTATÍSTICAS COM ALTERNÂNCIA (GRÁFICO / TABELA)
with tab4:
    st.header(f"Análise Estatística - {loteria.upper()}")
    df_freq, df_atraso = obter_estatisticas_completas(loteria)
    
    if df_freq is not None:
        modo_visao = st.radio(
            "Modo de Exibição:", 
            ["📊 Gráficos Interativos (Top 20)", "📝 Tabelas Completas"], 
            horizontal=True,
            label_visibility="collapsed"
        )
        
        st.divider()
        c1, c2 = st.columns(2)
        
        if "Gráficos" in modo_visao:
            top_freq = df_freq.head(20).copy()
            top_atraso = df_atraso.head(20).copy()
            top_freq['Número'] = top_freq['Número'].astype(str)
            top_atraso['Número'] = top_atraso['Número'].astype(str)

            with c1:
                st.subheader("🔥 Top 20 - Mais Sorteados")
                fig_freq = px.bar(
                    top_freq, x='Número', y='Sorteios', 
                    text='Sorteios', color='Sorteios', 
                    color_continuous_scale='Greens'
                )
                fig_freq.update_layout(xaxis_type='category', showlegend=False, margin=dict(l=0, r=0, t=30, b=0))
                fig_freq.update_traces(textposition='outside')
                st.plotly_chart(fig_freq, use_container_width=True)

            with c2:
                st.subheader("⏳ Top 20 - Maiores Atrasos")
                fig_atraso = px.bar(
                    top_atraso, x='Número', y='Atraso', 
                    text='Atraso', color='Atraso', 
                    color_continuous_scale='Reds'
                )
                fig_atraso.update_layout(xaxis_type='category', showlegend=False, margin=dict(l=0, r=0, t=30, b=0))
                fig_atraso.update_traces(textposition='outside')
                st.plotly_chart(fig_atraso, use_container_width=True)
                
        else:
            with c1:
                st.subheader("🔥 Frequência Completa")
                # Formatando os valores numéricos com 2 casas decimais usando .format(precision=2)
                st.dataframe(df_freq.style.format(precision=2).bar(subset=['Sorteios'], color='#28a745'), width='stretch', hide_index=True)

            with c2:
                st.subheader("⏳ Atrasos Completos")
                # Aplicando também nos atrasos para manter simetria visual
                st.dataframe(df_atraso.style.format(precision=2).background_gradient(subset=['Atraso'], cmap='YlOrRd'), width='stretch', hide_index=True)

    else:
        st.warning("Atualize os resultados na barra lateral para gerar os gráficos estatísticos.")