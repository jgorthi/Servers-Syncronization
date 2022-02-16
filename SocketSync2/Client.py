import socket
import threading
import time


time.sleep(1)
# cs client socket
mysocket = socket.socket()
# cp client port
cp = 4444
mysocket.bind(('',cp))

print("Socket created for Client at port ", cp)

# A server port
acp = 6666
time.sleep(2)
mysocket.connect(('127.0.0.1',acp))
print("Client connected to Server A")


def ThreadA(aserver):
    while True:
        try:
            files = eval(aserver.recv(1024).decode('utf-8'))
            i = 0
            for x in files:
                # adding index here
                print("[",i,"] ",x)
                i+=1
            print("--------------------------------------------------------")
        except:
            pass
        time.sleep(1)


thread_a = threading.Thread(target=ThreadA,args=(mysocket, ))
# initialing thread to send input for server A when user asks
thread_a.start()

while True:
    user_input = input("Press D to list the directory contents\nPress L to lock and index\nPress U to unlock and index\n")
    user_input = str(user_input)
    user_input.replace(" ", "")
    if user_input[0] == "D":
        mysocket.send("D".encode())
    elif user_input[0] == "L":
        file_number = (user_input[1:])
        mysocket.send(user_input.encode())
    elif user_input[0] == "U":
        file_number = (user_input[1:])
        mysocket.send(user_input.encode())
    else:
        print("Invalid Command")
    time.sleep(1)



