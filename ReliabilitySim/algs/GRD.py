import copy
from dataStructure.ms import Microservice
from dataStructure.msLink import MicroserviceLink
from dataStructure.request import Request
from dataStructure.node import Node
from dataStructure.graph import Graph
import networkx as nx
import Tools
import Paras

maxNum = Paras.path_max_num


def run(G: Graph, req: Request):
    # print(f'Req {req.reqId} arrived at Node {req.arriveNodeId} with {len(req.MsList) - 1} Microservices')
    # print(f'BackupLimit: {req.backupLimit}')
    Q = Tools.GetMicroserviceQueue(req)
    result = True
    while req.isPlaced is not True:
        m = None
        for msList in Q:
            if msList[0].nodeId is None:
                m = msList[0]
                break
        if m is None:
            req.isPlaced = True
            break
        candNodes = []
        for node in G.nodeList:
            if node not in m.banedNodes and node.cpuUsed + m.cpuReq <= node.CPU:
                candNodes.append(node)

        if len(candNodes) == 0:
            result = False
            break

        # Placement Begin
        n_max = None
        n_max_R = 0
        for n in candNodes:
            if n.R > n_max_R:
                n_max = n
                n_max_R = n.R
        n_max.AddMs(m)
        for parent in m.Parents:
            if parent.nodeId is None:
                continue
            link = Tools.FindLink(req, parent, m)
            if parent.nodeId == n_max.nodeId:
                link.linkPaths = []
            else:
                paths = G.FindDisjointPaths(n_max.nodeId, parent.nodeId, maxNum)
                pathLength = [len(p) for p in paths]
                # print(f'src: {n.nodeId} , dst: {parent.nodeId}', paths)
                while paths:
                    shortest_idx = pathLength.index(min(pathLength))
                    shortest_path = paths[shortest_idx]
                    if not Tools.CheckLinkConstraints(link, shortest_path, G, req):
                        # print(f' path len: {len(shortest_path) - 1}')
                        pathLength.remove(pathLength[shortest_idx])
                        paths.remove(paths[shortest_idx])
                    else:
                        for edge in G.GetEdgeFromPathNodes(shortest_path):
                            edge.AddLink(link)
                        link.linkPaths = [shortest_path]
                        break
                if not link.linkPaths:
                    result = False
                    req.CancelMicroservicePlacement(G, m)
                    break
        if not result:
            break

        # print(f'Req {req.reqId}: m{m.msId}({m.instId}) has been placed to Node {n_max.nodeId}')

    if result:
        return True
    else:
        Tools.ClearRequestFromGraph(G, req)
        return False


def printName():
    print('----------This is GRD----------')
