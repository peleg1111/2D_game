import os
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import dh
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from  const import ENCRIPTION_PATH

class DHManager:

    def __init__(self, save_path='client_', parameters=None, save_key = True):

        os.makedirs(ENCRIPTION_PATH, exist_ok=True)

        self.private_path = os.path.join(
            ENCRIPTION_PATH,
            save_path + 'private.pem'
        )

        self.public_path = os.path.join(
            ENCRIPTION_PATH,
            save_path + 'public.pem'
        )

        if os.path.exists(self.private_path):

            self.private_key = self.load_private_key()
            self.public_key = self.private_key.public_key()

            self.parameters = parameters

            if self.parameters is None:

                self.parameters = (self.private_key.private_numbers().public_numbers.
                                    parameter_numbers.parameters())

        else:

            if parameters is None:

                self.parameters = dh.generate_parameters(
                    generator=2,
                    key_size=2048
                )

            else:
                self.parameters = parameters

            self.private_key = self.parameters.generate_private_key()
            self.public_key = self.private_key.public_key()

            if save_key:
                self.save_private_key()
                self.save_public_key()


    def save_private_key(self):

        with open(self.private_path, "wb") as f:
            f.write(
                self.private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption()
                )
            )

    def save_public_key(self):

        with open(self.public_path, "wb") as f:
            f.write(
                self.public_key.public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo
                )
            )


    def load_private_key(self):

        with open(self.private_path, "rb") as f:
            return serialization.load_pem_private_key(
                f.read(),
                password=None
            )


    def get_public_key_bytes(self):

        return self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )


    def get_parameters_bytes(self):

        return self.parameters.parameter_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.ParameterFormat.PKCS3
        )


    @staticmethod
    def bytes_to_public_key(data):

        return serialization.load_pem_public_key(data)

    @staticmethod
    def bytes_to_parameters(data):

        return serialization.load_pem_parameters(data)


    def generate_shared_key(self, public_key_bytes):

        peer_public_key = serialization.load_pem_public_key(
            public_key_bytes
        )

        shared_secret = self.private_key.exchange(
            peer_public_key
        )

        aes_key = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
        ).derive(shared_secret)

        return aes_key


class AESManager:

    def __init__(self, key):

        self.key = key
        self.aes = AESGCM(key)

    def encrypt(self, msg):

        if isinstance(msg, str):
            msg = msg.encode()

        nonce = os.urandom(12)

        ciphertext = self.aes.encrypt(
            nonce,
            msg,
            None
        )

        return nonce + ciphertext

    def decrypt(self, msg):

        nonce = msg[:12]
        ciphertext = msg[12:]

        return self.aes.decrypt(
            nonce,
            ciphertext,
            None
        )