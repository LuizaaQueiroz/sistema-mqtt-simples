import streamlit as st
from client import ClienteWeb
from datetime import datetime

# Inicializa cliente
if 'cliente' not in st.session_state:
    st.session_state.cliente = ClienteWeb()

cliente = st.session_state.cliente

st.set_page_config(page_title="Chat Seguro MQTT-like", layout="centered")
st.markdown("""
    <style>
    .chat-box {
        border: 1px solid #ccc;
        border-radius: 10px;
        padding: 10px;
        background-color: #f9f9f9;
        max-height: 300px;
        overflow-y: auto;
    }
    .mensagem {
        margin-bottom: 10px;
    }
    .topico {
        font-weight: bold;
        color: #1f77b4;
    }
    .hora {
        font-size: 0.8em;
        color: #888;
    }
    </style>
""", unsafe_allow_html=True)

st.title("💬 Chat Seguro - Cliente MQTT-like")

# Conectar e autenticar
if not cliente.conectado:
    if st.button("🔐 Conectar e autenticar"):
        sucesso, msg = cliente.conectar()
        if sucesso:
            st.success(msg)
        else:
            st.error(msg)
else:
    st.success("Conectado e autenticado com sucesso.")

    # Escolha de tópico
    st.sidebar.header("Tópico de Conversa")
    topico_ativo = st.sidebar.text_input("Nome do tópico", value="chat")
    if st.sidebar.button("Assinar tópico"):
        cliente.enviar_sub(topico_ativo)
        st.sidebar.success(f"Assinado em '{topico_ativo}'")

    # Área de mensagens
    st.subheader(f"💭 Conversa no tópico: {topico_ativo}")
    with st.container():
        st.markdown('<div class="chat-box">', unsafe_allow_html=True)
        for msg in cliente.mensagens[-20:][::-1]:
            agora = datetime.now().strftime("%H:%M")
            st.markdown(f"<div class='mensagem'><span class='topico'>{msg}</span><br><span class='hora'>{agora}</span></div>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # Campo de envio
    st.markdown("---")
    st.text_input("Digite sua mensagem:", key="nova_msg")
    if st.button("Enviar mensagem"):
        texto = st.session_state.nova_msg.strip()
        if texto:
            try:
                cliente.enviar_pub(topico_ativo, texto)
                st.session_state.nova_msg = ""
            except Exception as e:
                st.error(f"Erro ao enviar: {e}")
