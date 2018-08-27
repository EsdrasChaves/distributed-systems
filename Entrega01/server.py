import socket
import queue
import threading
import time

PORT = 12345
HOST = socket.gethostbyname(socket.gethostname())



class Server:
    def __init__(self):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.bind((HOST, PORT))
        self.s.listen()
        self.event = threading.Event()


        self.input_queue = queue.Queue(maxsize=-1)
        self.process_queue = queue.Queue(maxsize=-1)
        self.log_queue = queue.Queue(maxsize=-1)
        self.hash = {}

    def reload_hash(self):
        try:
            with open('logfile', 'r') as file:
                for line in file:
                    line.replace('\n','')
                    self.process_command(reload=True, data=line)
        except:
            pass

    def receive_command(self, c, addr):
        while not self.event.is_set():
            data = c.recv(1024).decode()
            if not data: break
            self.input_queue.put((c, addr, data))
        c.close()

    def enqueue_command(self):
        while not self.event.is_set():
            if not self.input_queue.empty():
                c, addr, data = self.input_queue.get()
                self.process_queue.put((c, data))
                self.log_queue.put((addr, data))
                
    def process_command(self, reload=False, data=""):
        while not self.event.is_set():
            if not self.process_queue.empty() or reload == True:
                if reload == False:
                    c, data = self.process_queue.get()
                
                query = data.split()
                command = query[0]
                key = int(query[1])
                usr_data = " ".join(map(str, query[2:])) if len(query) > 2 else ""

                response_msg = ""

                if command == "CREATE":
                    if key not in list(self.hash.keys()):
                        self.hash[key] = usr_data
                        response_msg ="Successfully CREATED {} - {}".format(key, usr_data).encode()
                    else:
                        response_msg ="There is already an entry with the key {}".format(key).encode()
                
                elif command == "UPDATE":
                    if key in list(self.hash.keys()):
                        self.hash[key] = usr_data
                        response_msg = "Successfully UPDATED {} - new content: {}".format(key, usr_data).encode()
                    else:
                        response_msg = "There is no entry with the key {}".format(key).encode()
                
                elif command == "DELETE":
                    if key in list(self.hash.keys()):
                        self.hash.pop(key, None)
                        response_msg = "Successfully Removed entry {}".format(key).encode()
                    else:
                        response_msg = "There is no entry with the key {}".format(key).encode()

                elif command == "READ":
                    if key in list(self.hash.keys()):
                        response_msg = self.hash[key].encode()
                    else:
                        response_msg = "There is no entry with the key {}".format(key).encode()

                else:
                    response_msg = "Invalid command".encode()

                if reload == False:
                    c.send(response_msg)
                else:
                    break


    def log_command(self):
        logfile = open('logfile', 'a')
        while not self.event.is_set():
            if not self.log_queue.empty():
                _, data = self.log_queue.get()
                if data.split()[0] != "READ":
                    logfile.write(data + '\n')

        logfile.close()

    def program_loop(self):
        print("Servidor pronto para receber conexões!")
        while True:
            try:
                c, addr = self.s.accept()
                print("New connection: ", addr)
                t = threading.Thread(target=self.receive_command, args=(c, addr))
                t.setDaemon(True)
                t.start()
            except KeyboardInterrupt:
                self.event.set()
                print("Shutting down...")
                time.sleep(5)
                self.s.close()
                break



    def run(self):
        self.reload_hash()

        enqueue_thread = threading.Thread(target=self.enqueue_command)
        enqueue_thread.setDaemon(True)
        enqueue_thread.start()

        process_thread = threading.Thread(target=self.process_command)
        process_thread.setDaemon(True)
        process_thread.start()

        log_thread = threading.Thread(target=self.log_command)
        log_thread.setDaemon(True)
        log_thread.start()

        self.program_loop()


server = Server()
server.run()