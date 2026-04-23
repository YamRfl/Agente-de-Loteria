import os
os.environ.pop("SSLKEYLOGFILE", None)

import streamlit as st
import pandas as pd
import time
import plotly.express as px
import io  

from src.database import inicializar_bd, obter_conexao, obter_ultimo_concurso_db, atualizar_preco_banco, limpar_apostas_banco
from src.collector import atualizar_resultados
from src.generator import sugerir_jogo, calcular_custo_jogos
from src.checker import conferir_resultados
from src.analyzer import obter_estatisticas_completas
from src.auth import (inicializar_bd_auth, registrar_usuario, autenticar_usuario, 
                      simular_pagamento_e_liberar_licenca, listar_todos_usuarios,
                      alterar_senha_usuario, redefinir_senha_esquecida)

st.set_page_config(page_title="Agente IA Loterias - SaaS", layout="wide", page_icon="🍀")

inicializar_bd()
inicializar_bd_auth()

if 'carrinho' not in st.session_state: st.session_state.carrinho = []
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'user' not in st.session_state: st.session_state.user = None

@st.cache_data(show_spinner=False)
def carregar_estatisticas_cacheadas(loteria): return obter_estatisticas_completas(loteria)

@st.cache_data(show_spinner=False)
def carregar_historico_cacheados(loteria):
    conn = obter_conexao()
    df = pd.read_sql_query("SELECT id_concurso as Concurso, data_sorteio as Data, dezenas as Números FROM resultados WHERE loteria = ? ORDER BY id_concurso DESC", conn, params=(loteria,))
    conn.close()
    return df

@st.cache_data(show_spinner=False)
def carregar_apostas_cacheadas(loteria):
    conn = obter_conexao()
    df = pd.read_sql_query("SELECT concurso_alvo as Concurso, dezenas_jogadas as 'Suas Dezenas' FROM apostas_usuario WHERE loteria = ? ORDER BY id DESC", conn, params=(loteria,))
    conn.close()
    return df

st.title("🍀 Agente de IA - Analista de Loterias")

