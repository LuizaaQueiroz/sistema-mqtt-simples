from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

# Caminho da chave privada existente
chave_privada_path = "certs/client_key.pem"

# Caminho onde a chave pública será salva
chave_publica_path = "certs/client_pub.pem"

# Carrega a chave privada
with open(chave_privada_path, "rb") as f:
    chave_privada = serialization.load_pem_private_key(
        f.read(),
        password=None,
        backend=default_backend()
    )

# Extrai a chave pública
chave_publica = chave_privada.public_key()

# Salva a chave pública no formato PEM
with open(chave_publica_path, "wb") as f:
    f.write(
        chave_publica.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
    )

print("✅ Chave pública salva em certs/client_pub.pem")
