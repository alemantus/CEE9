# DTU dependencies
import logging, UniversalFormat_pb2
from google.protobuf.json_format import MessageToJson
logging.basicConfig(level=logging.INFO)
#

import sys
import time
import ISO10368Lib
import paho.mqtt.client as mqtt

# define container id when starting program
RCDid = sys.argv[1]

# acces token for DTU mqtt broker
token = 'eyJhbGciOiJSUzI1NiJ9.eyJzdWIiOiJSRkRFTU8iLCJpYXQiOjE1NTYxNDMyMDAsImV4cCI6MTU2NzI4ODgwMCwiaXNzIjoib3JkYSIsImF1dGhvcml0aWVzIjoiVVNFUixWSVMiLCJhZGRpdGlvbmFsIjoiRVZCRSJ9.DuLZSACASb5sjfb_j6_OfZpibQxXAwy1G1JbQIczwlN2tv5TxlFx7u8PTEuP8Q-BSNoI8MY-iDoDKRcG4RXr5SeLpdXe9V0mSkQRgjdSaKt7jwN10vKC-ydXYNZ2Y4bWjv__-3cJKVl8Q8n3BZ5RnduprIwVfwZ3pOqUyq-mRRWJTOZfwBsqQfnjHUY8hgDmkCCJrKPldpV5_m6AljOFbszGFmY9sufYvQuXUTEtNboAp_xChQTNyJG9fEXhCc_Bks-qOoA5lHJoP-4WMMZZ4cwNBX78oHp__aSQkZD6oKHXyB-Sdvvs8QuobmdNHe-Qi-xjHsXOvVQXxvd8pb2hRA'

# delcare global variables used in on_message callback
lowerBound = "" 
upperBound = ""
setPoint = ""
connectControl = 0
kickControl = 2
currentBroker = 0 # 0 = DTU, 1 = our own
tempList = [lowerBound,upperBound,setPoint,kickControl]

tempContainer = -30

while(1):

    # mqtt initialize
    def on_connect(client, userdata, flags, rc):
        #print("Connected with result code "+str(rc))

        # Subscribing in on_connect() means that if we lose the connection and
        # reconnect then subscriptions will be renewed.

        client.subscribe("/container"+RCDid+"/lowerBound")
        client.subscribe("/container"+RCDid+"/upperBound")
        client.subscribe("/container"+RCDid+"/setPoint")
        client.subscribe("/container"+RCDid+"/kick")

        client.subscribe("EVBE/#")

    # The callback for when a PUBLISH message is received from the server.
    def on_message(client, userdata, msg):

        global tempList
        global currentBroker

        if(currentBroker == 0):
            data = UniversalFormat_pb2.Data()
            data.ParseFromString(msg.payload)

            print('Value type: ' + data.WhichOneof('value'))
            print(str(data.timestamp) + ' ' + data.meta['unit_name'] \
                + '(' + data.channel + '): ' + str(data.double) + ' ' + data.unit)

        

        elif(currentBroker == 1):
            if(str(msg.topic) == "/container"+RCDid+"/lowerBound"):
                tempList[0] = int(msg.payload)
                tempList[3] = 0
            elif(str(msg.topic) == "/container"+RCDid+"/upperBound"):
                tempList[1] = int(msg.payload)
                tempList[3] = 0
            elif(str(msg.topic) == "/container"+RCDid+"/setPoint"):
                tempList[2] = int(msg.payload)
                tempList[3] = 0
            elif(str(msg.topic) == "/container"+RCDid+"/kick"):
                tempList[3] = 1


    def on_publish(client,userdata,result):
        print("data published \n")
        pass


    global currentBroker

    ###### Starting DTU broker connection ######
    client = mqtt.Client()
    client.tls_set()
    #client.tls_insecure_set(True)
    client.username_pw_set(token, '')
    client.on_connect = on_connect
    client.on_message = on_message
    client.reconnect_delay_set(1, 120)

    client.connect('broker.syslab.dk', 5005, 60)

    currentBroker = 0

    client.loop_start()



    # save important variables



    client.loop_stop()

    ###### Starting our broker connection ######
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    client.username_pw_set(username="jfccfsnl",password="a95j7N6GPemj")

    client.connect("m24.cloudmqtt.com", 10832, 60)

    currentBroker = 0

    client.loop_start()

    bitString = ""
    Sair = ""
    Rair = ""
    connectControl = 1

    global tempList

    if(tempList[0] != "" and tempList[1] != "" and tempList[2] != "" ):
        # ensures that we only calculate new values on send from ui
        if (tempList[3] == 1):
            bitString, Sair, Rair = ISO10368Lib.containerString(tempList[0], tempList[1], tempContainer)
        if(bitString != "" and Sair != "" and Rair != ""):
            client.publish("/container"+RCDid+"/bitString", bitString, qos=0, retain=False)
            client.publish("/container"+RCDid+"/Sair", Sair, qos=0, retain=False)
            client.publish("/container"+RCDid+"/Rair", Rair, qos=0, retain=False)
            print(Sair)



    # Blocking call that processes network traffic, dispatches callbacks and
    # handles reconnecting.
    # Other loop*() functions are available that give a threaded interface and a
    # manual interface.
    client.loop_stop()
    #time.sleep(5)
