
from socket import *
import time
import threading
import hashlib
import matplotlib.pyplot as plt


c = 0
complete = False
done = False



init = False

def send_requests(clientSocket, burst_size, requests):
    global complete, requests_pending, last_ds, done, c
    global no_requests, serverName, serverPort
    global time_sent, time_received, start, x, y, rcvd, state, squished
    global estimated_RTT, start, timeout_interval, establish, init
    
    cout = 0
    flag = False
    while not complete:
        
        for i in requests:
            offset = i*1448
            start = time.time()
            if i < no_requests-1:
                clientSocket.sendto(f"Offset: {offset}\nNumBytes: 1448\n\n".encode(),(serverName, serverPort))
            else:
                clientSocket.sendto(f"Offset: {offset}\nNumBytes: {last_ds}\n\n".encode(),(serverName, serverPort))

            time_sent[i] = time.time() - establish
            #offset += 1448
            #time.sleep(1/(burst_size*50))
            cout += 1
            if cout == 4:
                cout = 0
                time.sleep(timeout_interval/30)
        
        #print("Burst size: ", burst_size)
            
        if state == 0:
            if rcvd < burst_size:
                burst_size = max(burst_size//2, 1)
            elif rcvd == burst_size:
                burst_size = min(burst_size+2, no_requests-c)
        elif state == 1:
            burst_size = max(burst_size//2, 1)
            time.sleep(0.5)
            state = 2
            
        rcvd = 0
        """if not init:
            init = True
            #print(time_sent)
            plt.plot([time_sent[i]*1000 for i in requests], [i*1448 for i in requests], 'bo', label='Sent Time')
            
            indices = [i for i in requests if time_received[i] > 0]
            plt.plot([time_received[i]*1000 for i in indices], [i*1448 for i in indices], 'ro', label='Received Time')
        
        else:
            plt.plot([time_sent[i]*1000 for i in requests], [i*1448 for i in requests], 'bo')
            
            indices = [i for i in requests if time_received[i] > 0]
            plt.plot([time_received[i]*1000 for i in indices], [i*1448 for i in indices], 'ro')"""
        
        if requests[-1] == no_requests-1 or flag:
            flag = True
            count = 0
            #h = requests[-1]
            requests = []
            
            for i in range(no_requests):
                if requests_pending[i] == 1:
                    requests.append(i)
                    count += 1
                    
                if count == burst_size:
                    break
        else:
            h = requests[-1] 
            if h+1 == no_requests-1:
                requests = [no_requests-1] 
            elif h+1+burst_size >= no_requests-1:
                requests = [i for i in range(h+1, no_requests)]
            else:
                requests = [i for i in range(h+1, h+1+burst_size)]
                
        if requests != []:     
            time.sleep(timeout_interval/30) 
        else:
            complete = True
            print("Done")
            return        
        
        
        
    
        
def receive_messages(clientSocket):
    global c, complete, received_data, requests_pending, no_requests
    global time_sent, time_received, start, rcvd, done, estimated_RTT, start
    global timeout_interval, dev_rtt, establish, state, squished
    
    rcvd = 0
    temp = no_requests
    while temp != 0:
        while True:
            #clientSocket.settimeout(3*estimated_RTT)
            try:
                
                reply, serverAddress = clientSocket.recvfrom(2048)
                
                #print("TEMP: ", temp)
                #print("Time: ", time.time() - start)
                estimated_RTT = 0.9*estimated_RTT + 0.1*(time.time() - start)
                #estimated_RTT = (1-0.125)estimated_RTT + 0.125(time.time() - start)
                #print("RTT: ", estimated_RTT)
                dev_rtt = 0.75*dev_rtt + 0.25*(abs((time.time() - start) - estimated_RTT))
                timeout_interval = estimated_RTT + 4*dev_rtt
                #print("Estimated RTT: ", estimated_RTT)
                #print("Dev RTT: ", dev_rtt)
                decoded_data = reply.decode() 
                #print(decoded_data)
                offset_line = decoded_data.split('\n')[0]
                data_list = decoded_data.split('\n', 3)
                
                if data_list[2] == 'Squished' and state == 0:
                    print('SQUISHED')
                    squished = True
                    state = 1
                elif data_list[2] == '' and state == 2:
                    print('NOT ANYMORE')
                    squished = False
                    state = 0
                
                o = int(offset_line.split(': ')[1])
                index = o//1448
                print(index)
                if data_list[2] == 'Squished':
                    received_data[index] = data_list[3][1:]
                else:
                    received_data[index] = data_list[3]
                
                time_received[index] = time.time() - establish
                
                if requests_pending[index] != 0:
                    requests_pending[index] -= 1
                    temp -= 1
                    rcvd += 1
                    c += 1
                #print(c)
                
                break
            except timeout:
                print("TIMEOUT")
                break
            except:
                print('Connection lost from server')
                break
    done = True
    print("Completed")
    
def main():
    
    global c, complete, sleep, received_data, requests_pending
    global no_requests, serverName, serverPort, last_ds
    global time_sent, time_received, start, x, y, establish, state, squished
    global burst_size, estimated_RTT, offset, dev_rtt, timeout_interval
    
    burst_size = 4

    x = []
    y = []
    
    #serverName = "vayu.iitd.ac.in"
    serverName = "127.0.0.1"
    #serverName = "10.17.7.134"
    serverPort = 9801

    clientSocket = socket(AF_INET, SOCK_DGRAM)
    clientSocket.connect((serverName, serverPort))
    message = "SendSize\nReset\n\n"
    clientSocket.sendto(message.encode(),(serverName, serverPort))
    reply, serverAddress = clientSocket.recvfrom(2048)
    r = reply.decode()
    #print(r)
    #clientSocket.close()
    size_string = r.split(":")[1].strip()
    size = int(size_string)
    
    #no_requests = 50
    no_requests = (size//1448)+1
    last_ds = size - ((no_requests-1)*1448)
    requests_pending = [1]*no_requests
    time_sent = [0]*no_requests
    time_received = [0]*no_requests
    estimated_RTT = 0.01
    dev_rtt = 0.125
    timeout_interval = estimated_RTT + 4*dev_rtt
    print("Number of requests to be sent: ", no_requests)
    
    received_data = [""]*no_requests
    requests = [i for i in range(burst_size)]
    state = 0
    squished = False
    
    receive_thread = threading.Thread(target=receive_messages, args=(clientSocket,))
    receive_thread.start()
    #start = time.time()
    establish = time.time()
    send_requests(clientSocket, burst_size, requests) 
    
    #print(received_data)
    data = "".join(received_data)
    #print(data)
    hash_object = hashlib.md5(data.encode())
    hex_digest = hash_object.hexdigest()
    md5_hash = hex_digest.lower()
    print(f"MD5 hash for data: {md5_hash}")
    for i in received_data:
        if i == "":
            print("YES")
    clientSocket.sendto(f"Submit: 2021CS50614@idk\nMD5: {md5_hash}\n\n".encode(), (serverName, serverPort))
    
    a = True
    while a:
        while True:
            #clientSocket.settimeout(0.1)
            try:
                reply, serverAddress = clientSocket.recvfrom(2048)
                decoded_data = reply.decode() 
                
                if decoded_data.startswith("Result"):
                    a = False
                    print(decoded_data)
                break
            except timeout:
                print("TIMEOUT")
                break
            except:
                print('Connection lost from server')
                break

    
    clientSocket.close()

    
    #plt.plot(x[0], [i*1448 for i in range(len(x[0]))], 'bo-', label='Received Time')
    
    

    
    """plt.xlabel('Time (milliseconds)')
    plt.ylabel('Offset')
    plt.title('Offset vs Time')
    plt.legend()
    plt.show()"""
    
main()

# MD5: b3b08d9a6a47c706850ed972d1840b1d