import threading
import socket
import time
import os
from dotenv import load_dotenv

import grpc
import services_pb2
import services_pb2_grpc

load_dotenv()


class Client:

    def __init__(self):  # tipo um construtor
        self.host_address = os.getenv("HOST") + ":" + os.getenv("PORT")
        self.event = threading.Event()  # sincroniza thread, objeto inicia como false
        self._lock = False

        self._channel = grpc.insecure_channel(self.host_address)
        self.stub = services_pb2_grpc.ServiceStub(self._channel)

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
                query = Client.check_command(command)
                if command == "sair":
                    self.event.set()  # seta o evento com true
                    break
                elif  query is not None:  # verifica se é um comando válido
                    if query[0] == 'CREATE':
                        usr_data = " ".join(map(str, query[2:])) if len(query) > 2 else ""
                        data = services_pb2.Data(id=int(query[1]), data=usr_data)
                        result = self.stub.create(data)
                        #print(result.message)
                        print(result.resposta)
                    elif query[0] == 'UPDATE':
                        usr_data = " ".join(map(str, query[2:])) if len(query) > 2 else ""
                        data = services_pb2.Data(id=int(query[1]), data=usr_data)
                        #result = self.stub.update.future(data)
                        result = self.stub.update(data)
                        #result.add_done_callback(self.receive_result)
                        print(result.resposta)
                    elif query[0] == 'READ':
                        data = services_pb2.Id(id=int(query[1]))
                        #result = self.stub.read.future(data)
                        result = self.stub.read(data)
                        #result.add_done_callback(self.receive_result)
                        print(result.resposta)
                    elif query[0] == 'DELETE':
                        data = services_pb2.Id(id=int(query[1]))
                        # result = self.stub.delete.future(data)
                        result = self.stub.delete(data)
                        # result.add_done_callback(self.receive_result)
                        print(result.resposta)
                    self.lock = True
                else:
                    print("Invalid command...")

    def receive_result(self, result):
        try:
            r = response.result()
            print(r.resposta)
                
            self.lock = False
        except Exception as e:
            pass

    @staticmethod
    def check_command(usr_input):
        query = usr_input.split()
        if len(query) <= 0:
            return None

        if query[0] == 'CREATE' or query[0] == 'UPDATE':
            if len(query) >= 3 and query[1].isdigit():
                return query
        elif query[0] == 'DELETE' or query[0] == 'READ':
            if len(query) == 2 and query[1].isdigit():
                return query
        return None

    @staticmethod
    def print_menu():
        print("To add a new entry type CREATE <number> <message>\n"
              "To read an entry type READ <number>\n"
              "To modify an entry type UPDATE <number> <message>\n"
              "To remove an entry type DELETE <number>\n"
              "To close type 'sair': \n")

    def run(self):

        # output_thread = threading.Thread(
        #     target=self.receive_result)  # o output_thread roda a fnç q recebe as msg do servidor
        # output_thread.setDaemon(True)
        # output_thread.start()

        input_thread = threading.Thread(
            target=self.send_command)  # o input_thread roda a fnç q envia as msg p/ o servidor
        input_thread.setDaemon(True)
        input_thread.start()

        input_thread.join()
        if input_thread.isAlive():  # quando a thread do input termina ele irá esperar 5 segundos
            time.sleep(5)
        else:
            print("Server is down...")


client = Client()
client.run()
