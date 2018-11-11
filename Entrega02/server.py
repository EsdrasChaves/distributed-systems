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


from concurrent import futures
import grpc
import services_pb2
import services_pb2_grpc


_ONE_DAY_IN_SECONDS = 60 * 60 * 24

input_queue = queue.Queue(maxsize=-1)
process_queue = queue.Queue(maxsize=-1)
log_queue = queue.Queue(maxsize=-1)
chord_queue = queue.Queue(maxsize=-1)


class Server(services_pb2_grpc.ServiceServicer):
    def __init__(self):
        self.host_address = os.getenv("HOST") + ":" + os.getenv("PORT") 
        self.event = threading.Event()
        self.hash = {}
        self.config = configparser.ConfigParser()
        self.config.read('.config')
        self.countLog = int(self.config["DEFAULT"]["LAST_SNAP"])
        self.timer = None
        self.timeOfSnaps = 10

        self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=15))

    def create(self, request, context):
        key = request.id
        data = request.data
        req = 'CREATE {} {}'.format(key, data)
        return self.enqueue_request(req)

    def read(self, request, context):
        key = request.id
        req = 'READ {}'.format(key)
        return self.enqueue_request(req)

    def update(self, request, context):
        key = request.id
        data = request.data
        req = 'UPDATE {} {}'.format(key, data)
        return self.enqueue_request(req)

    def delete(self, request, contex):
        key = request.id
        req = 'DELETE {}'.format(key)
        return self.enqueue_request(req)

    def enqueue_request(self, request):
        pipe = queue.Queue()
        input_queue.put((pipe, request))
        rsp = pipe.get()
        del pipe
        return services_pb2.ServerResponse(resposta=rsp)

    def findFtSuc(self,n,idsArray):
        nNodes = int(os.getenv("NNODES"))
        lastId = idsArray[len(idsArray)-1]
        for i in range(0,nNodes):
            if n > lastId:
                n = n - lastId+1 # esse +1 é porque reseta no 0
            if n <= idsArray[i]:
                return idsArray[i]
    
    def setNodeId(self):
        
        # VER DEPOIS QUE TERMINAR
        # # Modificar porta a cada novo servidor aberto
        # with open(".env", 'r') as fileEnv1:
        #     tail = []
        #     for line in fileEnv1:
        #             strip = [s for s in line.split()]
        #             if strip[0] != 'PORT':
        #                 tail.append(line)
        #             else:
        #                 port = int(strip[2])
        #                 if port > 22230:
        #                     port = 22222
        #                 else:
        #                     port += 1
                        
        #                 tail.append('PORT = ' + str(port) + "\n")

        #     with open(".env", 'w') as fileEnv2:
        #             fileEnv2.writelines(tail)                    
        # fileEnv1.close()
        # fileEnv2.close()
        
        nBits = int(os.getenv("NBITS"))
        nNodes = int(os.getenv("NNODES"))
        currentId = (2**nBits - 1)
        responsibles = int(2**nBits/nNodes)
        
        idsBreakedfile = "./chord/nodeIdsBreaked"
        breakedfile = open(idsBreakedfile, 'a')
        
        # Verificar se algum id de servidor quebrado foi encontrado
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
        # Procurar um id
            nodeIdsfile = "./chord/nodeIds"
            idsfile = open(nodeIdsfile, 'a')

            nAlloc = 0
            #Se o arquvio existe precisa buscar o ultimo id inserido
            if os.stat(nodeIdsfile).st_size != 0:
                lastId = currentId
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
            
            # Escrever as finger tables
            currentId = (2**nBits - 1)
            idsArray = []
            # Computar o id de todos os servidores
            for i in range(0,nNodes):
                previousId = currentId-responsibles+1
                if previousId < 0 or (previousId - responsibles) < 0:
                    previousId = 0
                idsArray.append(currentId)
                currentId = previousId-1
            idsArray.reverse()
            # Tamanho recomendado das finger tables = log2(N)
            ftSize =  math.ceil(math.log(nNodes,2)) + 1
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
        self.previousNode = nodeId - responsibles
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
                for line in file: #lê o arquivo linha por linha
                    line = line.replace('\n','')
                    self.process_command(reload=True, data=line)
        except:
            pass

    def enqueue_command(self):
        while not self.event.is_set():
            if not input_queue.empty():
                req = input_queue.get()
                
                # analisar se esse servidor é responsável pela chave recebida
                c,data = req
                query = data.split()
                key = int(query[1])
                
                
                if key > self.previousNode and key <= self.nodeId:
                    # Se é de responsabilidade desse sevidor entao enfilera nele
                    process_queue.put(req) # F2
                    log_queue.put(req)     # F3
                else:
                    # enfilerar no chord_queue
                    chord_queue.put(req) # F4
               
                
    def process_command(self, reload=False, data=""): 
        while not self.event.is_set():
            if not process_queue.empty() or reload == True:
                if reload == False:
                    c, data = process_queue.get()
                
                query = data.split()
                command = query[0]
                key = int(query[1])
                usr_data = " ".join(map(str, query[2:])) if len(query) > 2 else ""

                response_msg = ""

                if command == "CREATE":
                    if key not in list(self.hash.keys()):
                        self.hash[key] = usr_data
                        response_msg ="Successfully CREATED {} - {}".format(key, usr_data)
                    else:
                        response_msg ="There is already an entry with the key {}".format(key)
                
                elif command == "UPDATE":
                    if key in list(self.hash.keys()):
                        self.hash[key] = usr_data
                        response_msg = "Successfully UPDATED {} - new content: {}".format(key, usr_data)
                    else:
                        response_msg = "There is no entry with the key {}".format(key)
                
                elif command == "DELETE":
                    if key in list(self.hash.keys()):
                        self.hash.pop(key, None)
                        response_msg = "Successfully Removed entry {}".format(key)
                    else:
                        response_msg = "There is no entry with the key {}".format(key)

                elif command == "READ":
                    if key in list(self.hash.keys()):
                        response_msg = self.hash[key]
                    else:
                        response_msg = "There is no entry with the key {}".format(key)

                else:
                    response_msg = "Invalid command"

                if reload == False:
                    try:
                        c.put(response_msg)
                    except:
                        pass
                else:
                    break

    def log_command(self):

        while not self.event.is_set():
            if not log_queue.empty():
                _, data = log_queue.get()  # data é o que recebeu do usuário, basicamente o comando
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

    def forward_command(self):
        while not self.event.is_set():
            if not chord_queue.empty():
                req = chord_queue.get()
                c,data = req
                query = data.split()
                key = int(query[1])
                # Faz a leitura da finger table do seu nodeId
                ft = "./chord/finger-table-" + str(self.nodeId)
                forwards = []
                with open(ft, 'r') as file:
                    for line in file:
                        routes = line.split()
                        forwards.append(int(routes[1]))
                    
                    print(forwards)
                    # Procura a entrada na finger table com o 
                    # primeiro valor maior que a chave
                    anterior = -1
                    forward_to = -1
                    for i in range (0,len(forwards)):
                        atual = forwards[i]
                        if key < atual:
                            # se encontra um primeiro valor maior
                            # que a chave
                            print("menor")
                            if anterior != -1:
                                # se nao for o primeiro, foward é o anterior
                                forward_to = anterior
                            else:
                                # se for o primeiro, foward é o primeiro 
                                forward_to = atual
                            break
                        anterior = atual

                    # se o foward to nao foi definido, chegou no fim da tabela
                    # define entao como ultimo valor da tabela
                    if forward_to == -1:
                        forward_to = forwards[len(forwards)-1]
                    print("Forwrad Requisition TO:")
                    print(forward_to)

                    nodeIdsfile = "./chord/nodeIds"
                    server_on = False
                    servers = []
                    with open(nodeIdsfile, 'r') as file2:
                        for line in file2:
                            servers.append(int(line))
                        print(servers)
                        server_on = forward_to in servers
                        #TODO
                        if server_on:
                            print("Server is on!")
                        else:
                            print("Abort operation")
                        
                        
                        
                file.close()
                file2.close()

    def call_remote_procedure(self, request, host_address):
        channel = grpc.insecure_channel(host_address)
        stub = services_pb2_grpc.ServiceStub(channel)

        _connection, rqst = request 
        query = rqst.split()
        if query[0] == 'CREATE':
            rqst = " ".join(map(str, query[2:])) if len(query) > 2 else ""
            data = services_pb2.Data(id=int(query[1]), data=rqst)
            result = self.stub.create.future(data)
            result.add_done_callback(self.get_process_response(_connection))
        elif query[0] == 'UPDATE':
            rqst = " ".join(map(str, query[2:])) if len(query) > 2 else ""
            data = services_pb2.Data(id=int(query[1]), data=rqst)
            result = self.stub.update.future(data)
            result.add_done_callback(self.get_process_response(_connection))
        elif query[0] == 'READ':
            data = services_pb2.Id(id=int(query[1]))
            result = self.stub.read.future(data)
            result.add_done_callback(self.get_process_response(_connection))
        elif query[0] == 'DELETE':
            data = services_pb2.Id(id=int(query[1]))
            result = self.stub.delete.future(data)
            result.add_done_callback(self.get_process_response(_connection))
    
    def get_process_response(self, connection):
        def process_response(response, connection=connection):
            connection.put(response.result().resposta)
        return process_response

    def run(self):
        self.reload_hash()
        self.nodeId = self.setNodeId()
        enqueue_thread = threading.Thread(target=self.enqueue_command)
        enqueue_thread.setDaemon(True)
        enqueue_thread.start()

        process_thread = threading.Thread(target=self.process_command)
        process_thread.setDaemon(True)
        process_thread.start()

        log_thread = threading.Thread(target=self.log_command)
        log_thread.setDaemon(True)
        log_thread.start()

        forward_thread = threading.Thread(target=self.forward_command)
        forward_thread.setDaemon(True)
        forward_thread.start()
        
        services_pb2_grpc.add_ServiceServicer_to_server(
            Server(), self.server
        )

        print("Servidor " + str(self.nodeId) + " pronto para receber conexões!")
        self.server.add_insecure_port(self.host_address)
        self.server.start()

        self.start_snap_thread()

        try:
            while True:
                time.sleep(_ONE_DAY_IN_SECONDS)
        except KeyboardInterrupt:
                    self.event.set()
                    #MODIFICAR
                    self.server.stop(0)
                    print("Shutting down...")
                    nodeIdsfile = "./chord/nodeIdsBreaked"
                    idsfile = open(nodeIdsfile, 'a')
                    idsfile.write( str(self.nodeId) + '\n' )
                    idsfile.close()
                    time.sleep(5)
                    self.timer.cancel()

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


if __name__ == '__main__':
    load_dotenv()
    server = Server()
    server.run()