with st.sidebar:
    st.header("🔐 Área do Usuário")
    
    if not st.session_state.logged_in:
        st.info("Versão Gratuita. Crie uma conta para adquirir a licença VIP e desbloquear a IA.")
        tab_log, tab_cad, tab_rec = st.tabs(["Entrar", "Criar Conta", "Esqueci a Senha"])
        
        with tab_log:
            with st.form("form_login"):
                log_email = st.text_input("E-mail")
                log_senha = st.text_input("Senha", type="password")
                submit_log = st.form_submit_button("Acessar Plataforma", type="primary", use_container_width=True)
                if submit_log:
                    sucesso, resposta = autenticar_usuario(log_email, log_senha)
                    if sucesso:
                        st.session_state.logged_in = True
                        st.session_state.user = resposta
                        st.rerun()
                    else: st.error(resposta)
                    
        with tab_cad:
            with st.form("form_cadastro", clear_on_submit=True):
                cad_nome = st.text_input("Nome Completo")
                cad_email = st.text_input("E-mail", help="Seu e-mail principal (ex: nome@dominio.com)")
                cad_senha = st.text_input("Senha", type="password", help="Mínimo 8 caracteres, contendo 1 letra maiúscula, 1 minúscula e 1 número.")
                submit_cad = st.form_submit_button("Cadastrar", use_container_width=True)
                if submit_cad:
                    sucesso, msg = registrar_usuario(cad_nome, cad_email, cad_senha)
                    st.success(msg) if sucesso else st.error(msg)
                    
        with tab_rec:
            st.caption("Recupere o acesso à sua conta.")
            with st.form("form_recuperar", clear_on_submit=True):
                rec_email = st.text_input("E-mail cadastrado")
                rec_senha = st.text_input("Nova Senha", type="password", help="Nova senha com regras de segurança.")
                submit_rec = st.form_submit_button("Redefinir Senha", use_container_width=True)
                if submit_rec:
                    sucesso, msg = redefinir_senha_esquecida(rec_email, rec_senha)
                    st.success(msg) if sucesso else st.error(msg)
    else:
        st.success(f"Bem-vindo(a), {st.session_state.user['nome'].split()[0]}!")
        is_premium = st.session_state.user.get('licenca') is not None
        
        if is_premium:
            st.info("💎 Status: **Assinante VIP**")
            st.caption(f"Licença: `{st.session_state.user['licenca'].split('-')[0]}...`")
        else:
            st.warning("Plano: **Gratuito**")
            st.divider()
            st.markdown("🚀 **Desbloqueie a IA!**")
            if st.button("💳 Simular Pagamento", type="primary", use_container_width=True):
                with st.spinner("Processando..."):
                    time.sleep(2)
                    st.session_state.user['licenca'] = simular_pagamento_e_liberar_licenca(st.session_state.user['email'])
                st.balloons(); st.rerun()
                
        with st.expander("⚙️ Alterar Senha"):
            with st.form("form_alt_senha", clear_on_submit=True):
                alt_senha_antiga = st.text_input("Senha Atual", type="password")
                alt_senha_nova = st.text_input("Nova Senha", type="password")
                submit_alt = st.form_submit_button("Atualizar Senha", use_container_width=True)
                if submit_alt:
                    suc, msg_alt = alterar_senha_usuario(st.session_state.user['email'], alt_senha_antiga, alt_senha_nova)
                    st.success(msg_alt) if suc else st.error(msg_alt)

        if st.button("Sair (Logout)", use_container_width=True):
            st.session_state.logged_in = False; st.session_state.user = None; st.rerun()

    st.divider()
    st.header("⚙️ Loterias")
    loteria = st.selectbox("Modalidade:", ["megasena", "lotofacil", "quina", "lotomania", "duplasena", "timemania", "maismilionaria", "diadesorte"], help="Escolha o jogo que deseja analisar e apostar.")
    
    prog_place = st.empty()
    if st.button("🔄 Sincronizar Sorteios", type="primary", use_container_width=True):
        try:
            atualizar_resultados(loteria, barra_progresso=prog_place.progress(0))
            st.cache_data.clear(); prog_place.empty()
            st.toast(f"Resultados da {loteria.upper()} atualizados com sucesso!", icon="✅")
            time.sleep(1)
            st.rerun()
        except Exception as e:
            st.error("A conexão com a Caixa foi interrompida.")
            
    # RESTAURAÇÃO DA FRASE DE AVISO
    st.caption("⚠️ **Aviso:** Se a atualização travar ou a tela ficar em branco, pressione **F5** (ou recarregue a página) para continuar.")
    st.info(f"Último Concurso: **{obter_ultimo_concurso_db(loteria)}**")
    
    with st.expander("♿ Acessibilidade e Ajuda"):
        st.markdown("""
        * **Contraste:** O sistema se adapta ao tema (Claro/Escuro) do seu Windows ou navegador.
        * **Dicas:** Posicione o mouse sobre os campos e ícones `?` para obter ajuda técnica.
        * **Zoom:** Utilize `Ctrl +` ou `Ctrl -` no teclado para ajustar o tamanho da fonte.
        """)

tabs_names = ["🎯 Gerador (Free/VIP)", "📊 Histórico", "🏆 Conferência", "📈 Estatísticas"]
is_admin = st.session_state.logged_in and st.session_state.user['role'] == 'admin'
if is_admin: tabs_names.append("🛡️ Painel Admin")

tabs = st.tabs(tabs_names)

