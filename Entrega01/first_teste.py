import threading
import socket
import time
import os
from dotenv import load_dotenv
load_dotenv()
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
        input()
    # metodo automatico (sem apertar enter)
    def execute2(self,command):
        self.s.send(command.encode())
        msg = self.s.recv(self.buffer_size).decode()
        print(msg)
        return msg
    def run(self):
        # CRUD OK
        print("CRUD OK")
        self.execute("CREATE 1001 ItemI")
        self.execute("READ 1001")
        self.execute("UPDATE 1001 ItemI2")
        self.execute("READ 1001")
        self.execute("DELETE 1001")
        # CRUD NOK
        print("CRUD NOK")
        self.execute("CREATE 1004 ItemI")   # nao existente
        self.execute("CREATE 1004 ItemI")
        self.execute("READ 1050 ItemJ")    # nao existente
        self.execute("UPDATE 1050 ItemJ2") # nao existente
        self.execute("READ 1005 ItemJ")
        self.execute("DELETE 1005 ItemJ")
        # Recuperação do Estado
        print("Recuperação do Estado \n")
        i=0;        
        startId 1010
        for i in range(5):
            number = startId + i # apenas um offset para evitar conflitos de id
            self.execute2("CREATE "+str(number)+" Item"+str(number))
        self.s.close()
        input("Reinicie o Servidor e aperte enter")        
        # recria o socket e reconecta
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect((self.host, self.port))
        
        startId += 5
        for i in range(5):
            number = startId + i # apenas um offset para evitar conflitos de id
            self.execute2("CREATE "+str(number)+" Item"+str(number))
        
        # Ordem de Execução
        print("Ordem de Execução")
        self.execute("CREATE 0 1") # o registro a0 é o 0 começa com o valor "1"
        for i in range(1,1001): 
            v = int(self.execute2( "READ "+str(i-1) )) + 1
            self.execute2("CREATE "+ str(i) + " " + str(v))
        print(str(i) + "Itens inseridos \n >READ a1000: ")     
        self.execute("READ 1000")
clientTest = ClientTest()
clientTest.run()