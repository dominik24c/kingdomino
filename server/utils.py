def listToStr(listOfNumbers):
    tmpList = [str(n) for n in listOfNumbers]
    return " ".join(tmpList)


def getCommandAndArgsForPlayer(msg):
    msgWithoutNewLine = msg.rstrip('\n')
    listOfMsg = msgWithoutNewLine.split(" ")
    utilizedList = list(filter(lambda char: char != "", listOfMsg))

    command = utilizedList[0]
    if len(utilizedList) == 1:
        args = []
    else:
        args = utilizedList[1:]
    return command, args
