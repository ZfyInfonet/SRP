class Request:
    def __init__(self, req_id, nodeId, ms_list, ms_link_list, backup_limit, lifetime, topo):
        self.reqId = req_id
        self.arriveNodeId = nodeId
        self.MsList = ms_list  # ms_list = [ms1InsList, ms2InsList ...]
        self.MsLinkList = ms_link_list
        self.backupLimit = backup_limit
        self.backupNum = 0
        self.lifetime = lifetime
        self.topo = topo
        self.isPlaced = False
        self.arriveTime = 0
        self.isValid = True

    def CancelMicroservicePlacement(self, g, m):
        if m.nodeId is not None:
            node = g.nodeList[m.nodeId]
            node.DelMs(m)

        for msLink in self.MsLinkList:
            if (m.msId, m.instId) in msLink.msLink and msLink.linkPaths is not None:
                for path in msLink.linkPaths:
                    for edge in g.GetEdgeFromPathNodes(path):
                        edge.DelLink(msLink)
                msLink.linkPaths = None

    def DeleteBackupMs(self, m):
        if m.instId > 1:
            for par in m.Parents:
                if m in par.Sons:
                    par.Sons.remove(m)
            for son in m.Sons:
                if m in son.Parents:
                    son.Parents.remove(m)
            if m in self.MsList[m.msId]:
                self.MsList[m.msId].remove(m)
            for link in self.MsLinkList:
                if (m.msId, m.instId) in link.msLink:
                    self.MsLinkList.remove(link)

