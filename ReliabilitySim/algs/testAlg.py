from dataStructure.ms import Microservice
from dataStructure.msLink import MicroserviceLink
from dataStructure.request import Request
from dataStructure.node import Node
from dataStructure.edge import Edge
from dataStructure.graph import Graph
import networkx as nx
import matplotlib.pyplot as plt
import Tools


def run(G: Graph, req: Request):
    print(f'Req {req.reqId} arrived at Node {req.arriveNodeId} with {len(req.MsList) - 1} Microservices')
    Q = Tools.GetMicroserviceQueue(req)
    for mList in Q:
        m = mList[0]
        if m.msId == 0:
            continue
        while m.nodeId is None:
            ResidualCpuMaxNode = None
            ResidualCpuMax = 0
            for n in G.nodeList:
                if n.flag is False or n.cpuUsed + m.cpuReq > n.CPU:
                    continue
                ResidualCpu = n.CPU - n.cpuUsed
                if ResidualCpu > ResidualCpuMax:
                    ResidualCpuMax = ResidualCpu
                    ResidualCpuMaxNode = n
            if ResidualCpuMaxNode is None:
                return False
            ResidualCpuMaxNode.AddMs(m)
            isAllLinkPlaced = True
            for parent in m.Parents:
                msLink = Tools.FindLink(req, parent, m)
                if parent.nodeId == ResidualCpuMaxNode.nodeId:
                    continue
                paths = Tools.FindAvailableLinkPaths(msLink, G, req)
                if len(paths) == 0:  # note
                    isAllLinkPlaced = False
                    break
                minLenPath = None
                minLen = 999
                for path in paths:
                    if len(path) < minLen:
                        minLenPath = path
                msLink.linkPaths = [minLenPath]
                for path in msLink.linkPaths:
                    edgeList = G.GetEdgeFromPathNodes(path)
                    for edge in edgeList:
                        edge.AddLink(msLink)
            if not isAllLinkPlaced:
                ResidualCpuMaxNode.flag = False
                ResidualCpuMaxNode.DelMs(m)
                continue
            for n in G.nodeList:
                n.flag = True

            print(f'Req {req.reqId}: Ms{m.msId} has been placed to Node {ResidualCpuMaxNode.nodeId}')
            break
    req.isPlaced = True
    # req_g = req.topo
    # nx.draw(req_g, with_labels=True)
    # plt.show()


def printName():
    print('----------This is testAlg----------')
