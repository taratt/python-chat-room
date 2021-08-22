"""
@author: Tara Saba
"""

import socket
import threading
import os
PORT = 8888
MESSAGE_LENGTH_SIZE = 64
ENCODING = 'utf-8'
FILE_SIZE= 16384
def main():
    address = "192.168.1.100"
    SERVER_INFORMATION = (address, PORT)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(SERVER_INFORMATION)
    username = input("username( You can use a-z, 0-9 and underscore only):")
    send_message(s,'q',username)
    receive_thread = threading.Thread(target=receive_message, args=(s,))
    receive_thread.start()
    send_thread = threading.Thread(target=sender_message, args=(s,))
    send_thread.start()

def sender_message(client):
    isconnected = True
    while (isconnected):
        message = input()
        if len(message)!= 0:
            if (message == 'end'):
                isconnected = False
                send_message(client,'q',"DISCONNECT")
            elif message[0]=='@' :
                try:
                    rec, rest = message.split(":", 1)
                    header, mess = rest.split(":", 1)
                    if header=='m':
                        send_message(client,'m',rec+":"+mess)
                        print("[the message is sent to the Server!]")
                    elif header =='f':
                        send_file(client,mess,rec.split("@",1)[1])
                except:
                    print("wrong pattern!")
            else:
                send_message(client,'q',message)
def send_message(client, header,message):
    head= header.encode(ENCODING)
    header_len = len(head)
    header_len = str(header_len).encode(ENCODING)
    header_len += b' ' * (MESSAGE_LENGTH_SIZE - len(header_len))
    mes = message.encode(ENCODING)
    msg_length = len(mes)
    msg_length = str(msg_length).encode(ENCODING)
    msg_length += b' '*(MESSAGE_LENGTH_SIZE - len(msg_length))
    client.send(header_len)
    client.send(head)
    client.send(msg_length)
    client.send(mes)


def send_file(client,path,receiver):
 try:
    with open(path,"rb") as file:
        filename, fileExtension=os.path.splitext(path)
        size=os.path.getsize(path)
        count =(int(size/16384 +1))
        shadow=count-1
        header='f'+str(count)
        send_message(client,header,receiver)
        send_message(client, fileExtension, '')
        while(count>0):
            if count !=1:
                mes = file.read(16384)
                client.send(mes)
            else:
                header=str(size-(shadow*16384))
                #print(header)
                mes= file.read(size-(shadow*16384))
                #head = header.encode(ENCODING)
                #header_len = len(head)
                #header_len = str(header_len).encode(ENCODING)
                #header_len += b' ' * (MESSAGE_LENGTH_SIZE - len(header_len))
                #client.send(header_len)
                #client.send(head)
                send_message(client,header,'')
                client.send(mes)
            count-=1
    print("[the file is sent!]")
 except:
     print("file not found!")
    #print("file sent")


def receive_file(client, header, message):
    count=int(header)
    sender,rest =message.split("*",1)
    g,c=rest.split("%",1)
    ex_len = int(client.recv(MESSAGE_LENGTH_SIZE).decode(ENCODING))
    extension = client.recv(ex_len).decode(ENCODING)
    with open("received_"+g+c+extension,"wb") as file:
        while(count>0):
           if count!=1:
            file.write(client.recv(FILE_SIZE))
           else:
              #file.write(client.recv(int(message)))
              length =int(client.recv(MESSAGE_LENGTH_SIZE).decode(ENCODING))
              size=int(client.recv(length).decode(ENCODING))
              file.write(client.recv(size))
           count-=1
    print("["+sender+"@"+g+"]: sent you a file!(filename:)"+"received_"+g+c+extension)
def receive_message(client):
    receive = True
    while(receive):
        header_len=int(client.recv(MESSAGE_LENGTH_SIZE).decode(ENCODING))
        header= client.recv(header_len).decode(ENCODING)
        if(header=='m'):
            message_length = int(client.recv(MESSAGE_LENGTH_SIZE).decode(ENCODING))
            message = client.recv(message_length).decode(ENCODING)
            if message == "[Server]: you went offline":
                receive = False
            print(message)
        elif(header[0]=='f'):
            message_length = int(client.recv(MESSAGE_LENGTH_SIZE).decode(ENCODING))
            message = client.recv(message_length).decode(ENCODING)
            receive_file(client,header[1:],message)


if __name__ == '__main__':
    main()