with tabs[0]:
    conn = obter_conexao()
    lim = conn.execute("SELECT dez_min, dez_max FROM tarifas WHERE loteria=?", (loteria,)).fetchone()
    conn.close()
    m_min, m_max = (lim[0], lim[1]) if lim else (6, 20)
    
    c1, c2 = st.columns(2)
    with c1: qtd_j = st.number_input("Qtd. Jogos:", 1, 100, 1, help="Número de bilhetes a serem gerados.")
    with c2: qtd_d = st.number_input(f"Dezenas ({m_min}-{m_max}):", m_min, m_max, m_min, help="Quantidade de números marcados em cada bilhete.")
    
    usuario_premium = st.session_state.logged_in and st.session_state.user.get('licenca') is not None
    
    if usuario_premium:
        with st.expander("🛠️ Filtros Matemáticos e IA"):
            cf1, cf2, cf3 = st.columns(3)
            with cf1:
                limite_soma = st.slider("Soma das Dezenas", 0, 800, (0, 800), 1)
                limite_fibo = st.slider("Qtd. Fibonacci", 0, m_max, (0, m_max), 1)
                limite_repetidas = st.slider("Repetidas (Últ. Sorteio)", 0, m_max, (0, m_max), 1)
            with cf2:
                limite_pares = st.slider("Qtd. de Pares", 0, m_max, (0, m_max), 1)
                limite_mult3 = st.slider("Qtd. Múlt. de 3", 0, m_max, (0, m_max), 1)
                max_linha = st.number_input("Máx. Linha", 1, 10, 10)
            with cf3:
                limite_primos = st.slider("Qtd. de Primos", 0, m_max, (0, m_max), 1)
                limite_moldura = st.slider("Qtd. Moldura", 0, m_max, (0, m_max), 1)
                max_coluna = st.number_input("Máx. Coluna", 1, 10, 10)
        
        usar_ia = st.toggle("🧠 Ativar IA (K-Means)", value=False, help="Filtra os jogos para corresponder ao cluster matemático mais provável.")
    else:
        st.error("🔒 **Premium Bloqueado** - Adquira uma licença para destravar Filtros e Machine Learning.")
        limite_soma = (0, 800); limite_fibo = (0, m_max); limite_repetidas = (0, m_max)
        limite_pares = (0, m_max); limite_mult3 = (0, m_max); limite_primos = (0, m_max)
        limite_moldura = (0, m_max); max_linha = 10; max_coluna = 10; usar_ia = False

    if st.button("➕ Adicionar ao Carrinho", type="primary", use_container_width=True):
        jogos = sugerir_jogo(loteria, qtd_j, qtd_d, usar_ia=usar_ia, filtro_soma=limite_soma, 
                             filtro_pares=limite_pares, filtro_primos=limite_primos, filtro_fibo=limite_fibo, 
                             filtro_mult3=limite_mult3, filtro_moldura=limite_moldura, filtro_repetidas=limite_repetidas, 
                             limite_linha=max_linha, limite_coluna=max_coluna)
        custo_uni = calcular_custo_jogos(loteria, qtd_j, qtd_d) / qtd_j
        for j in jogos:
            st.session_state.carrinho.append({"Loteria": loteria.upper(), "Dezenas": ", ".join(map(str, sorted(j))), "Custo Unitário": custo_uni, "IA / Filtros": "💎 VIP" if usar_ia or usuario_premium else "Aleatório (Free)"})
        st.rerun()

    if st.session_state.carrinho:
        st.divider()
        df_c = pd.DataFrame(st.session_state.carrinho)
        col_c1, col_c2 = st.columns([3, 1])
        with col_c1:
            st.dataframe(df_c, use_container_width=True, hide_index=True)
            st.metric("Total do Carrinho", f"R$ {df_c['Custo Unitário'].sum():.2f}")
        with col_c2:
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df_c.to_excel(writer, index=False, sheet_name='Meus Jogos')
            excel_dados = buffer.getvalue()
            
            if usuario_premium:
                st.download_button(
                    label="📥 Baixar em Excel", data=excel_dados, 
                    file_name="meus_jogos.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", 
                    use_container_width=True
                )
            else:
                st.button("🔒 Baixar Excel (VIP)", disabled=True, use_container_width=True)
            
            if st.button("🗑️ Limpar Carrinho", use_container_width=True): st.session_state.carrinho = []; st.rerun()
                
        if st.button("💾 CONFIRMAR E SALVAR NO BANCO PARA CONFERÊNCIA", use_container_width=True):
            conn = obter_conexao(); prox = obter_ultimo_concurso_db(loteria) + 1
            for _, r in df_c.iterrows():
                conn.execute("INSERT INTO apostas_usuario (loteria, concurso_alvo, dezenas_jogadas) VALUES (?,?,?)", (r["Loteria"].lower(), prox, r["Dezenas"].replace(" ", "")))
            conn.commit(); conn.close()
            st.cache_data.clear(); st.session_state.carrinho = []
            st.toast("Apostas guardadas com segurança no banco de dados!", icon="💾")
            time.sleep(1); st.rerun()

