"""
@author: Tara Saba
"""
import socket
import threading
import mysql.connector
from mysql.connector import Error

PORT = 8888
MESSAGE_LENGTH_SIZE = 64
ENCODING = 'utf-8'
FILE_SIZE= 16384
clients =[]
def main():
#    address = socket.gethostbyname(socket.getfqdn())
    address = "192.168.1.100"
    HOST_INFORMATION = (address, PORT)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(HOST_INFORMATION)
    print("Server is starting ...")

    connect_db()

    start(s)
def connect_db():
    try:
        db = mysql.connector.connect(host='localhost',user='root')
        if db.is_connected():
            db_cursor = db.cursor()
            print("database starting ...")
            create_db(db_cursor)
            db.commit()
            db_cursor.close()
    except Error as e:
        print("Error while connecting to MySQL", e)

def create_db(db_cursor):
    try:
        db_cursor.execute("drop database server;")
    except:
        print()
    try:
        db_cursor.execute("create database server;")
    except:
        print()
    try:
        db_cursor.execute("use server;")
    except:
        print("errrrrrrpr")
    try:
        db_cursor.execute("create table users (username varchar(255) primary key , ip varchar(255) ,port int);")
    except:
        print("error")
    try:
        db_cursor.execute("create table groups (groupname varchar(255), member varchar(255), CONSTRAINT PK primary key (groupname, member));")
    except:
        print("error")
def start(serverSocket):
    serverSocket.listen()
    while True:
        connection, address = serverSocket.accept()
        thread = threading.Thread(target= client_handler, args= (connection,address))
        thread.start()

def get_username(connection, address ,type):
    valid = True
    while valid :
        header_length = int(connection.recv(MESSAGE_LENGTH_SIZE).decode(ENCODING))
        header = connection.recv(header_length).decode(ENCODING)
        username_length = int(connection.recv(MESSAGE_LENGTH_SIZE).decode(ENCODING))
        username = connection.recv(username_length).decode(ENCODING)

        rt=db_handler()
        if rt[0]:
            db_cursor = rt[1]
            try:
                if type ==1:
                    db_cursor.execute("insert into users values (\'"+str(username)+"\',\'" +str(address[0])+"\',\'" +str(address[1])+"\');")
                if type ==2:
                    db_cursor.execute("select username from users where ip=\'" +address[0]+"\' and port="+str(address[1])+";")
                    users= db_cursor.fetchall()
                    for us in users:
                        nusername = us[0]

                    db_cursor.execute("update users set username=\'"+username+ "\' where ip=\'" +address[0]+"\' and port="+str(address[1])+";")
                    db_cursor.execute("update groups set member=\'" + username + "\' where member=\'" + nusername + "\' ;")
                rt[2].commit()
                db_cursor.close()
                valid = False
            except:
                send_message(connection,"[Server]: sorry, that username is taken! try again!",'m')
                #print("unable to insert the record")

    return username

def create_group(connection, username):
    invalid = True
    send_message(connection, "[Server]: enter the name of the group ", 'm')
    while invalid:
        group,header= receive_message(connection)
        rt= db_handler()
        if rt[0]:
            db_cursor = rt[1]
            db_cursor.execute("select distinct groupname from groups;")
            groups =db_cursor.fetchall()
            found = False
            #if "\'"+group+"\'," in groups:
             #   found= True
            for gr in groups:
                if group == gr[0]:
                    found= True
                    send_message(connection, "[Server]: that name has already been taken try another name! ", 'm')
            if not found:

                try:
                    db_cursor.execute("insert into groups values (\'" +group+ "\' ,\'" + username+"\');")
                    rt[2].commit()
                    db_cursor.close()
                    invalid = False
                    send_message(connection,"[Server]: The group has been created! You can now start adding members. In order to add members first enter \"add to @groupname\" and then the server will provide you with further instructions."
                                             ,'m')
                except:
                    send_message(connection,"[Server]: Unable to create group! try again!",'m')

        else:
            send_message(connection,"[Server]: Unable to connect to the database",'m')
