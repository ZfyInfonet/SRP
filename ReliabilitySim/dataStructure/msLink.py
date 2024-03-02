class MicroserviceLink:
    def __init__(self, req_id, ms_link, bandwidth, re_lambda, ddl):
        self.reqId = req_id
        self.msLink = ms_link           # ((3,1), (4,1)) m_3(1) -> m_4(1)
        self.bwReq = bandwidth
        self.reLambda = re_lambda
        self.isValid = True
        self.ddl = ddl
        self.linkPaths = None            # [paths]
        self.R = 0.99
        self.pathR = 1
        self.BackupR = 0
        self.kappa = self.R
        self.edgeList = []

    def ClearLinkinEdge(self):
        for edge in self.edgeList:
            edge.DelLink(self)