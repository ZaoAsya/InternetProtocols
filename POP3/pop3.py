import argparse
import socket
import ssl
# by Zaostrovskaya Anastasiya
import re
import io
import base64
import binascii


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("server", type=str, help="Сервер для получения почты")
    parser.add_argument("login", type=str, help="Логин для авторизации")
    parser.add_argument("password", type=str, help="Пароль для авторизации")
    parser.add_argument("number", type=int, help="Номер письма для просмотра")
    return parser.parse_args()


def decode_header(line):
    if line:
        try:
            if line[0] != "=":
                return line
            else:
                return base64.b64decode(line[9:-2]).decode()
        except binascii.Error:
            return "Error decoding"


def parse_message(num, message, amount):

    def parse_from_to(reg1, reg2):
        reg_to = re.compile(reg1)
        try:
            lst_to = reg_to.findall(message)[0].split()[1:]
        except IndexError:
            reg_to = re.compile(reg2)
            lst_to = reg_to.findall(message)[0].split()[1:]
        try:
            name, email = lst_to
        except ValueError:
            name = ""
            email = lst_to[0]
        return name, email

    def parse_subject():
        s = re.compile(r"(Subject: |\t)=\?utf-8\?B\?(.*?)\?=", re.IGNORECASE)
        find = s.findall(message)
        result = ""
        for part in find:
            result += part[1]
        subject = base64.b64decode(result).decode()
        return subject

    def parse_date():
        reg_date = re.compile(r"Date: [\w\s ,:]+")
        try:
            date = " ".join(reg_date.findall(message)[0].split()[2:])
        except IndexError:
            date = ""
        return date

    def parse_text(boundary):
        re_name = re.compile(r'Content-Type: text\/plain;')
        mes_parts = message.split(boundary)
        for part in mes_parts:
            name = re_name.findall(part)
            if name:
                text = part.split('\n')[4]
                with open('text_plain.txt', 'w') as f:
                    f.write(base64.b64decode(text).decode())
                return

    def parse_boundary():
        reg = re.compile(r'boundary="(.+)"')
        boundary = reg.findall(message)[1]
        return boundary

    def parse_file(boundary, files):
        re_name = re.compile(r'attachment; filename="(.*)"')
        mes_parts = message.split(boundary)
        for part in mes_parts:
            name = re_name.findall(part)
            if name:
                file = part.split('\r\n')[7:-3]
                res_file = ''
                for f in file:
                    res_file += f
                with io.open(files[name[0]], "wb") as name:
                    name.write(base64.decodestring(res_file.encode()))

    from_name, from_email = parse_from_to(r'From: [\S]*[\s]*<[\S]*>', r'From: [\S]*')
    to_name, to_email = parse_from_to(r'To: [\S]* <[\S]*>', r'To: [\S]*')
    date = parse_date()
    boundary = parse_boundary()
    parse_text(boundary)
    from_name = decode_header(from_name)
    to_name = decode_header(to_name)
    from_email = decode_header(from_email)
    to_email = decode_header(to_email)
    subject = decode_header(parse_subject())
    reg_filename = re.compile(r"filename=[\S]+")
    files = {file[10:-1]: decode_header(file[10:]) for file in reg_filename.findall(message)}
    print("ПИСЬМО №{}".format(num))
    print("  От кого:", from_name, from_email)
    print("  Кому: ", to_name, to_email)
    print("  Тема:", subject)
    if date:
        print("  Дата:", date)
    print("  Размер:", amount)
    if files:
        parse_file(boundary, files)
        print("  Вложений:", len(files))
        print("  Имена вложений:")
        for f in files:
            print("   ", files[f])


def problems(sock, cmd, data=''):
    print(cmd + " problems")
    print(data)
    sock.close()
    exit(0)


class Mail:
    def __init__(self, server, login, password, number):
        self.server = server
        self.port = 995
        self.login = login
        self.password = password
        self.number = number

    def connect(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ssl_sock = ssl.wrap_socket(sock)
        self.ssl_sock.settimeout(2)
        try:
            self.ssl_sock.connect((self.server, self.port))
            data = self.ssl_sock.recv(4096).decode()
            if data[:3] == "+OK":
                print("CONNECTION created")
            else:
                problems(self.ssl_sock, "CONNECTION", data)
        except socket.timeout:
            problems(self.ssl_sock, "CONNECTION timeout")

    def auth(self):
        login = "USER " + self.login + "\r\n"
        password = "PASS " + self.password + "\r\n"
        try:
            self.ssl_sock.send(login.encode())
            data = self.ssl_sock.recv(4096).decode()
            if data[:3] == "+OK":
                print("USER accepted")
            else:
                problems(self.ssl_sock, "USER", data)
            self.ssl_sock.send(password.encode())
            data = self.ssl_sock.recv(4096).decode()
            if data[:3] == "+OK":
                print("PASS accepted")
            else:
                problems(self.ssl_sock, "PASS", data)
        except socket.timeout:
            problems(self.ssl_sock, "AUTH timeout")

    def stat(self):
        try:
            self.ssl_sock.send("STAT\r\n".encode())
            data = self.ssl_sock.recv(4096).decode()
            if data[:3] == "+OK":
                if self.number > int(data.split()[1]):
                    problems(self.ssl_sock, "STAT", "-ERR Letter №{} doesn't exist".format(self.number))
                else:
                    print("STAT ok")
            else:
                problems(self.ssl_sock, "STAT", data)
        except socket.timeout:
            problems(self.ssl_sock, "STAT timeout")

    def get_messages(self):
        try:
            self.ssl_sock.send("RETR {}\r\n".format(self.number).encode())
            data = self.ssl_sock.recv(1024).decode(errors="ignore")
            amount = int(data.split()[1])
            message = ""
            while data:
                try:
                    if data.split()[0] != '+OK':
                        message += data
                    data = self.ssl_sock.recv(4096).decode(errors="ignore")
                except socket.timeout:
                    break
            parse_message(self.number, message, amount)
        except socket.timeout:
            problems(self.ssl_sock, "GET MESSAGE")

    def quit(self):
        try:
            self.ssl_sock.send("QUIT\r\n")
            print("QUIT")
            print(self.ssl_sock.recv(4096).decode())
        except:
            self.ssl_sock.close()
            exit(0)

    def get_mail(self):
        self.connect()
        self.auth()
        self.stat()
        self.get_messages()
        self.quit()


if __name__ == '__main__':
    args = get_args()
    server = args.server
    login = args.login
    password = args.password
    num = args.number
    mail = Mail(server, login, password, num)
    mail.get_mail()
