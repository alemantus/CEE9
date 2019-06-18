import datetime

now = datetime.datetime.now()


test = "hej"
def ISOstring(temp):
    tempISOdouble = (125 + temp)/0.05
    tempISO = round(tempISOdouble)
    return bin(tempISO).replace('0b', '').zfill(8)


def containerString(startTime, stopTime, tempContainer):

    if (now.hour > int(startTime) or now.hour < int(stopTime)):
        peak = 1
    else:
        peak = 0

    if(tempContainer >= -20 or peak == 1):
        tempDesired = -20
        Sair = -25
        Rair = -25
        tempISO = ISOstring(tempDesired)
        SairISO = "0" + ISOstring(Sair)
        RairISO = "0" + ISOstring(Rair)
    elif (tempContainer <= -29):
        tempDesired = -30
        Sair = -30
        Rair = -30
        tempISO = "0" + ISOstring(tempDesired)
        SairISO = "0" + ISOstring(Sair)
        RairISO = "0" + ISOstring(Rair)
    else:
        tempDesired = -30
        Sair = -75
        Rair = -75
        tempISO = "0" + ISOstring(tempDesired)
        SairISO = ISOstring(Sair)
        RairISO = ISOstring(Rair)

    # Alarm string, 100 angiver standard alarm
    alarm = "100"
    # Recent defrost R
    R = "0"
    # Mode, idk what it is
    Mode = "1111"
    # Alarm flags, 20 bits der er alle er 0 hvis intet er galt
    flags = "00000000000000000000"
    # Den smalede string der sendes til containeren
    bitString = flags + alarm + Mode + RairISO + SairISO + tempISO

    return bitString, Sair, Rair
