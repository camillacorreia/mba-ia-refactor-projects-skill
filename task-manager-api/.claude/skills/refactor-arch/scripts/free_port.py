"""Imprime uma porta TCP livre em 127.0.0.1. Uso: python free_port.py [porta_preferida]"""
import socket
import sys


def is_free(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("127.0.0.1", port))
            return True
        except OSError:
            return False


preferred = int(sys.argv[1]) if len(sys.argv) > 1 else 0
if preferred and is_free(preferred):
    print(preferred)
else:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        print(s.getsockname()[1])
