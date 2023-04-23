
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes


def create_key_pairs():
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )

    public_key = private_key.public_key()

    # Serialize the private and public keys to PEM format
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )

    return public_pem, private_pem



def encrypt_using_public(msg_in_bytes, public_pem):
    public_key = serialization.load_pem_public_key(public_pem)
    cipher = public_key.encrypt(msg_in_bytes, padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA1()), algorithm=hashes.SHA256(), label=None))
    return cipher
def decrypt_using_private(cipher, private_pem):
    private_key = serialization.load_pem_private_key(private_pem, password=None)
    decrypted_message = private_key.decrypt(cipher, padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA1()), algorithm=hashes.SHA256(), label=None))
    return decrypted_message


public_pem, private_pem = create_key_pairs()