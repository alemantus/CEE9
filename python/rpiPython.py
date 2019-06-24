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
import datetime

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
StartTime = 0
# Når manual = 0 så kører algoritmen
manual = 0
ControlManual = [0] * 24

Switch = 1
preHour = 0
preSek = 0
dag = 2
peakM = [False] * 24
peakA = [False] * 24

tempList = [lowerBound,upperBound,setPoint,kickControl]
Deif = [0.0,0.0,0.0,0.0,0.0,0.0,0.0]
tempContainer = -23

Effekttime = [0] * 60
Effektdag = [0] * 24
# Værdierne om peak tidspunkter er aflæst fra grafen for de første to dage
MpeakStart = [0, 15, 13, 0, 0, 0, 0, 0, 0]
MpeakEnd = [0, 1, 2, 0, 0, 0, 0, 0, 0]
ApeakStart = [0, 20, 20, 0, 0, 0, 0, 0, 0]
ApeakEnd = [0, 22, 0, 0, 0, 0, 0, 0, 0]
StartPeakshaving = 0
Testcounter = 0

while(1):
    now = datetime.datetime.now()

    ### Callbacks for DTU broker ###
    def on_connectDTU(client, userdata, flags, rc):
        print("Connected to DTU broker")
        clientOwn.publish("/container"+RCDid+"/on_connectOwn", "Connected to Own", qos=0, retain=False)

        clientDTU.subscribe("EVBE/#")

    def on_messageDTU(client, userdata, msg):
        global tempList
        global currentBroker
        global Deif
        global Effekttotal

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
                #print(Effekttotal)
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

        clientOwn.subscribe("/container"+RCDid+"/setPoint")
        clientOwn.subscribe("/container"+RCDid+"/kick")
        clientOwn.subscribe("/container"+RCDid+"/manual")

    def on_messageOwn(client, userdata, msg):
        global kickControl
        global manual

        if(str(msg.topic) == "/container"+RCDid+"/setPoint"):
            tempList[2] = int(msg.payload)
            tempList[3] = 0
        elif(str(msg.topic) == "/container"+RCDid+"/kick"):
            tempList[3] = 1
        elif(str(msg.topic) == "/container"+RCDid+"/manual"):
            manual = int(msg.payload)
            print("asd")
            print(int(msg.payload))


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
    global Effekttime 
    global Effektdag


    while(tempList[3] == 1 or ourCounter >= 5):
        # Sætter tærsklen for hvornår der er peak-strømforbrug middag/aften 
        Middagthresh = 35000
        Aftenthresh = 42000
        # Sætter effektmålinger ind for hvertminut 
        Effekttime[now.minute] = Effekttotal
        # Test vektor: Starter kl 00. d. 5/7 - slutter kl. 23 d 5/7
        Effektdag = [30000, 40000, 15000, 75000, 4000, 4000, 4000, 4000, 5000, 25000, 25000, 27000, 36000, 40000, 40000, 44000, 40000, 44000, 44000, 40000, 43000, 47000, 45000, 45000]
        
        # Gemmer hvilken time programmet startes i
        if(Switch == 1):
            preHour = now.hour
            preSek = now.second 
            Switch = 0

        # Summer de 60 effektmålinger på en time og gemmer resultatet i en liste med elementnummer = den pågældende time.   
        if(now.hour != preHour):
            Sumeffekttime = sum(i for i in  Effekttime)
            Effektdag[preHour] =  Sumeffekttime
            preHour = now.hour 
               

        #Laver liste på for middag/aften der indeholder peak-strømforbrugstimer i form af true/false for de valgte tidsrum 
        # Dette skal gøres når et nyt døgn starter (If statementet slås fra under test) 
        #if (now.hour == 00):
        if(True == True):
            y = 0
            z = 0
            for x in Effektdag:
                if (x > Middagthresh and (y > 11 and y < 15)):
                    peakM[y] = True
                else:
                    peakM[y] = False
                y = y + 1

            for x in Effektdag:
                if (x > Aftenthresh and (z > 19 and z < 24)):
                    peakA[z] = True
                else:
                    peakA[z] = False
                z = z + 1  

            #Liste der indeholder time-nummeret for de timer der er peak (peak=true) for middag/aften.
            resM = [i for i, val in enumerate(peakM) if val]
            resA = [i for i, val in enumerate(peakA) if val]


            # Lister på 8, der indeholder start og sluttidspunt for middag peaktimer.
            # Førte dag er ikke brugbar  
            if (dag != 1):
                MpeakStart[dag] = resM[0] 
                MpeakEnd[dag] = resM[len(resM) -1]

            #Lister på 8, der indeholder start og sluttidspunt for aften peaktimer 
            # Første dag kan godt bruges her 
            ApeakStart[dag] = resA[0] 
            ApeakEnd[dag] = resA[len(resA) -1]
            

            #Opdaterer dagen når klokken slår 00. 
            if (now.hour == 00):
                dag = dag + 1

        # Sætter tidspunktet for hvornår containeren skal køle til -30 grader.
        # Dette skal ske 1 time før peak-hour for den foregående dag. 
        # Dag 1 og 2 er fastsat fra grafen og ikke fra forrige dag. 
        if (dag == 1):
            MstartCool = MpeakStart[1] - 1
            AstartCool = ApeakStart[1] - 1 
        elif (dag == 2):
            MstartCool = MpeakStart[2] - 1
            AstartCool = ApeakStart[2] - 1
        else : 
            MstartCool = MpeakStart[dag-1] - 1
            AstartCool = ApeakStart[dag-1] - 1 


        # Betsemmer hvornår peak-shavingen skal begynde når containeren har nået -30 grader.  
        # Det skal den når effektmålingen er over middags/aften tærsklen og det respektive tidsrum er nået
        # Skal være slået fra under eksamendemo.  

        #if (Effekttotal > Middagthresh and (now.hour > MstartCool + 1) and (now.hour < MstartCool + 5)):
        #    StartPeakshaving = 1    
        #elif (Effekttotal > Aftenthresh and (now.hour > AstartCool + 1) and (now.hour < AstartCool + 5)):
        #    StartPeakshaving = 1
        #else :
        #    StartPeakshaving = 0      

        
