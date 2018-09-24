from threading import Thread
import socket
import time
import os
from dotenv import load_dotenv
from server  import run_server


class ClientTest:

    def __init__(self): #tipo um construtor
        self.host = os.getenv("HOST")
        self.port = int(os.getenv("PORT"))
        self.buffer_size = int(os.getenv("BUFFER_SIZE"))
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #cria socket STREAM -> TCP, DGRAM -> UDP
        self.s.connect((self.host, self.port)) #conecta

    def execute(self,command):
        self.s.send(command.encode())
        msg = self.s.recv(self.buffer_size).decode()
        print(msg)

    # metodo automatico (sem apertar enter)
    def execute2(self,command):
        self.s.send(command.encode())
        msg = self.s.recv(self.buffer_size).decode()
        print(msg)
        return msg


    def run(self,param):
        # CRUD OK
        print("CRUD OK")
        self.execute("CREATE {}1 ItemI".format(param))
        self.execute("READ {}1".format(param))
        self.execute("UPDATE {}1 ItemI2".format(param))
        self.execute("READ {}1".format(param))
        self.execute("DELETE {}1".format(param))

        # CRUD NOK
        print("CRUD NOK")
        self.execute("CREATE {}2 ItemI".format(param))   # nao existente
        self.execute("CREATE {}2 ItemI".format(param))
        self.execute("READ {}3".format(param))    # nao existente
        self.execute("UPDATE {}3 ItemJ2".format(param)) # nao existente
        self.execute("READ {}3".format(param))
        self.execute("DELETE {}3".format(param))


        # Recuperação do Estado
        print("Recuperação do Estado \n")
        i=0        
        startId = (1+param)*100
        for i in range(5):
            number = startId + i # apenas um offset para evitar conflitos de id
            self.execute2("CREATE "+str(number)+" Item"+str(number))
        self.s.close()
        
    def parte2(self,param):
        startId = (1+param)*1000
        i=0        

        # recria o socket e reconecta
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect((self.host, self.port))
        
        startId += 5
        for i in range(5):
            number = startId + i # apenas um offset para evitar conflitos de id
            self.execute2("CREATE "+str(number)+" Item"+str(number))
        
        # Ordem de Execução
        print("Ordem de Execução")
        inicial = (param + 1)*10000 + 11
        self.execute("CREATE {} 1".format(inicial)) # o registro a0 é o 0 começa com o valor "1"
        for i in range(inicial + 1,inicial + 1001): 
            v = int(self.execute2( "READ "+str(i-1) )) + 1
            self.execute2("CREATE "+ str(i) + " " + str(v))
        print(str(i) + "Itens inseridos \n >READ a1000: ")     
        self.execute("READ {}".format(inicial + 1001))


if __name__ == '__main__':

    #server_thread = Thread(target=run_server)
    
    load_dotenv()
    thread = []
    clients = []
    for i in range(10):
        clients.append(ClientTest())

    for i in range(10):    
        thread.append(Thread(target=clients[i].run,args=(i,)))
        thread[-1].start()
        
    for i in range(10):
        thread[i].join()
        
    input('Encerre o Server')
    thread = []
    for i in range(10):
        thread.append(Thread(target=clients[i].parte2,args=(i,)))
        thread[-1].start()
        
    for i in range(10):
        thread[i].join()
        
        

