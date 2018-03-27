import requests
import json
import sys
import subprocess
import re


class TraceException(Exception):
    """Не удалось построить маршрут"""
    def __str__(self):
        return "Не удалось построить маршрут"


class IPInfo:
    def __init__(self, ip, aS, country, isp):
        self.ip = ip
        self.AS = aS
        self.country = country
        self.isp = isp

    def __str__(self):
        return "IP: {}    AS: {}   Country: {}    Provider: {}"\
            .format(self.ip, self.AS, self.country, self.isp)


COMPLETE = re.compile('Трассировка завершена')
IP = re.compile('(\d+[.]\d+[.]\d+[.]\d+)')


def trace_destination(destination):
    try:
        info = []
        path = get_path(destination)
        path.pop(0)
        print("Сбор информации об узлах маршрута...")
        for p in path:
            info.append(get_info_router_from_ip(p))
        print_result(info)
    except:
        print("Не удалось построить маршрут")
    finally:
        sys.exit()


def get_path(destination):
    """Вернет список IP адресов маршрута"""
    print("Построение маршрута...")
    data = subprocess.check_output(['tracert', '-d', '-w', '1000', '-4', destination]).decode('cp866')
    success = re.search(COMPLETE, data)
    if success.group(0):
        return re.findall(IP, data)
    else:
        raise TraceException()


def get_info_router_from_ip(ip):
    r = requests.get("http://ip-api.com/json/" + ip)
    answer = json.loads(r.content)
    if answer["status"] == "success":
        return IPInfo(ip, answer["as"], answer["country"], answer["isp"])
    return IPInfo(ip, "Private", "Private", "Private")


def print_result(data):
    count = 1
    for d in data:
        print(str(count) + '. ' + str(d) + '\n')
        count += 1


if __name__ == "__main__":
    destination = sys.argv[1]
    # destination = '8.8.8.8'
    trace_destination(destination)
