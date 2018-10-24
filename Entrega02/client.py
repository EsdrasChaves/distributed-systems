import threading
import socket
import time
import os
from dotenv import load_dotenv

load_dotenv()


class Client:

    def __init__(self):  # tipo um construtor
        self.host = os.getenv("HOST")
        self.port = int(os.getenv("PORT"))
        self.buffer_size = int(os.getenv("BUFFER_SIZE"))
        self.event = threading.Event()  # sincroniza thread, objeto inicia como false
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # cria socket STREAM -> TCP, DGRAM -> UDP
        self.s.connect((self.host, self.port))  # conecta
        self._lock = False

    @property
    def lock(self):
        return self._lock

    @lock.setter
    def lock(self, value):
        self._lock = value

    def send_command(self):
        while not self.event.isSet():  # evento estiver setado
            if not self.lock:
                Client.print_menu()
                command = input()

                if command == "sair":
                    self.event.set()  # seta o evento com true
                    break
                elif Client.check_command(command):  # verifica se é um comando válido
                    self.s.send(command.encode())  # envia o comando para o servidor através do socket
                    self.lock = True
                else:
                    print("Invalid command...")

    def receive_result(self):
        while not self.event.isSet():
            msg = self.s.recv(self.buffer_size).decode()  # 1024 é a quantidade de bytes que vai ser lido
            if not msg:  # se o servidor cair ele retorna uma msg vazia
                self.event.set()  # seta o evento para true e o while pára
                break
            print(msg)
            print('\n')
            self.lock = False

    @staticmethod
    def check_command(usr_input):
        query = usr_input.split()
        if len(query) <= 0:
            return False

        if query[0] == 'CREATE' or query[0] == 'UPDATE':
            if len(query) >= 3 and query[1].isdigit():
                return True
        elif query[0] == 'DELETE' or query[0] == 'READ':
            if len(query) == 2 and query[1].isdigit():
                return True
        return False

    @staticmethod
    def print_menu():
        print("To add a new entry type CREATE <number> <message>\n"
              "To read an entry type READ <number>\n"
              "To modify an entry type UPDATE <number> <message>\n"
              "To remove an entry type DELETE <number>\n"
              "To close type 'sair': \n")

    def run(self):
        output_thread = threading.Thread(
            target=self.receive_result)  # o output_thread roda a fnç q recebe as msg do servidor
        output_thread.setDaemon(True)
        output_thread.start()

        input_thread = threading.Thread(
            target=self.send_command)  # o input_thread roda a fnç q envia as msg p/ o servidor
        input_thread.setDaemon(True)
        input_thread.start()

        input_thread.join()
        if output_thread.isAlive():  # quando a thread do input termina ele irá esperar 5 segundos
            time.sleep(5)
        else:
            print("Server is down...")


client = Client()
client.run()
