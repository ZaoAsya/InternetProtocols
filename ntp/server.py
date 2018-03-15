import time

from concurrent.futures import ThreadPoolExecutor
from socket import (socket, AF_INET, SOCK_DGRAM)
from struct import pack, unpack, Struct


UNIX_SHIFT = 2208988800  # 70 yaers in seconds time.time starts 1970
LOCALHOST = '127.0.0.1'


class Server:
    def __init__(self):
        self.shift = 300
        self.port = 123
        self.sock = socket(AF_INET, SOCK_DGRAM)  # IP, UDP

    def run(self):
        print('Listening on {}'.format(self.port))
        pool = ThreadPoolExecutor(128)
        self.sock.bind((LOCALHOST, self.port))

        while True:
            data, addr = self.sock.recvfrom(1024)
            pool.submit(self.handle, data, addr)

    def handle(self, data, addr):
        start_time = unpack('!BBBBII4sQQQQ', data)[10]
        recv_time = self.get_time()  # время прибытия
        packet = self.build_ntp(start_time, recv_time)
        self.sock.sendto(packet, addr)
        print('Sent a packet to {}.'.format(addr))

    def get_time(self):
        return int((time.time() + UNIX_SHIFT + self.shift) * (2 ** 32))  # перевод в первые значащие 32 бита int 

    def build_ntp(self, start_time, recv_time):
        packet = Struct('!BBBBII4sQQQQ').pack(
            0b00100100,
            3, 0, 0, 0, 0,
            b'0000',
            self.get_time(),  # время обновления
            start_time,  # начальное время
            recv_time,  # время приема
            self.get_time())  # время отправки
        return packet


def main():
    server = Server()
    server.run()


if __name__ == '__main__':
    main()