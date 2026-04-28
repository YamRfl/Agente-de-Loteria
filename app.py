import os
os.environ.pop("SSLKEYLOGFILE", None)

import streamlit as st
import pandas as pd
import time
import plotly.express as px
import io  

from src.database import inicializar_bd, obter_conexao, obter_ultimo_concurso_db, atualizar_preco_banco, limpar_apostas_banco
from src.collector import atualizar_resultados, sincronizar_todas_loterias
from src.generator import sugerir_jogo, calcular_custo_jogos
from src.checker import conferir_resultados
from src.analyzer import obter_estatisticas_completas
from src.auth import (inicializar_bd_auth, registrar_usuario, autenticar_usuario, 
                      simular_pagamento_e_liberar_licenca, listar_todos_usuarios,
                      alterar_senha_usuario, solicitar_token_recuperacao, redefinir_senha_com_token,
                      resetar_senha_por_admin)

st.set_page_config(page_title="Agente IA Loterias - SaaS", layout="wide", page_icon="🍀")

# ==========================================
# INJEÇÃO ESTÉTICA (CSS) - REDUÇÃO DE ESPAÇOS
# ==========================================
st.markdown("""
<style>
    [data-testid="stSidebar"] [data-testid="stSidebarUserContent"] {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
    .stButton>button {
        min-height: 2rem;
        padding-top: 0.2rem !important;
        padding-bottom: 0.2rem !important;
    }
    [data-testid="stSidebar"] hr {
        margin-top: 0.8rem !important;
        margin-bottom: 0.8rem !important;
    }
    [data-testid="stSidebar"] > div:first-child {
        overflow-y: auto !important;
    }
    [data-testid="stSidebar"] > div:first-child::-webkit-scrollbar {
        width: 6px;
        background-color: transparent;
    }
    [data-testid="stSidebar"] > div:first-child::-webkit-scrollbar-thumb {
        background-color: rgba(120, 120, 120, 0.4);
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

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

# ==========================================
# CABEÇALHO COM BOTÃO "SAIR"
# ==========================================
col_titulo, col_sair = st.columns([8, 2])
with col_titulo:
    st.title("🍀 Agente de IA - Analista de Loterias")
with col_sair:
    if st.session_state.logged_in:
        st.markdown("<div style='margin-top: 25px;'></div>", unsafe_allow_html=True)
        if st.button("🚪 Sair da Conta", type="secondary", width="stretch"):
            st.session_state.logged_in = False
            st.session_state.user = None
            st.rerun()

with st.sidebar:
    st.subheader("⚙️ Seleção de Loteria")
    loteria = st.selectbox("Modalidade", ["megasena", "lotofacil", "quina", "lotomania", "duplasena", "timemania", "maismilionaria", "diadesorte"], label_visibility="collapsed", help="Escolha a loteria.")
    
    prog_place = st.empty()
    status_text = st.empty()
    
    col_sync1, col_sync2 = st.columns(2)
    with col_sync1:
        if st.button("🔄 Atual", type="primary", width="stretch"):
            try:
                atualizar_resultados(loteria, barra_progresso=prog_place.progress(0))
                st.cache_data.clear(); prog_place.empty()
                st.toast(f"Resultados da {loteria.upper()} atualizados!", icon="✅")
                time.sleep(1); st.rerun()
            except Exception:
                st.error("Conexão interrompida.")
                
    with col_sync2:
        if st.button("⚡ TODAS", type="secondary", width="stretch"):
            try:
                sincronizar_todas_loterias(barra_progresso=prog_place.progress(0), texto_status=status_text)
                st.cache_data.clear(); prog_place.empty(); status_text.empty()
                st.toast("Banco de dados sincronizado!", icon="🚀")
                time.sleep(1); st.rerun()
            except Exception:
                st.error("Conexão interrompida.")
            
    st.caption(f"Último Concurso Sincronizado: **{obter_ultimo_concurso_db(loteria)}**")
    st.divider()

    st.subheader("🔐 Área do Usuário")
    if not st.session_state.logged_in:
        tab_log, tab_cad, tab_rec = st.tabs(["Entrar", "Criar Conta", "Recuperar"])
        with tab_log:
            with st.form("form_login"):
                log_email = st.text_input("E-mail", placeholder="E-mail de acesso", label_visibility="collapsed")
                log_senha = st.text_input("Senha", type="password", placeholder="Sua senha", label_visibility="collapsed")
                if st.form_submit_button("Acessar", type="primary", width="stretch"):
                    suc, res = autenticar_usuario(log_email, log_senha)
                    if suc:
                        st.session_state.logged_in = True
                        st.session_state.user = res
                        st.rerun()
                    else: st.error(res)
        with tab_cad:
            with st.form("form_cadastro", clear_on_submit=True):
                cad_nome = st.text_input("Nome Completo", placeholder="Nome", label_visibility="collapsed")
                cad_email = st.text_input("E-mail", placeholder="E-mail", label_visibility="collapsed")
                cad_senha = st.text_input("Senha", type="password", placeholder="Senha Forte", label_visibility="collapsed")
                if st.form_submit_button("Cadastrar Conta", width="stretch"):
                    s, m = registrar_usuario(cad_nome, cad_email, cad_senha)
                    if s: st.success(m)
                    else: st.error(m)
        with tab_rec:
            with st.form("form_pedir_token"):
                st.caption("1º Passo: Solicite o código")
                req_email = st.text_input("E-mail", placeholder="E-mail", label_visibility="collapsed")
                if st.form_submit_button("✉️ Receber Código", width="stretch"):
                    with st.spinner("Enviando..."):
                        s, m = solicitar_token_recuperacao(req_email)
                        if s: st.success(m)
                        else: st.error(m)
            with st.form("form_redefinir_senha", clear_on_submit=True):
                st.caption("2º Passo: Redefina sua senha")
                rec_email = st.text_input("Confirmar E-mail", label_visibility="collapsed")
                rec_token = st.text_input("Código de 6 dígitos", label_visibility="collapsed")
                rec_senha = st.text_input("Nova Senha Forte", type="password", label_visibility="collapsed")
                if st.form_submit_button("Salvar Nova Senha", type="primary", width="stretch"):
                    s, m = redefinir_senha_com_token(rec_email, rec_token, rec_senha)
                    if s: st.success(m)
                    else: st.error(m)
    else:
        st.success(f"Olá, {st.session_state.user['nome'].split()[0]}!")
        if st.session_state.user.get('licenca'): st.info("💎 Status: **Assinante VIP**")
        else:
            st.warning("Plano: **Gratuito**")
            if st.button("💳 Simular Pagamento", type="primary", width="stretch"):
                with st.spinner("Processando..."):
                    time.sleep(2)
                    st.session_state.user['licenca'] = simular_pagamento_e_liberar_licenca(st.session_state.user['email'])
                st.balloons(); st.rerun()
                
        if not st.session_state.user.get('trocar_senha'):
            with st.expander("👤 Configurações da Conta"):
                with st.form("form_alt_senha", clear_on_submit=True):
                    alt_antiga = st.text_input("Senha Atual", type="password", label_visibility="collapsed")
                    alt_nova = st.text_input("Nova Senha", type="password", label_visibility="collapsed")
                    if st.form_submit_button("Atualizar Senha", width="stretch"):
                        s, m = alterar_senha_usuario(st.session_state.user['email'], alt_antiga, alt_nova)
                        if s: st.success(m)
                        else: st.error(m)

        if st.button("Sair (Logout)", width="stretch"):
            st.session_state.logged_in = False; st.session_state.user = None; st.rerun()

# --- FIREWALL: TROCA DE SENHA OBRIGATÓRIA ---
if st.session_state.logged_in and st.session_state.user.get('trocar_senha'):
    st.warning("🛡️ **Segurança Crítica:** Sua senha foi resetada. Por favor, defina uma nova senha pessoal para continuar.")
    c_l1, c_l2, c_l3 = st.columns([1, 2, 1])
    with c_l2:
        with st.form("f_troca_obrigatoria"):
            s_t = st.text_input("Senha Temporária Recebida", type="password")
            s_n = st.text_input("Nova Senha Forte", type="password")
            s_c = st.text_input("Confirme a Nova Senha", type="password")
            if st.form_submit_button("Atualizar e Acessar Sistema", type="primary", width="stretch"):
                if s_n != s_c: st.error("As senhas não coincidem.")
                else:
                    suc, msg = alterar_senha_usuario(st.session_state.user['email'], s_t, s_n)
                    if suc:
                        st.success("Senha protegida com sucesso!"); st.session_state.user['trocar_senha'] = 0
                        time.sleep(1.5); st.rerun()
                    else: st.error(msg)
    st.stop()

# ==========================================
# ABAS PRINCIPAIS DO SISTEMA
# ==========================================
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
    with c1: qtd_j = st.number_input("Qtd. Jogos:", 1, 100, 1)
    with c2: qtd_d = st.number_input(f"Dezenas ({m_min}-{m_max}):", m_min, m_max, m_min)
    
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
        usar_ia = st.toggle("🧠 Ativar IA (K-Means)", value=False)
    else:
        st.error("🔒 **Premium Bloqueado**"); limite_soma=(0,800); limite_fibo=(0,m_max); limite_repetidas=(0,m_max); limite_pares=(0,m_max); limite_mult3=(0,m_max); limite_primos=(0,m_max); limite_moldura=(0,m_max); max_linha=10; max_coluna=10; usar_ia=False

    custo_previsto = calcular_custo_jogos(loteria, qtd_j, qtd_d)
    st.markdown(f"💰 **Custo Estimado da Aposta:** R$ {custo_previsto:.2f}")

    if st.button("➕ Adicionar ao Carrinho", type="primary", width="stretch"):
        jogos = sugerir_jogo(loteria, qtd_j, qtd_d, usar_ia=usar_ia, filtro_soma=limite_soma, filtro_pares=limite_pares, filtro_primos=limite_primos, filtro_fibo=limite_fibo, filtro_mult3=limite_mult3, filtro_moldura=limite_moldura, filtro_repetidas=limite_repetidas, limite_linha=max_linha, limite_coluna=max_coluna)
        custo_uni = custo_previsto / qtd_j if qtd_j > 0 else 0
        for j in jogos:
            st.session_state.carrinho.append({"Loteria": loteria.upper(), "Dezenas": ", ".join(map(str, sorted(j))), "Custo Unitário": custo_uni, "IA / Filtros": "💎 VIP" if usar_ia or usuario_premium else "Aleatório"})
        st.rerun()

    if st.session_state.carrinho:
        st.divider(); df_c = pd.DataFrame(st.session_state.carrinho)
        col_c1, col_c2 = st.columns([3, 1])
        with col_c1:
            st.dataframe(df_c, width="stretch", hide_index=True)
            st.metric("Total do Carrinho", f"R$ {df_c['Custo Unitário'].sum():.2f}")
        with col_c2:
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer: df_c.to_excel(writer, index=False, sheet_name='Jogos')
            if usuario_premium: st.download_button(label="📥 Baixar Excel", data=buffer.getvalue(), file_name="meus_jogos.xlsx", width="stretch")
            if st.button("🗑️ Limpar Carrinho", width="stretch"): st.session_state.carrinho = []; st.rerun()
                
        if st.button("💾 SALVAR NO BANCO PARA CONFERÊNCIA", width="stretch"):
            conn = obter_conexao(); prox = obter_ultimo_concurso_db(loteria) + 1
            for _, r in df_c.iterrows(): conn.execute("INSERT INTO apostas_usuario (loteria, concurso_alvo, dezenas_jogadas) VALUES (?,?,?)", (r["Loteria"].lower(), prox, r["Dezenas"].replace(" ", "")))
            conn.commit(); conn.close(); st.cache_data.clear(); st.session_state.carrinho = []; st.toast("Salvo!"); time.sleep(1); st.rerun()

with tabs[1]:
    df_h = carregar_historico_cacheados(loteria)
    if not df_h.empty: st.dataframe(df_h, width="stretch", hide_index=True)

with tabs[2]:
    df_p = carregar_apostas_cacheadas(loteria)
    if not df_p.empty:
        st.dataframe(df_p, width="stretch", hide_index=True)
        if st.button("🔍 Conferir Acertos com Sorteio Oficial", type="primary", width="stretch"):
            res = conferir_resultados(loteria)
            if res is not None:
                st.table(res)
                if res["Qtd. Acertos"].astype(str).str.isnumeric().any() and res[res["Qtd. Acertos"] != '-']["Qtd. Acertos"].astype(int).max() > 3: st.balloons()
        if st.button("🗑️ Apagar Histórico de Apostas", width="stretch"): limpar_apostas_banco(loteria); st.cache_data.clear(); st.rerun()
    else: st.info("Nenhuma aposta salva.")

with tabs[3]:
    st.header(f"Análise Estatística - {loteria.upper()}")
    df_f, df_a = carregar_estatisticas_cacheadas(loteria)
    if df_f is not None:
        c_e1, c_e2 = st.columns(2)
        c_e1.plotly_chart(px.bar(df_f.head(20).astype({'Número': str}), x='Número', y='Sorteios', title="Frequência", color='Sorteios', color_continuous_scale='Blues'), width="stretch")
        c_e2.plotly_chart(px.bar(df_a.head(20).astype({'Número': str}), x='Número', y='Atraso', title="Maiores Atrasos", color='Atraso', color_continuous_scale='Oranges'), width="stretch")

if is_admin:
    with tabs[4]:
        st.header("🛡️ Centro de Comando Admin")
        u_list = listar_todos_usuarios()
        st.dataframe(pd.DataFrame(u_list, columns=["ID", "Nome", "E-mail", "Cargo", "Licença", "Troca Pendente"]), width="stretch", hide_index=True)
        
st.divider()
st.subheader("🔑 Reset de Segurança (Senha Temporária)")

with st.form("f_adm_reset"):
    alvo = st.text_input("E-mail do Usuário")
    # Correção: use_container_width em vez de width="stretch"
    if st.form_submit_button("Gerar Senha Temporária", type="primary", use_container_width=True):
        if alvo:
            # Chamada à função do src/auth.py
            suc, p_temp = resetar_senha_por_admin(alvo)
            
            if suc:
                # Agora a variável p_temp está corretamente definida
                st.success(f"Resetado! Senha: **{p_temp}**") 
                st.warning("⚠️ Forneça esta senha ao usuário. Ela expira após o primeiro login.")
            else: 
                # Caso o usuário não seja encontrado ou ocorra erro no banco
                st.error(p_temp) 
        else:
            st.error("Por favor, insira um e-mail para realizar o reset.")
        
        st.divider(); st.subheader("Configurações Globais de Tarifas")
        conn = obter_conexao(); d_t = conn.execute("SELECT preco_base, dez_max FROM tarifas WHERE loteria=?", (loteria,)).fetchone(); conn.close()
        if d_t:
            ca1, ca2 = st.columns(2)
            n_p = ca1.number_input("Preço Base", value=float(d_t[0])); n_d = ca2.number_input("Máx Dezenas", value=int(d_t[1]))
            if st.button("💾 Salvar Tarifas"): atualizar_preco_banco(loteria, n_p, n_d); st.cache_data.clear(); st.success("Salvo!"); time.sleep(1); st.rerun()