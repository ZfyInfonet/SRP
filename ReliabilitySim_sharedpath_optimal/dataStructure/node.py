class Node:
    def __init__(self, node_id, cpu, reliability_low, reliability_high, threshold, is_access, edgeList):
        self.nodeId = node_id
        self.CPU = cpu
        self.cpuUsed = 0
        self.isValid = True
        self.isAccess = is_access
        if reliability_low < reliability_high:
            self.reLow = reliability_low
            self.reHigh = reliability_high
        else:
            self.reLow = reliability_high
            self.reHigh = reliability_low
        self.threshold = threshold
        self.R = self.reHigh
        self.Microservices = []
        self.MicroservicesIdList = []
        self.flag = True
        self.edgeList = edgeList

    def cpuChange(self, value):
        self.cpuUsed += value
        if self.cpuUsed/self.CPU < self.threshold:
            self.R = self.reHigh
        else:
            self.R = self.reLow

    def AddMs(self, microservice):
        if microservice not in self.Microservices:
            if self.CPU - self.cpuUsed < microservice.cpuReq:
                raise Exception("Insufficient CPU resources for Node ", self.nodeId)
            self.cpuChange(microservice.cpuReq)
            self.Microservices.append(microservice)
            microservice.nodeId = self.nodeId
            self.MicroservicesIdList.append([microservice.reqId, microservice.msId, microservice.instId])

    def DelMs(self, microservice):
        if microservice in self.Microservices:
            self.cpuChange(-microservice.cpuReq)
            self.Microservices.remove(microservice)
            self.MicroservicesIdList.remove([microservice.reqId, microservice.msId, microservice.instId])
            microservice.nodeId = None

    def printInfo(self):
        print('---------------------')
        if self.isAccess:
            print(f'Node {self.nodeId}: type: Access Node')
        else:
            print(f'Node {self.nodeId}: type: Node')
        print('---------------------')
        print(f'cpu usage: {self.cpuUsed}/{self.CPU}, working: {self.isValid}, r: {self.R} \n '
              f'rL: {self.reLow}, rH: {self.reHigh}, thr: {self.threshold}\n Microservice List:')

        for ms in self.Microservices:
            print(f'***    req:{ms.reqId}, ms:{ms.msId}, inst: {ms.instId}')
