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
ControlManual = [0] * 48

Switch = 1
preHour = 0
preSek = 0
dag = 1
peakM = [False] * 48
peakA = [False] * 48

tempList = [lowerBound,upperBound,setPoint,kickControl]
Deif = [0.0,0.0,0.0,0.0,0.0,0.0,0.0]
tempContainer = -23

Effekttime = [0] * 60
Effektdag = [0] * 24
Effekt1dag = [0] * 48
Effektuge = [0] * 5
Effekttotal = 0
Startcool = 0
# Værdierne om peak tidspunkter er aflæst fra grafen for de første to dage
MpeakStart = [0, 0, 0, 0, 0, 0, 0, 0, 0]
MpeakEnd = [0, 0, 0, 0, 0, 0, 0, 0, 0]
ApeakStart = [0, 0, 0, 0, 0, 0, 0, 0, 0]
ApeakEnd = [0, 0, 0, 0, 0, 0, 0, 0, 0]
StartPeakshaving = 0
Testcounter = 0
KlokkeHour = 0
KlokkenMin = 0 
Klokken = "00:00"

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
    ISOstring = ""
    Sair = ""
    Rair = ""
    global tempList
    global ourCounter
    global Effekttime 
    global Effektdag

    while((tempList[3] == 1 or ourCounter >= 1) and (dag != 4 or Testcounter != 47)):
    #SLÅET FRA UNDER DEMOEN   
        # Sætter tærsklen for hvornår der er peak-strømforbrug middag/aften 
        #Thresh = 35000   
          
      
        # Sætter effektmålinger ind for hvertminut 
        #Effekttime[now.minute] = Effekttotal
        
        # Gemmer hvilken time programmet startes i
        #if(Switch == 1):
        #    preHour = now.hour
        #    preSek = now.second 
        #    Switch = 0

        # Summer de 60 effektmålinger på en time og gemmer resultatet i en liste med elementnummer = den pågældende time.   
        #if(now.hour != preHour):
        #    Sumeffekttime = sum(i for i in  Effekttime)
        #    Effektdag[preHour] =  Sumeffekttime
        #    preHour = now.hour 

        # Sætter tidspunktet for hvornår containeren skal køle til -30 grader.
        # Dette skal ske 1 time før peak-hour for den foregående dag. 
        # Dag 1 og 2 er fastsat fra grafen og ikke fra forrige dag. 
        #if (dag == 1):
        #    MstartCool = MpeakStart[1] - 1
        #    AstartCool = ApeakStart[1] - 1 
        #elif (dag == 2):
        #    MstartCool = MpeakStart[2] - 1
        #    AstartCool = ApeakStart[2] - 1
        #else : 
        #    MstartCool = MpeakStart[dag-1] - 1
        #    AstartCool = ApeakStart[dag-1] - 1 


        # Betsemmer hvornår peak-shavingen skal begynde når containeren har nået -30 grader.  
        # Det skal den når effektmålingen er over middags/aften tærsklen og det respektive tidsrum er nået
        # Skal være slået fra under eksamendemo.  

        #if (Effekttotal > Middagthresh and (now.hour > MstartCool + 1) and (now.hour < MstartCool + 5)):
        #    StartPeakshaving = 1    
        #elif (Effekttotal > Aftenthresh and (now.hour > AstartCool + 1) and (now.hour < AstartCool + 5)):
        #    StartPeakshaving = 1
        #else :
        #    StartPeakshaving = 0 

        
        #print("Startpeakshaving er: " + str(StartPeakshaving))
        # Meget simpel umulator af temeraturen i containeren 
        #if (StartPeakshaving == 1):
            #tempContainer = -30 
        # else :
           # tempContainer = -20 


        #Opdaterer dagen når klokken slår 00. (Slået fra til DEMO)
            #if (now.hour == 00):
             #   dag = dag + 1

        # Threshhold sættes lavere under demo, da dataen er gennemsnittet for hver halve time og derfor lavere end den instentane værdi der skal bruges under normale omstændigheder
        if (dag == 1):  
            Thresh = 20000 
        else :
            Thresh = 25000 
        # Data over samlet effekt fra food court området i 5 dage. Sidste dag giver ikke menning at medbring i demoen
        Effektuge[1] = [15957.9414598682, 16551.9469384916, 15837.1665167312, 14725.3992198526, 15499.1849490379, 14826.9900451914, 13949.6053545898, 12439.7776843687, 12476.1620231613, 12320.6955092630, 12325.5025497277, 11984.7765089835, 10613.8774042540, 10708.7121913310, 10466.8177106758, 10957.9765883589, 12199.1161029792, 10352.3075582258, 10710.8387949313, 10532.2981351476, 11264.4150522048, 11745.5591053608, 11760.4677478604, 12203.5552771401, 13972.9050309513, 13816.3812282996, 13701.1414554949, 14086.2210766108, 14259.0836050268, 18664.2661746762, 21412.0793827903, 20030.5592067492, 19928.2274051965, 20565.9741411396, 23710.9167370531, 29239.8562493068, 32581.2150265356, 32129.3290124454, 34588.6111289670, 36569.4181409228, 34674.6099166397, 32875.5234316529, 36619.3487217986, 37254.9632699701, 36934.4823097841, 40801.2260674309, 39068.9629269541, 38359.2800742571]
        Effektuge[2] = [40883.1549256502, 34926.1092266451, 32652.2104178380, 34725.9603986798, 31916.2169099419, 34165.9520994172, 28543.7901345950, 27058.7815917353, 23287.1631244390, 20382.2442156263, 18722.8543276501, 15940.5096153589, 14457.4175687898, 14696.3893892053, 14229.8584053251, 14941.1481322097, 14410.0985544305, 15215.6086281829, 14361.5546534399, 23593.0698753193, 25991.4618304195, 21056.1958236966, 24930.5246745491, 28066.7778112654, 24313.6877668256, 30825.8577328160, 30042.3142242352, 32045.7764200820, 30214.1313349505, 31295.5316712099, 33472.7266582842, 33714.3897307986, 35746.1357116593, 31828.7193461299, 33705.7821776504, 36300.4151158270, 39989.9643030001, 35824.0491944571, 35658.4337236105, 35336.9423730502, 36966.3612178773, 39256.7214228165, 35644.5860136316, 35223.9127977658, 39488.2655223555, 38835.0250286294, 40632.2026518334, 39902.1058955889]
        Effektuge[3] = [34567.9452279732, 33959.5703916263, 37280.7912909827, 36753.3242778216, 39191.1468746248, 38432.8687550813, 37488.4620615768, 32289.1439913789, 29722.1595659544, 29559.9488886643, 30381.5560330421, 24282.6296695535, 21122.8513791512, 18299.6905907334, 16748.1088451557, 18023.1446046772, 18216.7341270932, 17811.0452594302, 16521.6173287893, 16595.9697485911, 18177.6535263383, 20761.0281956319, 21447.2467413043, 28743.2617496489, 28288.5810352841, 31797.8092896929, 36084.3708890523, 37025.8343098427, 35358.7090593031, 37763.5368506602, 40423.3380362960, 37560.8750809657, 41060.8211353878, 40665.6511306532, 38723.8427859322, 39966.4715787731, 39403.8003882837, 38247.9241898024, 40053.8009027995, 40058.5899549150, 39325.3494648512, 40225.8693097455, 39031.8901335908, 38563.7549781991, 38218.3065677889, 38696.4816555488, 42264.4162032346, 38902.7272739414]
        Effektuge[4] = [34156.2544814755, 34478.2099535587, 35691.9219845122, 33839.6195552409, 37762.4222922978, 35018.3861213351, 33570.6855293027, 30963.1652633058, 26632.3559444194, 26339.3522906687, 25076.0358591298, 21622.8401761776, 18762.2481595139, 17272.9013392509, 17593.2992568729, 16850.6860600504, 14981.5573157428, 15901.1362073327, 15301.2946256622, 14767.7543488182, 18149.2852251640, 19035.7742269835, 21270.5295414498, 31332.0575422640, 28648.1271227574, 32758.2529176593, 35503.6604704469, 35068.4686541599, 36894.9040876432, 36773.5934509923, 35645.3199813374, 37450.9047649841, 36887.6670441952, 37029.6350596149, 38249.3890497414, 32348.9454718042, 34113.9804543252, 25897.7910301541, 26200.3785061765, 19728.6164329633, 15469.8678642047, 25587.2204427361, 25214.1583133982, 23725.4438736655, 22268.2506741094, 20208.7724489241, 21948.0070269671, 21607.1731949822]
        #Effektuge[5] = [21188.8103479027, 20408.3130651595, 21114.8791902413, 20830.5735373466, 18068.1722770662, 19345.5391212902, 18411.6867112721, 18678.2133257825, 15526.2501125599, 13850.2826169496, 14422.9743480783, 12486.9690203671, 10287.1819335954, 8284.84853353177, 8044.85631742606, 8051.46680628223, 7304.26074603584, 8215.99821224526, 7072.29507792491, 6867.50671549156, 6278.45735710600, 6973.41804479758, 7057.01989277929, 6540.51308785099, 7781.85691524205, 5428.01291667100, 5901.28400096378, 6446.03758173533, 6366.00928522692, 6550.13853349553, 6060.97887844978, 5696.77082835988, 5637.08910715305, 7057.48763772973, 6669.05089182506, 6064.87631258938, 5131.77008741822, 4914.73114654610, 4742.54528603785, 4157.57773161271, 5175.06474075119, 4985.91585380085, 4399.42823158692, 3660.63733558561, 3944.23538015427, 7042.71727264348, 5620.84063713769, 4257.68220714976]

    
        #Laver liste på for middag/aften der indeholder peak-strømforbrugstimer i form af true/false for de valgte tidsrum 
        # Dette skal gøres når et nyt døgn starter (If statementet slås fra under test) 
        #if (now.hour == 00):
          
        if (True == True):
            y = 0
            z = 0
            for x in Effektuge[dag]:
                if (x > Thresh) and (y > 18 and y < 32):
                    peakM[y] = True
                else:
                    peakM[y] = False
                y = y + 1

            for x in Effektuge[dag]:
                if (x > Thresh and (z > 36 and z < 44)):
                    peakA[z] = True
                else:
                    peakA[z] = False
                z = z + 1  
             
            #Liste der indeholder time-nummeret for de timer der er peak (peak=true) for middag/aften.
            resM = [i for i, val in enumerate(peakM) if val]
            resA = [i for i, val in enumerate(peakA) if val]

           
            # Lister på 8, der indeholder start og sluttidspunt for middag peaktimer.
            #if (dag != 1): (Slåes fra i DEMOEN)
            #   MpeakStart[dag] = resM[0] 
            #   MpeakEnd[dag] = resM[len(resM) -1]
            #   ApeakStart[dag] = resA[0] 
            #   ApeakEnd[dag] = resA[len(resA) -1]
            
            MpeakStart[dag] = resM[0] 
            MpeakEnd[dag] = resM[len(resM) -1]

            #Lister på 8, der indeholder start og sluttidspunt for aften peaktimer 
            # Første dag kan godt bruges her 
            ApeakStart[dag] = resA[0] 
            ApeakEnd[dag] = resA[len(resA) -1]

        # Sætter starttidspunktet til en time før peak-hour for den pågældende dag     
        MstartCool = MpeakStart[dag] - 1
        AstartCool = ApeakStart[dag] - 1

        
