import argparse
import socket
import ssl
import quopri
# by Zaostrovskaya Anastasiya
import re
import io
import base64
import binascii


ENCODING = 'B'


def get_args():
    """Получение аргументов при запуск"""
    parser = argparse.ArgumentParser()
    parser.add_argument("--server", "-s", type=str, help="Сервер для получения почты")
    parser.add_argument("--login", "-l", type=str, help="Логин для авторизации")
    parser.add_argument("--password", "-p", type=str, help="Пароль для авторизации")
    parser.add_argument("--number", "-n", type=int, help="Номер письма для просмотра")
    return parser.parse_args()


def decode_header(line):
    """Декодирование частей заголовка"""
    if line:
        try:
            if line[0] != "=":
                return line
            elif ENCODING == 'B':
                return base64.b64decode(line[9:-2]).decode()
            elif ENCODING == 'Q':
                return quopri.decodestring(line[9:-2]).decode()
        except binascii.Error:
            return "Error decoding"


def parse_message(num, message, amount):
    """Разбор пришедшего сообщения"""

    def parse_from_to(reg1, reg2):
        """Разбор имени и адреса"""
        reg_to = re.compile(reg1)
        try:
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
        except:
            print("Error on parsing name or email")
            exit(0)
        return name, email

    def parse_subject():
        """Разбор темы сообщения"""
        s = re.compile(r"(Subject: |)(=\?UTF-8\?([BQ])\?(\S+)\?=)", re.IGNORECASE)
        find = s.findall(message)
        global ENCODING
        ENCODING = find[1][2]
        result = ""
        for part in find[1:]:
            result += part[3]
        if ENCODING == 'B':
            subject = base64.b64decode(result).decode()
        else:
            subject = quopri.decodestring(result).decode()
        return subject

    def parse_date():
        reg_date = re.compile(r"Date: [\w\s ,:]+")
        try:
            date = " ".join(reg_date.findall(message)[0].split()[2:])
        except IndexError:
            date = ""
        return date

    def parse_text(boundary):
        """Запись текста письма в файл"""
        re_name = re.compile(r'Content-Type: text\/plain;')
        if boundary:
            mes_parts = message.split(boundary)
            for part in mes_parts:
                name = re_name.findall(part)
                if name:
                    text = part.split('\n')[4]
        else:
            mes_parts = message.split('\r\n\r\n')
            text = mes_parts[1][:-5]
        with open('text_plain.txt', 'w') as f:
            if ENCODING == 'B':
                f.write(text)
            else:
                try:
                    f.write(quopri.decodestring(text).decode())
                except ValueError:
                    f.write(text)
        return

    def parse_boundary():
        """Поиск разделителя"""
        reg = re.compile(r'boundary="(.+)"')
        try:
            boundary = reg.findall(message)[1]
        except IndexError:
            boundary = ''
        return boundary

    def parse_file(boundary, files):
        """Запись файлов-вложений"""
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
                    if ENCODING == 'B':
                        name.write(base64.decodestring(res_file.encode()))
                    else:
                        name.write(quopri.encodestring(res_file.encode()))

    from_name, from_email = parse_from_to(r'From: [\S]*[\s]*<[\S]*>', r'From: [\S]*')
    to_name, to_email = parse_from_to(r'To: [\S]* <[\S]*>', r'To: [\S]*')
    date = parse_date()
    boundary = parse_boundary()
    subject = parse_subject()
    parse_text(boundary)
    from_name = decode_header(from_name)
    to_name = decode_header(to_name)
    from_email = decode_header(from_email)
    to_email = decode_header(to_email)
    reg_filename = re.compile(r"filename=[\S]+")
    files = dict()
    if boundary:
        files = {file[10:-1]: decode_header(file[10:]) for file in reg_filename.findall(message)}
    print("ПИСЬМО №{}".format(num))
    print("  От кого: {} {}".format(from_name, from_email))
    print("  Кому: {} {}".format(to_name, to_email))
    print("  Тема: {}".format(subject))
    if date:
        print("  Дата: {}".format(date))
    print("  Размер: {}".format(amount))
    if files:
        parse_file(boundary, files)
        print("  Вложений: {}".format(len(files)))
        print("  Имена вложений:")
        for f in files:
            print("   ", files[f])


def problems(sock, cmd, data=''):
    """Вывод ошибок"""
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
        """Создание соединения"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.ssl_sock = ssl.wrap_socket(sock)
            self.ssl_sock.settimeout(2)
            self.ssl_sock.connect((self.server, self.port))
            data = self.ssl_sock.recv(4096).decode()
            if data[:3] == "+OK":
                print("CONNECTION created")
            else:
                problems(self.ssl_sock, "CONNECTION", data)
        except socket.gaierror:
            problems(self.ssl_sock, "CONNECTION")
        except socket.timeout:
            problems(self.ssl_sock, "CONNECTION timeout")

    def auth(self):
        """Авторизация на почте"""
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
        """Проверка количества писем в ящике и возможности скачать заданное письмо"""
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

    def get_message(self):
        """Скачивание указанного сообщения"""
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
        """Закрытие сеанса"""
        try:
            self.ssl_sock.send("QUIT\r\n")
            print("QUIT")
            print(self.ssl_sock.recv(4096).decode())
        except:
            self.ssl_sock.close()
            exit(0)

    def get_mail(self):
        """Алгоритм получения письма"""
        self.connect()
        self.auth()
        self.stat()
        self.get_message()
        self.quit()


if __name__ == '__main__':
    args = get_args()
    server = args.server
    login = args.login
    password = args.password
    num = args.number
    mail = Mail(server, login, password, num)
    mail.get_mail()
