### DTU dependencies
import logging, UniversalFormat_pb2
from google.protobuf.json_format import MessageToJson
logging.basicConfig(level=logging.INFO)

###
import bme280
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
kickControl = 0
ourCounter = 0

tempList = [lowerBound,upperBound,setPoint,kickControl]
Deif = [0.0,0.0,0.0,0.0,0.0,0.0,0.0]
tempContainer = -30





while(1):

    ### Callbacks for DTU broker ###
    def on_connectDTU(client, userdata, flags, rc):
        print("Connected to DTU broker")
        clientOwn.publish("/container"+RCDid+"/on_connectOwn", "Connected to Own", qos=0, retain=False)

        clientDTU.subscribe("EVBE/#")

    def on_messageDTU(client, userdata, msg):
        global tempList
        global currentBroker
        global Deif
        data = UniversalFormat_pb2.Data()
        data.ParseFromString(msg.payload)

            #Gør så vi kun modtager effekt
        if(data.channel == "meter_active_power_sum"):
           # Deifstring = str(data.meta['unit_name']) + ' ' + str(data.double)

            ## Gør så vi kun modtager information fra DEIF
            if(data.meta['unit_name'][0:4] == "Deif"):
                DiefnrString = data.meta['unit_name']
                #Tager DIEF nummeret og laver det til int
                Diefnr = int(DiefnrString[7:8])
                Power = data.double
                #Sætter power in i et array, hvor array nr er DEIF nr.
                Deif[Diefnr] = Power
                #print(Diefnr)
                #print(Deif[Diefnr])
                Effekttotal = sum(i for i in Deif)
                a = [1, 2, 3, 4, 5]
                b = sum(i for i in a)
                print(b)
                print(Effekttotal)
                 ## print('Value type: ' + data.WhichOneof('value'))
                ## print(str(data.timestamp) + ' ' + data.meta['unit_name'] \
                 ##   + '(' + data.channel + '): ' + str(data.double) + ' ' + data.unit)

    def on_publishDTU(client,userdata,result):
        print("data published \n")
        pass

    ### Callbacks for DTU broker ###
    def on_connectOwn(client, userdata, flags, rc):
        print("Connected to own broker")
        clientOwn.publish("/container"+RCDid+"/on_connectOwn", "Connected to Own", qos=0, retain=False)

        clientOwn.subscribe("/container"+RCDid+"/lowerBound")
        clientOwn.subscribe("/container"+RCDid+"/upperBound")
        clientOwn.subscribe("/container"+RCDid+"/setPoint")
        clientOwn.subscribe("/container"+RCDid+"/kick")

    def on_messageOwn(client, userdata, msg):
        global kickControl

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


    def on_publishOwn(client,userdata,result):
        print("data published \n")
        pass



    if (connectControl == 0):
        ###### Starting DTU broker connection ######
        clientDTU = mqtt.Client()
        clientDTU.tls_set()
        #client.tls_insecure_set(True)
        clientDTU.username_pw_set(token, '')
        clientDTU.on_connect = on_connectDTU
        clientDTU.on_message = on_messageDTU
        clientDTU.reconnect_delay_set(1, 120)

        clientDTU.connect('broker.syslab.dk', 5005, 60)

        ###### Starting our broker connection ######
        clientOwn = mqtt.Client()
        clientOwn.on_connect = on_connectOwn
        clientOwn.on_message = on_messageOwn

        #clientOwn.username_pw_set(username="mqtt",password="3329646")
        #clientOwn.connect("87.63.168.126", 1883, 60)

        clientOwn.username_pw_set(username="jfccfsnl",password="a95j7N6GPemj")
        clientOwn.connect("m24.cloudmqtt.com", 10832, 60)

        connectControl = 1


    bitString = ""
    Sair = ""
    Rair = ""
    global tempList
    global ourCounter



    while(tempList[3] == 1 or ourCounter >= 5):
        ourCounter = 0

        bme76 = bme280.Bme280(i2c_bus=1,sensor_address=0x76)
        bme76.set_mode(bme280.MODE_FORCED)
        t1, p1, h1 = bme76.get_data()

        #bme77 = bme280.Bme280(i2c_bus=1,sensor_address=0x77)
        #bme77.set_mode(bme280.MODE_FORCED)
        #t2, p2, h2 = bme77.get_data()
        print(round(t1,2))
        clientOwn.publish("/container"+RCDid+"/tempInside", round(t1,2), qos=0, retain=False)
        #clientOwn.publish("/container"+RCDid+"/tempOutside", round(t2,2), qos=0, retain=False)
        if(tempList[0] != "" and tempList[1] != "" and tempList[2] != "" and tempList[3] == 1):
            clientOwn.publish("/container"+RCDid+"/recieved", "topic=/container"+RCDid+"/lowerBound, msg.payload    ="+str(tempList[0]), qos=0, retain=False)
            clientOwn.publish("/container"+RCDid+"/recieved", "topic=/container"+RCDid+"/upperBound, msg.payload="+str(tempList[1]), qos=0, retain=False)
            clientOwn.publish("/container"+RCDid+"/recieved", "topic=/container"+RCDid+"/setPoint, msg.payload="+str(tempList[2]), qos=0, retain=False)

            bitString, Sair, Rair = ISO10368Lib.containerString(tempList[0], tempList[1], tempContainer)
            tempList[3] = 0

            if(bitString != "" and Sair != "" and Rair != ""):
                clientOwn.publish("/container"+RCDid+"/bitString", bitString, qos=0, retain=False)
                clientOwn.publish("/container"+RCDid+"/Sair", Sair, qos=0, retain=False)
                clientOwn.publish("/container"+RCDid+"/Rair", Rair, qos=0, retain=False)

        else:
            tempList[3] = 0



    clientDTU.loop_start()
    clientOwn.loop_start()
    ourCounter += 1
    time.sleep(1)
