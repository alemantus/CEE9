import datetime

now = datetime.datetime.now()


test = "hej"
print(test)
def ISOstring(temp):
    tempISOdouble = (125 + temp)/0.05
    tempISO = round(tempISOdouble)
    return bin(tempISO).replace('0b', '').zfill(8)


def containerString(MstartCool, AstartCool, tempContainer, StartPeakshaving, Testcounter):
    #Bestemmer hvornår containeren skal køle til -30 grader.     
    #if (now.hour >= int(MstartCool) and now.hour <= int(MstartCool) + 1):
    #    Startcool = 1
    #elif (now.hour >= int(AstartCool) and now.hour <= int(AstartCool) + 1):
    #    Startcool = 1
    #else:
     #   Startcool = 0

    #Samme formål som overstående bare til demoen. Dette betyder timer = sekunder
    if (Testcounter >= int(MstartCool) and Testcounter <= int(MstartCool) + 1):
        Startcool = 1
    elif (Testcounter >= int(AstartCool) and Testcounter <= int(AstartCool) + 1):
        Startcool = 1
    else:
        Startcool = 0    

    print("Klokken er:" + " " + str(Testcounter)) 

    if(StartPeakshaving == 1):
        tempDesired = -20
        Sair = -25
        Rair = -25
        tempISO = ISOstring(tempDesired)
        SairISO = "0" + ISOstring(Sair)
        RairISO = "0" + ISOstring(Rair)
        # LED skal lyse i stedet for printout 
        test1 = "Peak-shaving i gang - Containeren slukkes"
        print(test1)
    elif (tempContainer <= -30):
        tempDesired = -30
        Sair = -30
        Rair = -30
        tempISO = "0" + ISOstring(tempDesired)
        SairISO = "0" + ISOstring(Sair)
        RairISO = "0" + ISOstring(Rair)
        # LED skal lyse i stedet for printout 
        test2 = "Containertemeraturen holdes på -30 grader"
        print(test2)
    elif (Startcool == 1):
        tempDesired = -30
        Sair = 75
        Rair = 75
        tempISO = "0" + ISOstring(tempDesired)
        SairISO = ISOstring(Sair)
        RairISO = ISOstring(Rair)
        # LED skal lyse i stedet for printout 
        test3 = "Containerens setpoint ændres til -30 grader (Nedkølingstid 1 time)"
        print(test3)
    else :
        tempDesired = -20
        Sair = -25
        Rair = -25
        tempISO = ISOstring(tempDesired)
        SairISO = "0" + ISOstring(Sair)
        RairISO = "0" + ISOstring(Rair)
        # LED skal lyse i stedet for printout 
        test4 = "Containeren holdes på -18 grader (Normal tilstand)"
        print(test4)   
        

    # Alarm string, 100 angiver standard alarm
    alarm = "100"
    # Recent defrost R
    R = "0"
    # Mode, idk what it is
    Mode = "1111"
    # Alarm flags, 20 bits der er alle er 0 hvis intet er galt
    flags = "00000000000000000000"
    # Den smalede string der sendes til containeren
    bitString = tempISO + SairISO + RairISO + Mode + alarm + flags   

    return bitString
