__author__ = 'Peleg Etzioni'

import threading
import time
import socket
import random
from encryption.encryption_manager import DHManager, AESManager
from const import *


HANDSHAKE_TIMEOUT = 15  # [sec]
RESEND_TIME = 0.5  # [sec]


class Client_handshake:

    def __init__(self, addr, dh, params_msg):
        self.addr = addr
        self.dh = dh
        self.params_msg = params_msg
        self.deadline = time.time() + HANDSHAKE_TIMEOUT
        self.done = False
        self.last_sent = 0.0


class Server_encryption:

    def __init__(self, sock, aes_dict, lock):
        self.sock = sock
        self.aes_dict = aes_dict
        self.lock = lock
        self.clients = {}  # addr --> Client_handshake

        self.server_dh = DHManager(save_path='server_')

        # ניקוי handshakes שפג תוקפם
        threading.Thread(target=self.clean_loop, daemon=True).start()

    def handle(self, data, addr):
        if data == ENC_HELLO:
            self.on_start(addr)
            return True

        if data.startswith(ENC_PUBKEY):
            self.on_public_key(data, addr)
            return True

        return False

    def on_start(self, addr):
        with self.lock:
            if addr in self.clients and not self.clients[addr].done:
                hand_shake = self.clients[addr]

                if time.time() - hand_shake.last_sent > RESEND_TIME:
                    self.send(hand_shake.params_msg,addr)
                    hand_shake.last_sent = time.time()
                    if DEBUG:
                        print(f"Handshake --> resent ENC_PARAMS to {addr}")
                return

            dh = DHManager(
                save_path=f'server_{addr[0]}_{addr[1]}_',
                parameters=self.server_dh.parameters,
                save_key= False
            )

            params_pem = dh.get_parameters_bytes()
            pub_pem = dh.get_public_key_bytes()
            params_msg = ENC_PARAMS + b"|" + params_pem + b"|" + pub_pem

            hand_shake = Client_handshake(addr, dh, params_msg)
            self.clients[addr] = hand_shake

        self.send(params_msg,addr)
        hand_shake.last_sent = time.time()
        if DEBUG:
            print(f"Handshake --> sent ENC_PARAMS to {addr}")

    def on_public_key(self, data, addr):
        aes = None
        hand_shake = None

        with self.lock:
            hand_shake = self.clients.get(addr, None)
            if hand_shake is None or hand_shake.done:
                return

            try:
                _, client_pub_pem = data.split(b"|", 1)
                aes_key = hand_shake.dh.generate_shared_key(client_pub_pem)
                aes = AESManager(aes_key)

                self.aes_dict[addr] = aes
                hand_shake.done = True
            except Exception as e:
                print(f"Handshake --> bad ENC_PUBKEY from {addr}: {e}")
                return

        if aes and hand_shake and hand_shake.done:
            self.send(ENC_DONE,addr)
            if DEBUG:
                print(f" Handshake --> encryption with {addr} established successfully")

    def clean_loop(self):
        while True:
            time.sleep(5)
            now = time.time()
            with self.lock:
                expired = [a for a, hs in self.clients.items()
                           if hs.done or now > hs.deadline]
                for a in expired:
                    del self.clients[a]


    def send(self,msg , addr,DROP_RATE = 0.1, CHANGE_RATE = 0.14):
        msg = msg.encode() if isinstance(msg, str) else msg

        num = random.random()
        if num < DROP_RATE:  # מדמה איבוד של הודעות ברשת
            print(f"msg lost --> {msg}")
            return

        if num < CHANGE_RATE:  # מדמה שינוי של הודעות ברשת
            arr = list(msg.decode())
            random.shuffle(arr)
            msg = "".join(arr).encode()
            print(f"\n\nmsg changed --> {msg}\n\n")

        print(f"sent --> {addr} --> {msg}")
        self.sock.sendto(msg,addr)