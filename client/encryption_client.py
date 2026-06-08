__author__ = 'Peleg Etzioni'

import socket
import time
from encryption.encryption_manager import DHManager, AESManager
from const import *


HANDSHAKE_TIMEOUT = 15  # שניות עד שמוותרים
HANDSHAKE_RETRY = 0.5  # שניות בין ניסיונות חוזרים


class ClientHandshake:

    def __init__(self, sock, dst):
        self.sock = sock
        self.dst = dst

    def run(self):
        dh = None
        server_pub_pem = None

        deadline = time.time() + HANDSHAKE_TIMEOUT
        self.sock.settimeout(HANDSHAKE_RETRY)

        while time.time() < deadline and dh is None:
            self.sock.sendto(ENC_HELLO, self.dst)
            if DEBUG:
                print("Handshake --> sent ENC_HELLO")

            try:
                data, _ = self.sock.recvfrom(8192)
            except socket.timeout:
                if DEBUG:
                    print("Handshake --> timeout waiting for ENC_PARAMS, retrying")
                continue
            except Exception as e:
                return

            if not data.startswith(ENC_PARAMS):
                continue

            try:
                # ENC_PARAMS|<params_pem>|<server_pub_pem>
                _, params_pem, server_pub_pem = data.split(b"|", 2)
                parameters = DHManager.bytes_to_parameters(params_pem)

                dh = DHManager(save_path='client_', parameters=parameters)
                if DEBUG:
                    print("Handshake --> DH parameters initialized successfully")

            except Exception as e:
                print(f"Handshake --> bad ENC_PARAMS: {e}")
                dh = None
                continue

        if dh is None:
            if DEBUG:
                print("Handshake --> failed to initialize DH parameters")
            self.sock.settimeout(None)
            return None

        client_pub_pem = dh.get_public_key_bytes()
        msg = ENC_PUBKEY + b"|" + client_pub_pem

        _deadline = time.time() + HANDSHAKE_TIMEOUT
        self.sock.settimeout(HANDSHAKE_RETRY)

        while time.time() < _deadline:
            self.sock.sendto(msg, self.dst)
            if DEBUG:
                print("Handshake --> sent/resent ENC_PUBKEY")

            try:
                data, _ = self.sock.recvfrom(8192)
            except socket.timeout:
                if DEBUG:
                    print("Handshake --> timeout waiting for ENC_DONE, retrying…")
                continue

            if data == ENC_DONE:
                try:
                    aes_key = dh.generate_shared_key(server_pub_pem)
                    aes = AESManager(aes_key)
                    if DEBUG:
                        print("Handshake --> encryption established")
                    self.sock.settimeout(None)
                    return aes

                except Exception as e:
                    print(f"Handshake --> error establishing AES key: {e}")
                    self.sock.settimeout(None)
                    return None

        if DEBUG:
            print("Handshake --> handshake failed: timeout")
        self.sock.settimeout(None)
        return None