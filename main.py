import streamlit as st
from client import ClienteWeb
from datetime import datetime
import json
import os

# Caminho do arquivo de tópicos globais
TOPICOS_PATH = "topicos.json"

# Funções auxiliares para ler e salvar tópicos globais
def carregar_topicos():
    if os.path.exists(TOPICOS_PATH):
        with open(TOPICOS_PATH, "r") as f:
            return set(json.load(f))
    return set()

def salvar_topicos(topicos):
    with open(TOPICOS_PATH, "w") as f:
        json.dump(sorted(list(topicos)), f)

# Inicializa cliente e topicos
if 'cliente' not in st.session_state:
    st.session_state.cliente = ClienteWeb()
if 'topicos' not in st.session_state:
    st.session_state.topicos = carregar_topicos()
if 'mensagens_por_topico' not in st.session_state:
    st.session_state.mensagens_por_topico = {}

cliente = st.session_state.cliente

st.set_page_config(page_title="MQTT Chat Seguro", layout="wide")
st.markdown("""
    <style>
    .status-bar {
        padding: 10px;
        margin-bottom: 15px;
        border-radius: 5px;
        color: white;
        font-weight: bold;
        text-align: center;
    }
    .connected { background-color: #28a745; }
    .disconnected { background-color: #dc3545; }
    .chat-box {
        height: 400px;
        overflow-y: auto;
        padding: 10px;
        border: 1px solid #ddd;
        border-radius: 10px;
        background-color: #f8f9fa;
    }
    .msg-bubble {
        margin-bottom: 10px;
        padding: 8px 12px;
        background-color: #e2f0d9;
        border-radius: 10px;
        display: inline-block;
        max-width: 80%;
    }
    .topico {
        font-weight: bold;
        color: #007bff;
    }
    .timestamp {
        font-size: 0.75em;
        color: #666;
    }
    </style>
""", unsafe_allow_html=True)

# Título e status de conexão
st.title("💬 MQTT Chat Seguro")

if not cliente.conectado:
    nome = st.text_input("Digite seu nome de cliente:", key="nome")
    if st.button("🔐 Conectar e autenticar"):
        if nome.strip():
            sucesso, msg = cliente.conectar(nome.strip())
            if sucesso:
                st.success(msg)
            else:
                st.error(msg)
        else:
            st.warning("Digite um nome para conectar.")
else:
    st.markdown('<div class="status-bar connected">🔒 Conectado com sucesso</div>', unsafe_allow_html=True)

    col1, col2 = st.columns([3, 1])
    with col2:
        st.subheader("Gerenciar Tópicos")
        novo_topico = st.text_input("Criar novo tópico")
        if st.button("Criar Tópico") and novo_topico.strip():
            st.session_state.topicos.add(novo_topico.strip())
            salvar_topicos(st.session_state.topicos)
            st.success(f"Tópico '{novo_topico.strip()}' criado com sucesso!")

        topico_ativo = st.selectbox("Selecione um tópico", sorted(list(st.session_state.topicos)))
        if st.button("Assinar"):
            cliente.enviar_sub(topico_ativo)
            st.success(f"Assinado em '{topico_ativo}'")

    with col1:
        st.subheader(f"Chat - Tópico: {topico_ativo}")
        st.markdown('<div class="chat-box">', unsafe_allow_html=True)
        mensagens = st.session_state.mensagens_por_topico.get(topico_ativo, [])
        for msg in mensagens[::-1]:
            agora = datetime.now().strftime("%H:%M")
            st.markdown(f"<div class='msg-bubble'><div class='topico'>{msg}</div><div class='timestamp'>{agora}</div></div>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")
    with st.form("form_msg", clear_on_submit=True):
        col_msg, col_btn = st.columns([5, 1])
        with col_msg:
            mensagem = st.text_input("Digite sua mensagem:", key="nova_msg")
        with col_btn:
            enviar = st.form_submit_button("Enviar")

        if enviar and mensagem.strip():
            try:
                cliente.enviar_pub(topico_ativo, mensagem.strip())
                st.session_state.mensagens_por_topico.setdefault(topico_ativo, []).append(f"{cliente.nome_cliente}: {mensagem.strip()}")
            except Exception as e:
                st.error(f"Erro ao enviar: {e}")

    # Atualiza mensagens recebidas
    for msg in cliente.mensagens:
        if "]" in msg:
            partes = msg.split("]", 1)
            topico = partes[0].strip("[]")
            conteudo = partes[1].strip()
            st.session_state.topicos.add(topico)
            salvar_topicos(st.session_state.topicos)
            st.session_state.mensagens_por_topico.setdefault(topico, []).append(conteudo)
    cliente.mensagens.clear()
