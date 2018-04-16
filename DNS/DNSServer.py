import pickle
import socket
import time
# by Zaostrovskaya Anastasiya
import os
import sys
from DNSPacket import *


CACHE = dict()


def save_cache():
    global CACHE
    output = open('cache_data.pkl', 'wb')
    pickle.dump(CACHE, output, 2)
    output.close()


def build_cache():
    global CACHE
    file = 'cache_data.pkl'
    if os.access(file, os.F_OK):
        print("Start with NOT empty Cache")
        input = open(file, 'rb')
        CACHE = pickle.load(input)
        input.close()
    else:
        print("Start with empty Cache")
        CACHE = dict()


def add_records_to_cache(packet: DNSPacket):

    def get_answers(answers):
        if answers is not None:
            for ans in answers:
                if ans.atype in {1, 2}:
                    add_record(ans)

    def add_record(r):
        key = (r.aname, r.atype)
        if key in CACHE:
            CACHE[key].add(CacheUnit(r, time.time(), r.ttl))
        else:
            CACHE[key] = {CacheUnit(r, time.time(), r.ttl)}

    get_answers(packet.answer)
    get_answers(packet.additional)
    get_answers(packet.authority)


def get_from_cache(key, packet: DNSPacket):
    data = [(p.rr.rdata, p.rr.rdlength) for p in CACHE[key] if time.time() - p.time <= p.packet_ttl]
    rdata = [d[0] for d in data]
    rdl = data[0][1]
    for data in rdata:
        packet.answer.append(Answer(key[0], key[1], 1, 300, rdl, data))
    packet.header.set_ancount(len(rdata))
    return packet


class CacheUnit:
    def __init__(self, answer: Answer, time, ttl):
        self.rr = answer  # answer object
        self.time = time
        self.packet_ttl = ttl

    def __str__(self):
        return "data: " + str(self.rr) + "\ntime adding: " \
               + str(self.time) + "\nttl: " + str(self.packet_ttl)

    def __hash__(self):
        return hash(self.rr.atype)

    def __eq__(self, other):
        if type(other) != type(self):
            return False
        return self.rr == other.rr


class DNSServer():
    def __init__(self, data: DNSPacket, addr, server, sock):
        self.client = addr
        self.port = 53
        self.data = data
        self.server = server
        self.client_sock = sock
        self.request = None

    def ask_server(self):
        sock_ask_server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock_ask_server.settimeout(1)
        try:
            sock_ask_server.sendto(self.request.to_bytes(), (self.server, self.port))
            response = sock_ask_server.recv(1024)
            response_packet = read_dns_packet(response)
            print("\nResponse from SERVER\nFor: " + str(response_packet.answer[0].aname))
            self.client_sock.sendto(response_packet.to_bytes(), self.client)
            add_records_to_cache(response_packet)
        except socket.error:
            print("Wait... smth wrong")

    def ask_cache(self, key, id):
        reply = get_from_cache(key, self.request)
        if reply:
            print("\nResponse from CACHE\nFor: " + str(key[0]))
            reply.header.set_id(id)
            add_records_to_cache(reply)
            self.client_sock.sendto(reply.to_bytes(), self.client)
        else:
            CACHE.__delitem__(key)
            self.ask_server()

    def start(self):
        self.request = read_dns_packet(self.data)
        key = (self.request.question[0].qname, self.request.question[0].qtype)  # имя домена и тип запроса
        if key in CACHE:
            self.ask_cache(key, self.request.header.id)
        elif key[1] in {1, 2}:
            self.ask_server()


def main(arg_server):
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        client_socket.settimeout(1/60)
        server = arg_server
        if arg_server == "127.0.0.1":
            server = "8.8.8.8"
        client_socket.bind(('127.0.0.2', 53))
        print("Start dns-server listening {0} port with {1} server".format(53, server))
        build_cache()
        print("Waiting for request...")
    except OSError as ex:
        print(ex)
        sys.exit()
    try:
        while True:
            try:
                data, addr = client_socket.recvfrom(1024)
            except socket.timeout:
                continue
            DNSServer(data, addr, server, client_socket).start()
    except KeyboardInterrupt:
        client_socket.close()
        save_cache()
        print("\nDNS server was stopped\nCache was saved")
        sys.exit(0)
    except Exception as ex:
        client_socket.close()
        print(ex)
        sys.exit(0)


if __name__ == "__main__":
    try:
        main(sys.argv[1])
    except IndexError:
        print("Enter the main server")
        sys.exit(0)
