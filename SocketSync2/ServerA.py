import socket
import threading
import time
import os


time.sleep(5)

lock_list = []
already_locked = []
update_content = []
# aserver A server socket
aserver = socket.socket()
#  A server port for B Server
ap = 5555
aserver.bind(('',ap))

print("Socket created for Server A at port ",ap)

bp = 7779
aserver.connect(('127.0.0.1',bp))

print("A Server connected to B server")


# getting Path for Server A
path = os.getcwd() + "\ServerA"


# function to list all files at server A
def serverFiles():
    a_server_files = os.listdir(path)
    a_list = list()
    for x in a_server_files:
        stats = os.stat(os.path.join(path,x))
        a_list.append([x, stats.st_size, stats.st_mtime])
    return a_list


def get_update_content():
    return update_content


fileList = serverFiles()


def startSync(b, mode, oldAfiles=None):
    # Getting B Server files
    global update_content
    Bfiles = eval(b.recv(4096).decode('utf-8'))
    Bfiles.sort()
    #print("Bfiles", Bfiles)
    # Getting A Server Files
    myfiles = serverFiles()
    myfiles.sort()

    # Print Starting Files
    if mode == 0:
        print("Initial files at Server A", myfiles)
        print("Initial files at Server B", Bfiles)

    if myfiles == Bfiles:
        b.send("None1".encode())
        time.sleep(1)
        b.send("None2".encode())
        if mode == 1:
            time.sleep(1)
            b.send("None3".encode())
        print("In sync")
        return myfiles

    # Only taking care of deleting files since the intial sync code takes care of add and modified files
    if mode == 1:
            oldAfiles.sort()
            # Checking if A server files have changed
            if myfiles == oldAfiles:
                if len(myfiles) > len(Bfiles):
                    print("A file has been deleted at B Server")
                    for delfile in myfiles:
                        if delfile not in Bfiles:
                            print(delfile[0].encode())
                            filePath = path + "\\" + delfile[0]
                            os.remove(filePath)
                            print("Removed File ", delfile[0])
                            b.send("None4".encode())
                            time.sleep(1)
                            b.send("None5".encode())
                            time.sleep(1)
                            b.send("None6".encode())
                            return Bfiles
            else:
                if len(myfiles) < len(oldAfiles):
                    print("A file has been deleted at A Server")
                    b.send("None7".encode())
                    time.sleep(1)
                    b.send("None8".encode())
                    time.sleep(1)
                    for delfile in oldAfiles:
                        if delfile not in myfiles:
                            b.send(delfile[0].encode())
                            print("Asked server B to remove file ",delfile[0])
                    time.sleep(1)
                    b.send("None9".encode())
                    return myfiles

    # store names to check for duplicates
    Bfiles_names = [x[0] for x in Bfiles]
    myfiles_names = [x[0] for x in myfiles]

    # Getting files from Server B to Server A
    for Bfile in Bfiles:
        if Bfile not in myfiles:
            # if found duplicate file rewrite file with recent modified time
            if Bfile[0] in myfiles_names:
                a_index = myfiles_names.index(Bfile[0])
                if myfiles[a_index][2] > Bfile[2]:
                    continue
                # new locking inclusion
                else:
                    if Bfile[0] in lock_list:
                        update_content_names = [x[0] for x in update_content]
                        if Bfile[0] in update_content_names:
                            #print("IN")
                            indies = []
                            for i in range(len(update_content)):
                                if update_content[i][0] == Bfile[0]:
                                   indies.append(i)
                            if Bfile[2] == update_content[indies[-1]][2]:
                                #print("SKIPING")
                                continue
                        # update save in FIFO queue
                        request = Bfile[0]  # filename
                        b.send(request.encode())
                        new_file_path = path + "\\" + Bfile[0]
                        bytes_array = []
                        #new_file = open(new_file_path, "wb")
                        print("Getting Locked file content ", Bfile[0])
                        fileData = b.recv(1024)
                        b.settimeout(1)
                        try:
                            while fileData:
                                bytes_array.append(fileData)
                                fileData = b.recv(1024)
                        except socket.timeout as _:
                            pass
                        b.settimeout(999999)
                        #new_file.close()
                        # setting modified time
                        new_time = Bfile[2]
                        #os.utime(new_file_path, (Bfile[2], Bfile[2]))
                        print("Locked file content stored", request)
                        locked_file_content = [Bfile[0],bytes_array,new_time]
                        update_content.append(locked_file_content)
                        print("Update content ",update_content)
                        continue
            #################################################################################
            request = Bfile[0] #filename
            b.send(request.encode())
            new_file_path = path + "\\" + Bfile[0]
            new_file = open(new_file_path, "wb")
            print("getting",new_file_path)
            fileData = b.recv(1024)
            b.settimeout(1)
            try:
                while fileData:
                    new_file.write(fileData)
                    fileData = b.recv(1024)
            except socket.timeout as _:
                pass
            b.settimeout(999999)
            new_file.close()
            # setting modified time
            os.utime(new_file_path, (Bfile[2], Bfile[2]))
            print("File added Server A from Server B ", request)
    # Done sending files
    time.sleep(1)
    b.send("None10".encode())

    # wait to sync
    time.sleep(1)

    # Transferring files from Server A to Server B
    for Afile in myfiles:
        if Afile not in Bfiles:
            if Afile[0] in Bfiles_names:
                b_index = Bfiles_names.index(Afile[0])
                if Bfiles[b_index][2] > Afile[2]:
                    continue
            request = Afile[0]
            print(request)
            b.send(request.encode())

            filePath = path + "\\" + request
            file = open(filePath, "rb")
            fileData = file.read(1024)
            while fileData:
                if fileData == "": break
                b.send(fileData)
                fileData = file.read(1024)
                print("reading",request)
            file.close()
            time.sleep(1)
            _mtime = str(Afile[2]).encode()
            b.send(_mtime)
            print("File add to at Server B from Server A", request)
            time.sleep(1)

    # Done getting files
    b.send("None11".encode())
    if mode == 1:
        time.sleep(1)
        b.send("None12".encode())
    myfiles = serverFiles()
    myfiles.sort()
    return myfiles