with tabs[1]:
    df_h = carregar_historico_cacheados(loteria)
    if not df_h.empty: st.dataframe(df_h, use_container_width=True, hide_index=True)

with tabs[2]:
    df_p = carregar_apostas_cacheadas(loteria)
    if not df_p.empty:
        st.dataframe(df_p, use_container_width=True, hide_index=True)
        c_conf1, c_conf2 = st.columns(2)
        with c_conf1:
            if st.button("🔍 Conferir Acertos com Sorteio Oficial", use_container_width=True, type="primary"):
                res = conferir_resultados(loteria)
                if res is not None:
                    st.table(res)
                    if res["Qtd. Acertos"].astype(str).str.isnumeric().any() and res[res["Qtd. Acertos"] != '-']["Qtd. Acertos"].astype(int).max() > 3:
                        st.balloons()
        with c_conf2:
            if st.button("🗑️ Apagar Histórico", use_container_width=True):
                limpar_apostas_banco(loteria); st.cache_data.clear(); st.rerun()
    else:
        st.info("Você ainda não tem jogos salvos para esta loteria.")

with tabs[3]:
    st.header(f"Análise Estatística - {loteria.upper()}")
    df_freq, df_atraso = carregar_estatisticas_cacheadas(loteria)
    if df_freq is not None:
        modo_visao = st.radio("Visão:", ["📊 Gráficos (Top 20)", "📝 Tabelas Completas"], horizontal=True, label_visibility="collapsed")
        c_est1, c_est2 = st.columns(2)
        if "Gráficos" in modo_visao:
            with c_est1: st.plotly_chart(px.bar(df_freq.head(20).astype({'Número': str}), x='Número', y='Sorteios', title="Frequência (Mais Sorteados)", color='Sorteios', color_continuous_scale='Blues'), use_container_width=True)
            with c_est2: st.plotly_chart(px.bar(df_atraso.head(20).astype({'Número': str}), x='Número', y='Atraso', title="Atrasos (Mais Tempo Sem Sair)", color='Atraso', color_continuous_scale='Oranges'), use_container_width=True)
        else:
            with c_est1: st.dataframe(df_freq.style.format(precision=2).bar(subset=['Sorteios'], color='#1f77b4'), use_container_width=True, hide_index=True)
            with c_est2: st.dataframe(df_atraso.style.format(precision=2).background_gradient(subset=['Atraso'], cmap='Oranges'), use_container_width=True, hide_index=True)

if is_admin:
    with tabs[4]:
        st.header("🛡️ Centro de Comando e Controle")
        st.subheader("Base de Clientes")
        st.dataframe(pd.DataFrame(listar_todos_usuarios(), columns=["ID", "Nome", "E-mail", "Cargo", "Chave de Licença"]), use_container_width=True, hide_index=True)
        
        st.divider()
        st.subheader("Configurações Globais de Tarifas")
        conn = obter_conexao()
        dados_t = conn.execute("SELECT preco_base, dez_max FROM tarifas WHERE loteria=?", (loteria,)).fetchone()
        conn.close()
        
        if dados_t:
            ca1, ca2 = st.columns(2)
            with ca1: novo_preco = st.number_input("Alterar Preço da Aposta Base:", value=float(dados_t[0]), step=0.50)
            with ca2: nova_dez_max = st.number_input("Alterar Limite Máximo de Dezenas:", value=int(dados_t[1]), step=1)
            
            if st.button("💾 Salvar Novas Tarifas no Banco", type="primary"):
                atualizar_preco_banco(loteria, novo_preco, nova_dez_max)
                st.cache_data.clear() 
                st.success("Tarifas do sistema atualizadas e aplicadas para todos os usuários!")