# KODE TIL EKSAMENS DEMONSTRAION 
        # Counter der tæller fra 0 til 47, svarende til antallet af halve timer i et døgn 
        if (preSek != now.second and Testcounter < 47):
            Testcounter = Testcounter + 1
            preSek = now.second 
        elif (Testcounter == 47):
            Testcounter = 0 
            print("Det er nu dag " + str(dag))
           
        if (dag == 1 and Testcounter == 0):
            print("Det er nu dag " + str(dag))


        # Laver DEMO-klokken, der springer i halve timers intervaller 
        if (Testcounter % 2 == 0):
            KlokkeHour = int(Testcounter / 2)
            KlokkenMin = 0
        else :
            KlokkeHour = int(Testcounter / 2)     
            KlokkenMin = 30
                
        # Laver strengen med klokken på rigtig format 
        if (KlokkeHour < 10):    
            Klokken = "0" + str(KlokkeHour) + ":" + str(KlokkenMin)
        else :
            Klokken = str(KlokkeHour) + ":" + str(KlokkenMin)

        if (KlokkenMin == 0):
            Klokken = Klokken+"0"      

        Klokken = "Klokken er:" + " " + Klokken     

        if (Testcounter == 47 and dag < 4):
            dag = dag + 1
        
        print(Klokken)
     

        # Gemmer hvilke tidspunkter på døgnet som algortimen har været slået fra, så den ikke slår fra hvis den ikke hær været nedkølet til -30 
        ControlManual[Testcounter] = manual       


        # StartPeakshave variablen starter peak shaving når -30 grader er nået og effekten er over middag/aften threshhold
        # Gør også så containeren maks kan være slukket 3 timer ad gangen.
        # Effektuge[dag][MstartCool] > Thresh og  Effektuge[dag][AstartCool] > Thresh indsættes i if og elif respektivt, når demoen ikke kører
        if ((Testcounter >= MstartCool + 3) and (Testcounter < MstartCool + 7)):
            StartPeakshaving = 1   
        elif ((Testcounter >= AstartCool + 3) and (Testcounter < AstartCool + 7)):
            StartPeakshaving = 1
        else :
            StartPeakshaving = 0  

        if (ControlManual[AstartCool] == 1 or ControlManual[AstartCool + 1] == 1 or ControlManual[AstartCool + 2] == 1 or ControlManual[AstartCool + 3] == 1):
            StartPeakshaving = 0    
        elif (ControlManual[MstartCool] == 1 or ControlManual[MstartCool + 1] == 1 or ControlManual[MstartCool + 2] == 1 or ControlManual[MstartCool + 3] == 1):
            StartPeakshaving = 0

        if (Testcounter > int(MstartCool) -1 and Testcounter <= int(MstartCool) + 2):
            Startcool = 1
        elif (Testcounter > int(AstartCool) -1 and Testcounter <= int(AstartCool) + 2):
            Startcool = 1
        else:
            Startcool = 0        

         
        #Sender informationerne til ISOstring hvor tilstandsændringer sker 
        
        ISOstring = ISO10368Lib.containerString(Startcool, tempContainer, StartPeakshaving, Testcounter, manual, ControlManual)
        #else:

        if (Testcounter == 47 and dag == 4):
            print("Demoen er slut")

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
