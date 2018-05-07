import sys
import socket
# by Zaostrovskaya Anastasiya
import argparse
import threading


open_port = []
lock = threading.Lock()


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", "-s", type=str, help="начало диапазона сканирования")
    parser.add_argument("--finish", "-f", type=str, help="конец диапазона сканирования")
    return parser.parse_args()


def scanTCP(start, finish):
    for port in range(start, finish+1):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2)
        try:
            s.connect(('cs.usu.edu.ru', port))
        except socket.timeout or socket.error:
            s.close()
        except KeyboardInterrupt:
            sys.exit(0)
        else:
            global lock
            lock.acquire()
            print(str(port) + ' active TCP port')
            open_port.append(port)
            s.close()
            lock.release()


if __name__ == "__main__":
    args = get_args()
    try:
        s = int(args.start)
        f = int(args.finish)
        d = (f - s) // 4
    except ValueError:
        print("Start and Finish of range to scan should be digits")
        sys.exit(0)
    try:
        threads = []
        p = s-1
        for x in range(4):
            threads.append(threading.Thread(target=scanTCP, args=(p + 1, p + d)))
            p += d
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        print(open_port)
    except Exception as e:
        print(e)
        sys.exit(0)
