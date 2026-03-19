import socket
import threading

HOST = "127.0.0.1"
PORT = 5000

running = True


def receive_messages(sock):
    global running

    while running:
        try:
            data = sock.recv(1024)

            if not data:
                print("\n[СЕРВЕР ОТКЛЮЧЕН]")
                break

            message = data.decode("utf-8").strip()

            print("\n" + message)

        except:
            print("\n[ПОТЕРЯНО СОЕДИНЕНИЕ]")
            break

    running = False


def main():
    global running

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        client_socket.connect((HOST, PORT))
    except Exception as e:
        print(f"Ошибка подключения: {e}")
        return

    nickname = input("Введите ник: ").strip()
    client_socket.send(nickname.encode("utf-8"))

    response = client_socket.recv(1024).decode("utf-8").strip()

    if response.startswith("ERROR"):
        print(response)
        return

    print(response.replace("OK ", ""))
    print("Введите сообщение (/exit для выхода)\n")

    thread = threading.Thread(
        target=receive_messages,
        args=(client_socket,),
        daemon=True
    )
    thread.start()

    while running:
        try:
            print("Ваше сообщение: ", end="", flush=True)
            message = input().strip()

            if not message:
                continue

            client_socket.send(message.encode("utf-8"))

            if message == "/exit":
                break

        except:
            print("[ОШИБКА ОТПРАВКИ]")
            break

    running = False
    client_socket.close()


if __name__ == "__main__":
    main()