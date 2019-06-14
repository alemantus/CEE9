import sys
import time
import rpiPythonLib
import paho.mqtt.client as mqtt

#startTime = int(sys.argv[1])
#stopTime = int(sys.argv[2])
RCDid = sys.argv[1]

lowerBound = ""
upperBound = ""
setPoint = ""


tempContainer = -30

print(rpiPythonLib.containerString(2, 12, tempContainer))
#Gets 3 variables from library function return 
#bitString, Sair, Rair = rpiPythonLib.containerString(startTime, stopTime, tempContainer)

#print(Rair)

while(1):

    #mqtt initialize
    def on_connect(client, userdata, flags, rc):
        print("Connected with result code "+str(rc))

        # Subscribing in on_connect() means that if we lose the connection and
        # reconnect then subscriptions will be renewed.

        client.subscribe("/container"+RCDid+"/lowerBound")
        client.subscribe("/container"+RCDid+"/upperBound")
        client.subscribe("/container"+RCDid+"/setPoint")
        client.subscribe("/container1/setPoint")

    # The callback for when a PUBLISH message is received from the server.
    def on_message(client, userdata, msg):
        print(msg.topic)

        if(str(msg.topic) == "/container"+RCDid+"/lowerBound"):
            lowerBound = msg.payload
        elif(str(msg.topic) == "/container"+RCDid+"/upperBound"):
            upperBound = msg.payload
        elif(str(msg.topic) == "/container1/setPoint"):
            setPoint = msg.payload
            print("test1")
        
        bitString, Sair, Rair = rpiPythonLib.containerString(lowerBound, upperBound, tempContainer)
        #print("test1")
        print(setPoint)
    def on_publish(client,userdata,result):             #create function for callback
        print("data published \n")
        pass

    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    client.username_pw_set(username="jfccfsnl",password="a95j7N6GPemj")

    client.connect("m24.cloudmqtt.com", 10832, 60)

    client.publish("data", "test", qos=0, retain=False)

    
    # Blocking call that processes network traffic, dispatches callbacks and
    # handles reconnecting.
    # Other loop*() functions are available that give a threaded interface and a
    # manual interface.
    client.loop_forever()
    time.sleep(1)