def leave(group , connection, username):
    rt=db_handler()
    if rt[0]:
        db_cursor = rt[1]
        db_cursor.execute("select distinct groupname from groups;")
        groups = db_cursor.fetchall()
        gfound=False
        for gr in groups:
            if group==gr[0]:
                gfound= True
        if gfound:
                      try:
                        flag, members = find_group(group, username, connection)
                        for mem in members:
                             if mem!=username:
                              mem = find_connection(mem)
                              send_message(mem, "@" + username + " left " + group, 'm')
                        rt[1].execute("delete from groups where member=\'" + str(username) + "\';")
                        rt[2].commit()
                        db_cursor.close()
                        send_message(connection,"[Server]: you successfully left the group!",'m')

                      except:
                          print()
        else:
                send_message(connection, "[Server]: Group not found!",'m')
    else:
        send_message(connection, "[Server]: Unable to connect to the database",'m')
def add_member(group , connection, username):
    rt=db_handler()
    if rt[0]:
        db_cursor = rt[1]
        db_cursor.execute("select distinct groupname from groups;")
        groups = db_cursor.fetchall()
        gfound=False
        for gr in groups:
            if group==gr[0]:
                gfound= True
        if gfound:
                ufound=False
                db_cursor.execute("select member from groups where groupname = \'"+group+"\'; ")
                members=db_cursor.fetchall()
                for member in members:
                    if username==member[0]:
                        ufound=True
                if ufound:
                    send_message(connection,"[Server]: enter the id of the new member in the following pattern (without @): memberid",'m')
                    mem, header=receive_message(connection)
                    check = find_connection(mem)
                    if check != "nope":
                      try:
                        db_cursor.execute("insert into groups values (\'" +group+ "\' ,\'" + mem+"\');")
                        rt[2].commit()
                        db_cursor.close()
                        send_message(connection,"[Server]: "+mem+" is successfully added to the group!",'m')
                      except:
                          send_message(connection, "[Server]: " + mem + " is already in the group!", 'm')
                    else:
                        send_message(connection, "[Server]: user not found!",'m')
                else:
                    send_message(connection,"[Server]: Sorry you are not a member of this group thus you can't add any members",'m')
        else:
                send_message(connection, "[Server]: Group not found!",'m')
    else:
        send_message(connection, "[Server]: Unable to connect to the database",'m')
def client_handler(connection, address):
    username =get_username(connection,address,1)
    clients.append(connection)
    send_message(connection,"[Server]: Welcome "+username,'m')
    broadcast("[Server]: " +username+ " just joined!",connection)
    connected = True
    while connected:
        message, header=receive_message(connection)
        if header=='q':
            if message == "DISCONNECT":
                rt=db_handler()
                if rt[0]:
                    rt[1].execute("delete from users where username=\'" + str(username)+"\';")
                    try:
                        rt[1].execute("delete from groups where member=\'" + str(username) + "\';")
                    except:
                        print()
                    rt[2].commit()
                    rt[1].close()
                connected = False
            elif message== "change username":
                 send_message(connection, "[Server]: enter the new username ",'m' )
                 username= get_username(connection,address,2)
                 send_message(connection,"[Server]: username successfully changed to " + username,'m')

            elif message[0:3]== "add":
                #send_message(connection,"ok",'m')
              try:
                groupname = message.split('@',1)[1]
                add_member(groupname,connection, username)
              except:
                  send_message(connection, "wrong pattern!", 'm')
            elif message=="ls":
                ls(connection,username)
            elif message =="lsg":
                lsg(connection)
            elif message=="create group":
                 create_group(connection,username)
            elif message[0:3]=="lsm":
                try:
                    groupname = message.split('@', 1)[1]
                    lsm(groupname, connection,username)
                except:
                    send_message(connection, "wrong pattern!", 'm')
            elif message[0:5] == "leave":

                try:
                    groupname = message.split('@', 1)[1]
                    leave(groupname, connection, username)
                except:
                    send_message(connection, "wrong pattern!", 'm')
        elif header=='m':
            if len(message)!=0:
                flag= False
                try:
                    reciepent, mesToSend =message.split("@",1)[1].split(":",1)
                    flag = True
                except:
                    send_message(connection, "wrong pattern!",'m')
                if flag:
                    rec = find_connection(reciepent)
                    flag,members =find_group(reciepent, username, connection)
                    if rec!= "nope":
                        send_message(rec,"["+username+"]:"+mesToSend,'m')
                    elif flag==True:
                        for mem in members:
                            mem = find_connection(mem)
                            send_message(mem,"["+username+"@"+reciepent+"]:"+mesToSend,'m')
                    elif rec=="nope" and flag==False and members!='d':
                        send_message(connection,"[Server]: " + reciepent+ " not found!",'m')

        elif header[0]=='f':
            flag, members=find_group(message, username, connection)
            if flag==False:
                members=[]
                members.append(message)
            rec_send_file_group(connection,header,members,username,message)
    send_message(connection,"[Server]: you went offline",'m')
    clients.remove(connection)
    broadcast("[Server]: "+username + " went offline", connection)
    connection.close()