# KODE TIL EKSAMENS DEMONSTRAION 
        # Counter der skal lave timer til sekunder 
        if (preSek != now.second and Testcounter < 23):
            Testcounter = Testcounter + 1
            preSek = now.second 
        elif (Testcounter == 23):
            Testcounter = 0    
        
        # Gemmer hvilke tidspunkter på døgnet som algortimen har været slået fra 
        ControlManual[Testcounter] = manual       


        # StartPeakshave variablen starter peak shaving når -30 grader er nået og effekten er over middag/aften threshhold
        # Gør også så containeren maks kan være slukket 3 timer ad gangen. 
        if (Effektdag[Testcounter] > Middagthresh and (Testcounter >= MstartCool + 1) and (Testcounter < MstartCool + 4)):
            StartPeakshaving = 1   
        elif (Effektdag[Testcounter] > Aftenthresh and (Testcounter >= AstartCool + 1) and (Testcounter < AstartCool + 4)):
            StartPeakshaving = 1
        else :
            StartPeakshaving = 0  

        if (ControlManual[AstartCool] == 1 or ControlManual[AstartCool + 1] == 1 or ControlManual[AstartCool + 2] == 1 or ControlManual[AstartCool + 3] == 1):
            StartPeakshaving = 0    
        elif (ControlManual[MstartCool] == 1 or ControlManual[MstartCool + 1] == 1 or ControlManual[MstartCool + 2] == 1 or ControlManual[MstartCool + 3] == 1):
            StartPeakshaving = 0    

        # Meget simpel umulator af temeraturen i containeren 
        #if (StartPeakshaving == 1):
            #tempContainer = -30 
       # else :
           # tempContainer = -20         

        
        

        
        #Sender informationerne til ISOstring hvor tilstandsændringer sker 
        
        ISOstring = ISO10368Lib.containerString(MstartCool, AstartCool, tempContainer, StartPeakshaving, Testcounter, manual, ControlManual)
        #else:



        ourCounter = 0

        #bme76 = bme280.Bme280(i2c_bus=1,sensor_address=0x76)
        #bme76.set_mode(bme280.MODE_FORCED)
        #t1, p1, h1 = bme76.get_data()

        #bme77 = bme280.Bme280(i2c_bus=1,sensor_address=0x77)
        #bme77.set_mode(bme280.MODE_FORCED)
        #t2, p2, h2 = bme77.get_data()
        #print(round(t1,2))
        #clientOwn.publish("/container"+RCDid+"/tempInside", round(t1,2), qos=0, retain=False)
        #clientOwn.publish("/container"+RCDid+"/tempOutside", round(t2,2), qos=0, retain=False)

        
        clientOwn.publish("/container"+RCDid+"/effektTotal", Effekttotal, qos=0, retain=False)
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
