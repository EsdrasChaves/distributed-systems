import threading
import socket
import time

PORT = 12345
HOST = socket.gethostbyname(socket.gethostname())

class Client:

    def __init__(self):
        self.event = threading.Event()
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect((HOST, PORT))
    def send_command(self):
        while not self.event.isSet():
            command = input()

            if command == "sair": 
                self.event.set()
                break
            elif self.check_command(command):
                self.s.sendto(command.encode(), (HOST, PORT))
            else:
                print("Invalid command...")


    def receive_result(self):
        while not self.event.isSet():
            msg = self.s.recv(1024).decode()
            if not msg:
                self.event.set()
                break
            print(msg)

    def check_command(self, usr_input):
        query = usr_input.split()
        if len(query) <= 0:
            return False

        if query[0] == 'CREATE' or query[0] == 'UPDATE':
            if  len(query) >= 3 and query[1].isdigit():
                return True
        elif query[0] == 'DELETE' or query[0] == 'READ':
            if len(query) == 2 and query[1].isdigit():
                return True
        return False
    
    def print_menu(self):
        pass

    def run(self):
        output_thread = threading.Thread(target=self.receive_result)
        output_thread.setDaemon(True)
        output_thread.start()

        input_thread = threading.Thread(target=self.send_command)
        input_thread.setDaemon(True)
        input_thread.start()

        input_thread.join()
        if output_thread.isAlive():
            time.sleep(5)
        else:
            print("Server is down...")
        

client = Client()
client.run()