def lsm(groupname, connection, username):
    rt = db_handler()
    if rt[0]:
        db_cursor = rt[1]
        db_cursor.execute("select distinct groupname from groups;")
        groups = db_cursor.fetchall()
        gfound = False
        for gr in groups:
            if groupname == gr[0]:
                gfound = True
        if gfound:
            ufound = False
            db_cursor.execute("select member from groups where groupname = \'" + groupname + "\'; ")
            members = db_cursor.fetchall()
            for member in members:
                if username == member[0]:
                    ufound = True
            if ufound:
                try:
                    stringuser = []
                    ustr = "[Server]: "
                    for member in members:
                        stringuser.append(member[0])
                    for member in stringuser:
                        if member != username:
                            ustr += "@" + str(member) + "\t"
                        else:
                            ustr += "@" + str(member) + "(You)" + "\t"

                    send_message(connection, ustr, 'm')
                except:
                    print("something went wrong")
            else:
                send_message(connection,
                                 "[Server]: Sorry you are not a member of this group thus you can't view the members list",
                                 'm')
        else:
                send_message(connection, "[Server]: Group not found!", 'm')
    else:
            send_message(connection, "[Server]: Unable to connect to the database", 'm')


def rec_send_file_group(connection,header,members,username,group):
    count = int(header[1:])
    flag = True
    connections=[]
    for mem in members:
        connections.append(find_connection(mem))
    empty, extension = receive_message(connection)
    co=0
    receiver_name=0
    for receiver in connections:
        if receiver == "nope":
            receiver_name=co
            flag= False
        co+=1
    if flag:
     counter = 1
     for receiver in connections:
        send_message(receiver, username+"*"+group+"%"+str(counter), 'f' + str(count))
        counter+=1
     extension = extension.encode(ENCODING)
     msg_length = len(extension)
     msg_length = str(msg_length).encode(ENCODING)
     msg_length += b' ' * (MESSAGE_LENGTH_SIZE - len(msg_length))
     for receiver in connections:
        receiver.send(msg_length)
        receiver.send(extension)
     while (count > 0):
            if count != 1:
                temp=connection.recv(FILE_SIZE)
                for receiver in connections:
                    receiver.send(temp)
            else:
                message, size = receive_message(connection)
                head = str(size).encode(ENCODING)
                size = int(size)
                header_len = len(head)
                header_len = str(header_len).encode(ENCODING)
                header_len += b' ' * (MESSAGE_LENGTH_SIZE - len(header_len))
                for receiver in connections:
                    receiver.send(header_len)
                    receiver.send(head)
                temp=connection.recv(size)
                for receiver in connections:
                    receiver.send(temp)
            count -= 1
    else:
        send_message(connection, "[Server]: " + members[receiver_name] + " not found!", 'm')

