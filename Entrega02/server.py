# -*- coding: utf-8 -*-

import socket
import queue
import threading
import time
import os
import sys
from dotenv import load_dotenv
import configparser
import math


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
        self.config = configparser.ConfigParser()
        self.config.read('.config')
        self.countLog = int(self.config["DEFAULT"]["LAST_SNAP"])
        self.timer = None
        self.timeOfSnaps = 10


    def findFtSuc(self,n,idsArray):
        nNodes = int(os.getenv("NNODES"))
        lastId = idsArray[len(idsArray)-1]
        for i in range(0,nNodes):
            if n > lastId:
                n = n - lastId+1 # esse +1 é porque reseta no 0
            if n <= idsArray[i]:
                return idsArray[i]
    
    def setNodeId(self):
        idsBreakedfile = "./chord/nodeIdsBreaked"
        breakedfile = open(idsBreakedfile, 'a')
        
        # #se o arquivo tem informacao
        if os.stat(idsBreakedfile).st_size != 0: 
            with open(idsBreakedfile, 'r') as file:
                first = True
                tail = []
                for line in file:
                    if not first:
                        tail.append(line)
                    else:
                        nodeId = [int(num) for num in line.split()]
                        nodeId = nodeId[0]
                        first =False

            with open(idsBreakedfile, 'w') as file2:
                file2.writelines(tail)                    
            breakedfile.close()
        else:
            nBits = int(os.getenv("NBITS"))
            nNodes = int(os.getenv("NNODES"))
            currentId = (2**nBits - 1)
            responsibles = int(2**nBits/nNodes)
            
            nodeIdsfile = "./chord/nodeIds"
            idsfile = open(nodeIdsfile, 'a')

            #se o arquivo tem informacao
            if os.stat(nodeIdsfile).st_size != 0:
                lastId = currentId
                #precisa buscar o ultimo id inserido
                nAlloc = 0
                with open(nodeIdsfile, 'r') as file:
                    for line in file: #lê o arquivo linha por linha
                        nAlloc += 1 
                        lastId = int(line)
                currentId = int(lastId - responsibles)
            if(currentId >= 0 and nAlloc < nNodes ):
                nodeId = currentId
                idsfile.write(str(nodeId) + "\n")
                idsfile.close()
            else: 
                idsfile.close()
                nodeId = -1
                print("Numero de servidores completo")
                self.event.set()
                sys.exit()            

            currentId = (2**nBits - 1)
            idsArray = []
            for i in range(0,nNodes):
                previousId = currentId-responsibles+1
                if previousId < 0 or (previousId - responsibles) < 0:
                    previousId = 0
                idsArray.append(currentId)
                currentId = previousId-1
            idsArray.reverse()
            ftSize =  math.ceil(math.log(nNodes,2))
            try:
                ft = "./chord/finger-table-" + str(nodeId)
                ftfile = open(ft, 'a')
                for i in range(1,ftSize):
                    n = nodeId +  2**(i-1)
                    line = str(i) + " " + str( self.findFtSuc( n,idsArray ) ) + "\n"
                    ftfile.write(line)
            except:
                pass
            ftfile.close()
        return nodeId
    
    def reload_hash(self):

        try:
            with open('snap.' + str(self.countLog), 'r') as file:
                for line in file:  # lê o arquivo linha por linha
                    line_stream = line.split(" ")
                    key = int(line_stream[0])
                    data = str(" ".join(line_stream[1:]))
                    data = data.replace('\n', '')
                    self.hash[key] = data
        except:
            pass

        try:
            with open('logfile.' + str(self.countLog), 'r') as file:
                for line in file: #lê o arquivo linha por linhaq
                    line = line.replace('\n','')
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

        while not self.event.is_set():
            if not self.log_queue.empty():
                _, data = self.log_queue.get()  # data é o que recebeu do usuário, basicamente o comando
                if data.split()[0] != "READ":
                    if os.path.isfile(('logfile.' + str(self.countLog - 3))):
                        os.remove('logfile.' + str(self.countLog - 3))
                    try:
                        logfile = open('logfile.' + str(self.countLog), 'a')
                    except:
                        logfile = open('logfile.' + str(self.countLog), 'w')
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
                nodeIdsfile = "./chord/nodeIdsBreaked"
                idsfile = open(nodeIdsfile, 'a')
                idsfile.write( str(self.nodeId) + '\n' )
                idsfile.close()
                time.sleep(5)
                self.s.close()
                self.timer.stop()
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
        self.start_snap_thread()
        self.program_loop()

    def modify_log(self):

        if os.path.isfile(('logfile.' + str(self.countLog))):
            self.countLog += 1
            with open('snap.' + str(self.countLog), 'w') as f:
                f.writelines([str(i)+' ' + self.hash[i]+'\n' for i in list(self.hash.keys())])
                f.flush()

            if os.path.isfile(('snap.' + str(self.countLog-3))):
                os.remove('snap.' + str(self.countLog-3))
            self.config["DEFAULT"]["LAST_SNAP"] = str(self.countLog)
            with open('.config', 'w') as configfile:
                self.config.write(configfile)
        self.start_snap_thread()

    def start_snap_thread(self):
        self.timer = threading.Timer(self.timeOfSnaps, self.modify_log)
        self.timer.start()


def run_server():
    load_dotenv()
    server = Server()
    server.run()


if __name__ == '__main__':

    run_server()
