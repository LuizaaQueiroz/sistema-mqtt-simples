import streamlit as st
from client import ClienteWeb
import json
import os
import random
import string
import time
from streamlit_autorefresh import st_autorefresh
from datetime import datetime

TOPICOS_PATH = "json/topicos.json"
ADMINS_PATH = "json/admins.json"
SENHAS_TOPICO_PATH = "json/senhas_topicos.json"
PRIVACIDADE_PATH = "json/privacidade_topicos.json"
MEMBROS_PATH = "json/membros_topicos.json"

def carregar_json(caminho):
    if os.path.exists(caminho) and os.path.getsize(caminho) > 0:
        with open(caminho, "r") as f:
            return json.load(f)
    return {}

def salvar_json(caminho, data):
    with open(caminho, "w") as f:
        json.dump(data, f, indent=2)

# Estado Streamlit
if 'cliente' not in st.session_state:
    st.session_state.cliente = ClienteWeb()
if 'topicos' not in st.session_state:
    st.session_state.topicos = set(carregar_json(TOPICOS_PATH))
if 'mensagens_por_topico' not in st.session_state:
    st.session_state.mensagens_por_topico = {}
if 'admins' not in st.session_state:
    st.session_state.admins = carregar_json(ADMINS_PATH)
if 'senhas_topico' not in st.session_state:
    st.session_state.senhas_topico = carregar_json(SENHAS_TOPICO_PATH)
if 'privacidade_topicos' not in st.session_state:
    st.session_state.privacidade_topicos = carregar_json(PRIVACIDADE_PATH)
if 'membros_topicos' not in st.session_state:
    st.session_state.membros_topicos = carregar_json(MEMBROS_PATH)

cliente = st.session_state.cliente

st.set_page_config(page_title="MQTT Chat Seguro", layout="wide")
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
    st_autorefresh(interval=3000, key="atualizacao_mensagens")

    # Processa mensagens recebidas
    for msg in cliente.mensagens:
        if "]" in msg:
            partes = msg.split("]", 1)
            topico_msg = partes[0].strip("[]")
            conteudo = partes[1].strip()
            st.session_state.topicos.add(topico_msg)
            salvar_json(TOPICOS_PATH, sorted(list(st.session_state.topicos)))
            st.session_state.mensagens_por_topico.setdefault(topico_msg, []).append(conteudo)
    cliente.mensagens.clear()

    col1, col2 = st.columns([3, 1])

    with col2:
        st.subheader("Gerenciar Tópicos")

        novo_topico = st.text_input("Nome do novo tópico:")
        tipo_privacidade = st.radio("Tipo de Tópico:", ["Público", "Privado"], horizontal=True)

        if st.button("Criar Tópico") and novo_topico.strip():
            topico = novo_topico.strip()
            st.session_state.topicos.add(topico)
            salvar_json(TOPICOS_PATH, sorted(list(st.session_state.topicos)))

            st.session_state.admins[topico] = cliente.nome_cliente
            salvar_json(ADMINS_PATH, st.session_state.admins)

            priv = "publico" if tipo_privacidade == "Público" else "privado"
            st.session_state.privacidade_topicos[topico] = priv
            salvar_json(PRIVACIDADE_PATH, st.session_state.privacidade_topicos)

            if priv == "privado":
                st.session_state.membros_topicos.setdefault(topico, []).append(cliente.nome_cliente)
                salvar_json(MEMBROS_PATH, st.session_state.membros_topicos)

            # ✅ Assina o admin automaticamente
            cliente.enviar_sub(topico)
            st.success(f"Tópico '{topico}' criado como {priv}. Você foi automaticamente inscrito.")

        topicos_lista = sorted(list(st.session_state.topicos))
        topico_ativo = st.selectbox("Selecione um tópico", topicos_lista)

        if topico_ativo:
            priv = st.session_state.privacidade_topicos.get(topico_ativo, "publico")
            pode_entrar = False

            if priv == "publico":
                pode_entrar = True
            elif cliente.nome_cliente == st.session_state.admins.get(topico_ativo):
                pode_entrar = True
            else:
                senha_digitada = st.text_input(f"Digite a senha para o tópico '{topico_ativo}':", type="password", key=f"senha_{topico_ativo}")
                if st.button("Confirmar Senha", key=f"btn_senha_{topico_ativo}"):
                    dados_senha = st.session_state.senhas_topico.get(topico_ativo)
                    if dados_senha:
                        senha_correta = dados_senha.get("senha")
                        timestamp_gerado = dados_senha.get("timestamp")
                        agora = int(time.time())
                        if agora - timestamp_gerado > 7200:
                            st.error("⚠️ A senha expirou. Peça ao administrador para gerar uma nova.")
                        elif senha_digitada == senha_correta:
                            pode_entrar = True
                            st.success("Senha correta! Você foi inscrito no tópico.")
                        else:
                            st.error("Senha incorreta.")
                    else:
                        st.error("Nenhuma senha ativa para este tópico.")

            if st.button("Assinar") and pode_entrar:
                cliente.enviar_sub(topico_ativo)
                st.success(f"Assinado em '{topico_ativo}'")

            if st.session_state.admins.get(topico_ativo) == cliente.nome_cliente:
                st.markdown(f"🛡️ Você é o administrador de '{topico_ativo}'")

                # Exibir senha atual se ainda válida
                dados_senha = st.session_state.senhas_topico.get(topico_ativo)
                agora = int(time.time())
                if dados_senha:
                    senha_atual = dados_senha.get("senha")
                    timestamp_gerado = dados_senha.get("timestamp")
                    tempo_restante = max(0, 7200 - (agora - timestamp_gerado))
                    if tempo_restante > 0:
                        minutos_restantes = tempo_restante // 60
                        st.info(f"🔑 Senha atual: `{senha_atual}`\n\n⏳ Validade restante: {minutos_restantes} minutos")
                    else:
                        st.warning("⚠️ A senha atual expirou. Gere uma nova.")

                # Geração de senha (se expirado ou inexistente)
                if not dados_senha or agora - dados_senha.get("timestamp") > 7200:
                    if st.button("🔑 Gerar nova senha temporária"):
                        senha_temp = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
                        st.session_state.senhas_topico[topico_ativo] = {
                            "senha": senha_temp,
                            "timestamp": agora
                        }
                        salvar_json(SENHAS_TOPICO_PATH, st.session_state.senhas_topico)
                        st.success(f"Nova senha para '{topico_ativo}': `{senha_temp}` (válida por 2 horas)")

    with col1:
        if topico_ativo:
            st.subheader(f"Chat - Tópico: {topico_ativo}")
            mensagens = st.session_state.mensagens_por_topico.get(topico_ativo, [])
            if not mensagens:
                st.info("Nenhuma mensagem ainda neste tópico.")
            else:
                for msg in mensagens:
                    st.markdown(f"✅ {msg}")

            st.markdown("---")
            with st.form("form_msg", clear_on_submit=True):
                col_msg, col_btn = st.columns([5, 1])
                with col_msg:
                    mensagem = st.text_input("Digite sua mensagem:", key="nova_msg")
                with col_btn:
                    enviar = st.form_submit_button("Enviar")

                if enviar and mensagem.strip() and topico_ativo:
                    try:
                        cliente.enviar_pub(topico_ativo, mensagem.strip())
                    except Exception as e:
                        st.error(f"Erro ao enviar: {e}")
        else:
            st.warning("Para começar, entre em um tópico.")