def receive_message(connection):
    header_length = int(connection.recv(MESSAGE_LENGTH_SIZE).decode(ENCODING))
    header = connection.recv(header_length).decode(ENCODING)
    message_length = int(connection.recv(MESSAGE_LENGTH_SIZE).decode(ENCODING))
    message = connection.recv(message_length).decode(ENCODING)
    return message,header
def ls(connection, username):
    rt= db_handler()
    if rt[0]:
        db_cursor = rt[1]
        try:
            db_cursor.execute("select username from users;")
            users = db_cursor.fetchall()
            stringuser=[]
            ustr="[Server]: "
            for user in users:
                stringuser.append(user[0])
            for user in stringuser:
                if user!= username:
                    ustr+="@"+str(user)+"\t"
                else:
                    ustr += "@" + str(user) +"(You)"+ "\t"
            send_message(connection,ustr,'m')
        except:
            print("something went wrong")
def find_group(groupname , username, connection):
    rt = db_handler()
    if rt[0]:
        db_cursor = rt[1]
        db_cursor.execute("select distinct groupname from groups;")
        groups = db_cursor.fetchall()
        gfound = False
        for gr in groups:
            if groupname == gr[0]:
                gfound = True
        if gfound:
            ufound = False
            db_cursor.execute("select member from groups where groupname = \'" + groupname + "\'; ")
            members = db_cursor.fetchall()
            for member in members:
                if username == member[0]:
                    ufound = True
            if ufound:
                try:
                    stringuser = []
                    for member in members:
                        stringuser.append(str(member[0]))
                    return True,stringuser
                except:
                    print("something went wrong")
            else:
                send_message(connection,
                             "[Server]: Sorry you are not a member of this group thus you can't send message to it",
                             'm')
                return False,'d'
        else:
            return False,''
    else:
        send_message(connection, "[Server]: Unable to connect to the database", 'm')
        return False, 'd'
def lsg(connection):
    rt = db_handler()
    if rt[0]:
        db_cursor = rt[1]
        try:
            db_cursor.execute("select distinct groupname from groups;")
            groups =db_cursor.fetchall()
            stringuser = []
            ustr = "[Server]: "
            for group in groups:
                stringuser.append(group[0])
            for group in stringuser:
                    ustr += "@" + str(group) + "\t"

            send_message(connection, ustr, 'm')
        except:
            print("something went wrong")
def find_connection(rec):
    rt=db_handler()
    if rt[0]:
        db_cursor = rt[1]
        try:
            db_cursor.execute("select ip,port from users where username=\'"+rec+"\';")
            address = db_cursor.fetchall()[0]
            for client in clients:
                 if client.getpeername()==address:
                     db_cursor.close()
                     return client
        except:
            return "nope"
def send_message(conn, message,header):
    head = header.encode(ENCODING)
    header_len = len(head)
    header_len = str(header_len).encode(ENCODING)
    header_len += b' ' * (MESSAGE_LENGTH_SIZE - len(header_len))
    mes = message.encode(ENCODING)
    msg_length = len(mes)
    msg_length = str(msg_length).encode(ENCODING)
    msg_length += b' '*(MESSAGE_LENGTH_SIZE - len(msg_length))
    conn.send(header_len)
    conn.send(head)
    conn.send(msg_length)
    conn.send(mes)

def broadcast(mes,broadcaster):
    for client in clients:
        if client!= broadcaster:
            send_message(client , mes,'m')

def db_handler():
    db = mysql.connector.connect(host='localhost', database='server', user='root')
    if db.is_connected():
        db_cursor = db.cursor()
        return (True ,db_cursor,db)
    else:
        return (False,"error")


if __name__ == '__main__':
    main()