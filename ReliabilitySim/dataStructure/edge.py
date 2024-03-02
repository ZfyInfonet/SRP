import Paras


class Edge:
    def __init__(self, nodeId1, nodeId2, bandwidth, re_lambda, prop_delay):
        self.BW = bandwidth
        self.sharedBW = (Paras.edge_shared_ratio-1) * bandwidth
        self.bwUsed = 0
        self.sharedBwUsed = 0
        self.reLambda = re_lambda
        self.ends = (nodeId1, nodeId2)
        self.propDelay = prop_delay
        self.isValid = True
        self.R = 0.99
        self.linkList = []

    def AddLink(self, link):
        self.bwUsed += link.bwReq
        self.linkList.append(link)

    def DelLink(self, link):
        if link in self.linkList:
            self.bwUsed -= link.bwReq
            self.linkList.remove(link)
            link.ClearLinkinEdge()