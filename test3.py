import sys

firstString="2 5 5".split(' ')
userLimit=int(firstString[0])
serviceLimit=int(firstString[1])
duration=int(firstString[2])

usersTimes={}
serviceTimes={'firstTime':[], 'NofReqs':0}

def counter(firstTime=[0,1,2], nowTime=0):
    NofReqs=1 # append NowTime
    retFirstTime=[]
    startTime = nowTime - duration
    endTime = nowTime
    for ev in firstTime:
        if ev >= startTime:
        # if nowTime-ev<=duration:
            retFirstTime.append(ev)
            NofReqs=NofReqs+1
    retFirstTime.append(nowTime)
    return retFirstTime, NofReqs



def aprover(record={}, nowEvent={}, errCode="", limit=0, reqCode=""):
    firstTime, NofReqs = counter(firstTime=record['firstTime'], nowTime=nowEvent['time'])
    if NofReqs<= limit:
        retRec = {'firstTime': firstTime, 'NofReqs':NofReqs}
        code=reqCode
    else: # >= limit
        retRec = {'firstTime': firstTime, 'NofReqs':NofReqs}
        code = errCode
    return retRec, code

while True:
    reqCode = '200'
    inputStr=input()
    if inputStr=='-1':break

    inputStr=inputStr.split(' ')
    time=int(inputStr[0])
    userId=int(inputStr[1])
    nowEvent={'time':time, 'userId': userId}

    if not userId in usersTimes:
        usersTimes[userId]={'firstTime':[time], 'NofReqs':1}
    else:
        user= usersTimes[userId]
        retRec, reqCode= aprover(record=user, nowEvent=nowEvent, errCode="429", limit=userLimit, reqCode=reqCode)
        usersTimes[userId]= retRec


    retRec2, reqCode2 = aprover(record=serviceTimes, nowEvent=nowEvent, errCode="503", limit=serviceLimit, reqCode=reqCode)
    serviceTimes = {'firstTime': retRec2['firstTime'], 'NofReqs': retRec2['NofReqs']}
    if not reqCode=='200':
        print (reqCode)
    elif not reqCode2 == '200':
        print(reqCode2)
    else:
        print('200')
    sys.stdout.flush()


