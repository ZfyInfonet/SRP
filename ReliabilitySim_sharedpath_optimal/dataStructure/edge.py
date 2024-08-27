import Paras


class Edge:
    def __init__(self, nodeId1, nodeId2, bandwidth, re_lambda, prop_delay):
        self.BW = bandwidth
        self.sharedBW = (Paras.edge_shared_ratio - 1) * bandwidth
        self.bwUsed = 0
        self.sharedBwUsed = 0
        self.reLambda = re_lambda
        self.ends = (nodeId1, nodeId2)
        self.propDelay = prop_delay
        self.isValid = True
        self.R = 0.99
        self.linkList = []
        self.backupLinkList = []

    def AddLink(self, link):
        if self.bwUsed + link.bwReq <= self.BW:
            self.bwUsed += link.bwReq
            self.linkList.append(link)
            if self not in link.edgeList:
                link.edgeList.append(self)

    def AddBackupLink(self, link):
        if link.bwReq + self.sharedBwUsed < self.sharedBW:
            self.sharedBwUsed += link.bwReq
            self.backupLinkList.append(link)
            if self not in link.edgeList:
                link.edgeList.append(self)

    def DelLink(self, link):
        if link in self.linkList:
            self.bwUsed -= link.bwReq
            self.linkList.remove(link)
            link.ClearLinkinEdge()
        if link in self.backupLinkList:
            self.sharedBwUsed -= link.bwReq
            self.backupLinkList.remove(link)
            link.ClearLinkinEdge()
