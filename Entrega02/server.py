# -*- coding: utf-8 -*-

import socket
import queue
import threading
import time
import os
import sys
from dotenv import load_dotenv


class Server:
    def __init__(self):
        self.host = os.getenv("HOST")
        self.port = int(os.getenv("PORT"))
        self.buffer_size = int(os.getenv("BUFFER_SIZE"))
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.bind((self.host, self.port))
        self.s.listen()
        self.event = threading.Event()

        self.input_queue = queue.Queue(maxsize=-1) #número negativo no maxsize para infinito
        self.process_queue = queue.Queue(maxsize=-1)
        self.log_queue = queue.Queue(maxsize=-1)
        self.hash = {}
        self.nodeId = self.setNodeId()


    def setNodeId(self):
        nBits = int(os.getenv("NBITS"))
        nNodes = int(os.getenv("NNODES"))
        nodeId = (2**nBits - 1)
        responsibles = int(2**nBits/nNodes)
        
        try:
            routes = "./chord/roteamento"
            routesfile = open(routes, 'a')
            #fazer a tabela de rotas apenas uma vez
            if os.stat(routes).st_size == 0:
                writeArray = []
                for i in range(0,nNodes):
                    previousId = nodeId-responsibles+1
                    if previousId < 0 or (previousId - responsibles) < 0:
                        previousId = 0
                    writeRange = str( previousId ) + " " + str( nodeId ) + "\n"
                    writeArray.append(writeRange)
                    nodeId = previousId-1

                writeArray.reverse()
            for i in range(0,nNodes):
                routesfile.write(str(i+1) + " " + writeArray[i])
                    
            
            routesfile.close()

        except:
            pass


        nodeId = (2**nBits - 1)
        

        nodeIdsfile = "./chord/nodeIds"
        idsfile = open(nodeIdsfile, 'a')

        #se o arquivo tem informacao
        if os.stat(nodeIdsfile).st_size != 0:
            lastId = nodeId
            #precisa buscar o ultimo id inserido
            with open(nodeIdsfile, 'r') as file:
                for line in file: #lê o arquivo linha por linha
                    lastId = int(line)
            nodeId = int(lastId - responsibles)
        if(nodeId >= 0 ):
            idsfile.write(str(nodeId) + "\n")
            idsfile.close()
        else: 
            nodeId = -1
            print("Numero de servidores completo")
            self.event.set()
            sys.exit()            

        return nodeId

    def reload_hash(self):
        try:
            with open('logfile', 'r') as file:
                i = 0
                for line in file: #lê o arquivo linha por linha
                    print (i + "\n")
                    i += 1
                    line.replace('\n','')
                    self.process_command(reload=True, data=line)
        except:
            pass

    def receive_command(self, c, addr):
        print("New connection: ", addr)
        while not self.event.is_set():
            data = c.recv(self.buffer_size).decode()
            if not data: break
            self.input_queue.put((c, addr, data)) #c -> conexão, addr -> endereço, data -> data
        c.close()

    def enqueue_command(self):
        while not self.event.is_set():
            if not self.input_queue.empty():
                # analisar se esse servidor é responsável pela chave recebida
                c, addr, data = self.input_queue.get()
                self.process_queue.put((c, data))
                self.log_queue.put((addr, data))
                
    def process_command(self, reload=False, data=""): #tira de fila de processos e vai processar e responder pro cliente
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
                    try:
                        c.send(response_msg)
                    except:
                        pass
                else:
                    break

    def log_command(self):
        logfile = open('logfile', 'a')
        while not self.event.is_set():
            if not self.log_queue.empty():
                _, data = self.log_queue.get() #data é o que recebeu do usuário, basicamente o comando
                if data.split()[0] != "READ":
                    logfile.write(data + '\n')
                    logfile.flush()

        logfile.close()

    def program_loop(self):
        print("Servidor " + str(self.nodeId) + " pronto para receber conexões!")
        while True:
            try:
                c, addr = self.s.accept()
                t = threading.Thread(target=self.receive_command, args=(c, addr))
                t.setDaemon(True) #quando o programa encerrar a thread também encerra
                t.start()
            except KeyboardInterrupt:
                self.event.set()
                print("Shutting down...")
                time.sleep(5)
                self.s.close()
                break



    def run(self):
        self.reload_hash() #se tiver alguma coisa no arquivo de log ele reexecuta

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


def run_server():
    load_dotenv()
    server = Server()
    server.run()

if __name__ == '__main__':

    run_server()