# Initial sync
startSync(aserver,0)


def clientThreadFunc():
    # socket for client
    cc = socket.socket()
    # A server port for Client
    port_num = 6666
    cc.bind(('', port_num))
    cc.listen(1)
    # waiting for client to connect
    # meanwhile Server A and Server B are getting in sync
    client, address = cc.accept()
    while True:
        user_input = client.recv(1024).decode()
        if user_input == "D":
            files = serverFiles()
            files.sort()
            for lfile in lock_list:
                for file in files:
                    if lfile == file[0]:
                        # if the file is locked we will inform the client it is locked
                        file.append("Locked")

            client.send(str(files).encode())

        # client aksing to lock file
        if user_input[0] == "L":
            file_number = int(user_input[1:])
            files = serverFiles()
            files.sort()
            file_name = files[file_number][0]
            print("User asked to lock file ",file_name)
            lock_list.append(file_name)
            print("Locked file successfully")

        # client aksing to unlock file
        if user_input[0] == "U":
            file_number = int(user_input[1:])
            files = serverFiles()
            files.sort()
            # get file name from index
            file_name = files[file_number][0]
            print("User asked to unlock file ", file_name)

            update_content = get_update_content()
            #if file_name in already_locked:
            #    for x in updatev2:
            #        update_content.remove(x)

            #print("Unlock update content, ", update_content)
            indies = []
            # getting indies of all updates to the file
            for i in range(len(update_content)):
                if file_name == update_content[i][0]:
                    indies.append(i)

            tmp = update_content.copy()
            #run for each update counted in FIFO quee
            for i in indies:
                new_file_path = path + "\\" + file_name
                new_file = open(new_file_path, "wb")
                print("updating unlocked file", new_file_path)
                _array = update_content[i][1] # the bytes array where we store data from reading file
                #print("_array is ", _array)
                new_time = update_content[i][2]
                for j in _array:
                    new_file.write(j)
                new_file.close()
                # setting modified time
                os.utime(new_file_path, (new_time, new_time))
                #update_content.remove(tmp[i])
                # sleep 10 seconds so that we can see the changes in real time
                # that is, the file is updated in FIFO order.
                time.sleep(10)

            # now remove all updates that were made
            for i in indies:
                update_content.remove(tmp[i])

            #already_locked.append(file_name)
            #updatev2 = get_update_content()
            lock_list.remove(file_name)



clientThread = threading.Thread(target=clientThreadFunc)
# initialing client thread
# takes care of input from client
clientThread.start()

time.sleep(2)
oldFiles = serverFiles()

# while loop runs periodically to make sure server A and server B are in sync
while True:
    #print("Astart")
    time.sleep(3)
    aserver.send(" ".encode())
    #print("send")
    oldFiles = startSync(aserver, 1, oldAfiles=oldFiles)
    #print(oldFiles,"Over")
