import socket
import threading
import signal
import sys

HOST = "127.0.0.1"
PORT = 5000

clients = {}
clients_lock = threading.Lock()
server_socket = None
running = True


def broadcast(message, sender_socket=None):
    with clients_lock:
        for client_socket in list(clients.keys()):
            if client_socket != sender_socket:
                try:
                    client_socket.send((message + "\n").encode("utf-8"))
                except:
                    remove_client(client_socket)


def remove_client(client_socket):
    nickname = None

    with clients_lock:
        if client_socket in clients:
            nickname = clients[client_socket]
            del clients[client_socket]

    try:
        client_socket.close()
    except:
        pass

    if nickname:
        print(f"[DISCONNECT] {nickname} отключился")
        broadcast(f"INFO {nickname} вышел из чата")


def handle_client(client_socket, client_address):
    try:
        nickname = client_socket.recv(1024).decode("utf-8").strip()

        if not nickname:
            client_socket.send("ERROR Ник пустой\n".encode("utf-8"))
            return

        with clients_lock:
            if nickname in clients.values():
                client_socket.send("ERROR Ник занят\n".encode("utf-8"))
                return

            clients[client_socket] = nickname

        print(f"[CONNECT] {nickname} подключился ({client_address})")

        client_socket.send(f"OK Добро пожаловать, {nickname}\n".encode("utf-8"))
        broadcast(f"INFO {nickname} зашел в чат", client_socket)

        while True:
            data = client_socket.recv(1024)

            if not data:
                break

            message = data.decode("utf-8").strip()

            if message == "/exit":
                client_socket.send("INFO Вы вышли из чата\n".encode("utf-8"))
                break

            broadcast(f"MSG {nickname}: {message}", client_socket)

    except:
        print(f"[ERROR] Клиент {client_address} отвалился")

    finally:
        remove_client(client_socket)


def shutdown_server(signal_received, frame):
    global running

    print("\n[SERVER] Получен Ctrl+C")
    print("[SERVER] Завершаем работу...")

    running = False

    with clients_lock:
        for client_socket, nickname in list(clients.items()):
            try:
                print(f"[SERVER] Отключаем: {nickname}")
                client_socket.send("INFO Сервер завершает работу\n".encode("utf-8"))
                client_socket.close()
            except:
                pass

        clients.clear()

    try:
        server_socket.close()
    except:
        pass

    print("[SERVER] Сервер остановлен")
    sys.exit(0)


def main():
    global server_socket

    signal.signal(signal.SIGINT, shutdown_server)

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    server_socket.bind((HOST, PORT))
    server_socket.listen()

    server_socket.settimeout(1)

    print(f"[SERVER] Запущен на {HOST}:{PORT}")
    print("[SERVER] Нажмите Ctrl+C для остановки\n")

    while running:
        try:
            client_socket, client_address = server_socket.accept()

            thread = threading.Thread(
                target=handle_client,
                args=(client_socket, client_address),
                daemon=True
            )
            thread.start()

        except socket.timeout:
            continue

        except Exception as e:
            print("Ошибка accept:", e)
            break


if __name__ == "__main__":
    main()