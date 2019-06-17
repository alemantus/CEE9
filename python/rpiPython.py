import sys
import time
#import ISO10368Lib
import libraries
import paho.mqtt.client as mqtt

# define container id when starting program
RCDid = sys.argv[1]

#asdasd
# delcare global variables used in on_message callback
lowerBound = "" 
upperBound = ""
setPoint = ""
connectControl = 0
kickControl = 2

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

    # The callback for when a PUBLISH message is received from the server.
    def on_message(client, userdata, msg):

        #global lowerBound
        #global upperBound
        #global setPoint
        #global kickControl

        global tempList


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

    # connects once
    if (connectControl == 0):
        client = mqtt.Client()
        client.on_connect = on_connect
        client.on_message = on_message

        client.username_pw_set(username="jfccfsnl",password="a95j7N6GPemj")

        client.connect("m24.cloudmqtt.com", 10832, 60)

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
    client.loop_start()
    time.sleep(5)
