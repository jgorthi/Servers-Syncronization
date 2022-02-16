import socket
import os
import time


time.sleep(5)

# bserver B server socket
bserver = socket.socket()
# bp B server port
bp = 7779
bserver.bind(('', bp))

print("Socket created for Server B at port ", bp)

bserver.listen(1)
# B server connection
aserver, address = bserver.accept()

print("B Server connected to A server")


# getting Path for Server B
path = os.getcwd() + "\ServerB"


# function to list all files at server B
def serverFiles():
    b_server_files = os.listdir(path)
    b_list = list()
    for x in b_server_files:
        stats = os.stat(os.path.join(path, x))
        b_list.append([x, stats.st_size, stats.st_mtime])
    return b_list



# First printing all files at server B at the time of start of execution

def startSync(a, mode):

    # mode 0 = Initial Sync
    # mode 1 = After Initial Sync

    b_files = serverFiles()
    a.send(str(b_files).encode())

    # Transferring requested files from Server B to Server A
    while True:
        fileName = a.recv(1024).decode()
        #print(None, fileName)
        if "None" in fileName:
            break
        filePath = path + "\\" + fileName
        file = open(filePath,"rb")
        fileData = file.read(1024)
        while fileData:
            a.send(fileData)
            fileData = file.read(1024)
        file.close()
        print("Reading ",fileName)
        time.sleep(1)

    # Getting files from Server A to Server B
    while True:
        fileName = a.recv(1024).decode()
        #print(None, fileName)
        if "None" in fileName:
            break
        #print(fileName)
        filePath = path + "\\" + fileName
        new_file = open(filePath, "wb")
        fileData = a.recv(1024)
        a.settimeout(0.5)
        try:
            while fileData:
                new_file.write(fileData)
                fileData = a.recv(1024)
        except socket.timeout as _:
            pass
        a.settimeout(999999)
        new_file.close()
        print("Writing ",fileName)
        mtime = eval(a.recv(1024).decode('utf-8'))
        # setting modified time
        os.utime(filePath, (mtime, mtime))

    # Delete file when asked by Server A
    while True and mode == 1:
        #print("Didn't check")
        fileName = a.recv(1024).decode()
        #print(None, fileName)
        if "None" in fileName:
            break
        print("Deleting ",fileName)
        filePath = path + "\\" + fileName
        os.remove(filePath)



# Initial Sync
startSync(aserver,0)


# while loop make sure it starts sync when server A signals
while True:
    #print("Bstart")
    if aserver.recv(1024):
        #print("in")
        startSync(aserver,1)
        #print("Out")


