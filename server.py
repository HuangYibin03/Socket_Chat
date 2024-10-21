import socket
from threading import Thread

clients = {}  # 存储已连接的客户端和对应的名称

class ClientThread(Thread):
    def __init__(self, client_socket, client_address):
        Thread.__init__(self)
        self.client_socket = client_socket
        self.client_address = client_address
        self.client_name = None
        print(f"[+] New connection from {client_address}")

    def run(self):
        global clients
        # 接收客户端发送的名字
        self.client_name = self.client_socket.recv(1024).decode("utf-8")
        clients[self.client_socket] = self.client_name
        # self.broadcast(f"{self.client_name} has joined the chat.", self.client_socket)
        self.broadcast(f'server@wind:{self.client_name} has joined the chat.', self.client_socket,0)
        # self.broadcast(f'<div style="color:gray; text-align:ceconter;">server@wind:{self.client_name} has joined the chat.</div>', self.client_socket,0)
        self.broadcast_user_list()
        while True:
            try:
                message = self.client_socket.recv(1024)
                if message:
                    # 广播客户端消息，附加客户端名字
                    self.broadcast(f"{self.client_name}: {message.decode('utf-8')}", self.client_socket,1)
                    
                else:
                    break
            except:
                break

        # 客户端断开连接
        print(f"[-] Connection closed from {self.client_address}")
        self.broadcast(f'server@wind:{self.client_name} has left the chat.', self.client_socket,0)
        # self.broadcast(f'<div style="color:gray; text-align:center;">{self.client_name} has left the chat.</div>', self.client_socket,0)
        # clients.pop(self.client_socket)
        self.broadcast_user_list()
        self.client_socket.close()

    def broadcast(self, message, sender_socket,flag):
        """广播消息给所有连接的客户端"""
        to_remove=[]
        #系统公共消息
        if flag==0:
            for client in clients:
                try:
                    client.send(message.encode())
                except:
                    to_remove.append(client)
                    
        #用户发送消息
        else:
            for client in clients:
                if client != sender_socket:
                    try:
                        left_message= f'{message}'
                        # left_message= f'<div style="text-align: left;">{message}</div>'
                        client.send(left_message.encode())
                    except:
                        to_remove.append(client)
        for client in to_remove:
            client.close()
            # clients.pop(client)
            clients.pop(client, None)
    def broadcast_user_list(self):
        to_remove=[]
        """广播当前在线用户列表"""
        client_list=list(clients.keys())
        user_list = ','.join(clients.values())  # 将用户名列表组合成字符串
        for client in client_list:
            try:
                client.send(f"USER_LIST:{user_list}".encode())  # 发送用户列表，使用特定前缀区分
            except:
                to_remove.append(client)
        for client in to_remove:
            client.close()
            # clients.pop(client)
            clients.pop(client, None)
def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    host = '0.0.0.0'
    port = 8080
    server_socket.bind((host, port))
    server_socket.listen(5)
    print("[*] Server started on port 8080")

    while True:
        client_socket, client_address = server_socket.accept()
        new_client = ClientThread(client_socket, client_address)
        new_client.start()

if __name__ == "__main__":
    server_thread = Thread(target=start_server)
    server_thread.start()

    while True:
        # 服务器端可以主动输入消息广播给所有客户端
        server_message = input("Server: ")
        for client in clients:
            try:
                client.send(f"Server: {server_message}".encode())
            except:
                client.close()
                clients.pop(client)
