from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from datetime import datetime, timedelta

# 1. Gerar chave privada
chave = rsa.generate_private_key(public_exponent=65537, key_size=2048)

# Salvar chave privada em PEM
with open("certs/client_key.pem", "wb") as f:
    f.write(
        chave.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )

# 2. Criar informações de identidade
nome = x509.Name([
    x509.NameAttribute(NameOID.COUNTRY_NAME, u"BR"),
    x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, u"SC"),
    x509.NameAttribute(NameOID.LOCALITY_NAME, u"Lages"),
    x509.NameAttribute(NameOID.ORGANIZATION_NAME, u"IFSC"),
    x509.NameAttribute(NameOID.COMMON_NAME, u"Luiza Queiroz"),  # CN
])

# 3. Criar CSR
csr = (
    x509.CertificateSigningRequestBuilder()
    .subject_name(nome)
    .sign(chave, hashes.SHA256())
)

# 4. Salvar CSR em disco
with open("certs/broker.csr", "wb") as f:
    f.write(csr.public_bytes(serialization.Encoding.PEM))

print("✅ CSR e chave privada gerados em: certs/")
