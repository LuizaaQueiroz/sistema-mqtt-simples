from .crypto_utils import (
    gerar_chave_aes,
    criptografar_aes,
    criptografar_ec,
    carregar_chave_publica_pem
)
import json
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa, ec
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding


from datetime import datetime

def enviar_pub(cliente, topico, mensagem_clara):
    if not cliente.conectado:
        print("[ERRO] Cliente não está conectado.")
        return

    try:
        chave_pub_path = f'certs/pub_keys/{topico}_pub.pem'
        chave_publica_dest = carregar_chave_publica_pem(chave_pub_path)
        print(f"[DEBUG] Tipo da chave pública: {type(chave_publica_dest)}")

        chave_aes = gerar_chave_aes()
        msg_cript = criptografar_aes(mensagem_clara, chave_aes)

        if isinstance(chave_publica_dest, rsa.RSAPublicKey):
            encrypted_aes_key = chave_publica_dest.encrypt(
                chave_aes,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            ephemeral_pub_bytes = None

        elif isinstance(chave_publica_dest, ec.EllipticCurvePublicKey):
            encrypted_aes_key, ephemeral_pub = criptografar_ec(chave_aes, chave_publica_dest)
            ephemeral_pub_bytes = ephemeral_pub.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            ).decode()

        else:
            raise ValueError("Tipo de chave pública não suportado")

        timestamp = datetime.utcnow().isoformat() + 'Z'  # UTC timestamp ISO 8601

        pacote = {
            "tipo": "publicar",
            "topico": topico,
            "id": cliente.nome_cliente,
            "destinatario": topico,
            "remetente": cliente.nome_cliente,
            "timestamp": timestamp,
            "mensagem": {
                "aes": encrypted_aes_key.hex(),
                "msg": msg_cript.hex(),
                "ephemeral_public_key": ephemeral_pub_bytes
            }
        }

        cliente.socket.send(json.dumps(pacote).encode())
        print(f"[DEBUG] Mensagem publicada para {topico}")

    except Exception as e:
        print(f"[ERRO] Falha ao publicar para {topico}: {e}")

def enviar_sub(cliente, topico):
    if cliente.conectado:
        try:
            pacote = json.dumps({
                "tipo": "inscrever",
                "topico": topico,
                "id": cliente.nome_cliente
            })
            cliente.socket.send(pacote.encode())
            print(f"[DEBUG] Inscrição enviada para o tópico {topico} por {cliente.nome_cliente}")
        except Exception as e:
            print(f"[ERRO] Falha ao inscrever no tópico {topico}: {e}")
