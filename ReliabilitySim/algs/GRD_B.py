import copy
from dataStructure.ms import Microservice
from dataStructure.msLink import MicroserviceLink
from dataStructure.request import Request
from dataStructure.node import Node
from dataStructure.graph import Graph
import networkx as nx
import Tools

maxNum = 3


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

        # Placement Begin
        result = Placement(G, req, m)
        if not result:
            break
        #
        # print(f'Req {req.reqId}: m{m.msId}({m.instId}) has been placed to Node {m.nodeId}')
    BackupAndPlace(G, req)
    if result:
        return True
    else:
        Tools.ClearRequestFromGraph(G, req)
        return False


def Placement(G: Graph, req: Request, m: Microservice):
    candNodes = []
    for node in G.nodeList:
        if node.cpuUsed + m.cpuReq <= node.CPU:
            candNodes.append(node)

    if len(candNodes) == 0:
        return False
    result = True
    n_max = None
    n_max_R = 0
    for n in candNodes:
        if n.R > n_max_R:
            n_max = n
            n_max_R = n.R
    n_max.AddMs(m)
    for parent in m.Parents:
        link = Tools.FindLink(req, parent, m)
        if parent.nodeId is None:
            continue
        if parent.nodeId == n_max.nodeId:
            link.linkPaths = []
        else:
            paths = G.FindDisjointPaths(n_max.nodeId, parent.nodeId, maxNum)
            pathLength = [len(p) for p in paths]
            # print(n_max.nodeId, parent.nodeId, pathLength)
            # print(f'src: {n_max.nodeId} , dst: {parent.nodeId}', paths)
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
                if m.instId == 1:
                    result = False
                    break
                else:
                    req.CancelMicroservicePlacement(G, req, m)
                    req.DeleteBackupMs(m)
                    break
    if m.instId > 1:
        for son in m.Sons:
            link = Tools.FindLink(req, m, son)

            if son.nodeId is None or link is None:
                continue
            if son.nodeId == n_max.nodeId:
                link.linkPaths = []
            else:
                paths = G.FindDisjointPaths(n_max.nodeId, son.nodeId, maxNum)
                pathLength = [len(p) for p in paths]
                # print(n_max.nodeId, parent.nodeId, pathLength)
                # print(f'src: {n_max.nodeId} , dst: {parent.nodeId}', paths)
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
                    req.CancelMicroservicePlacement(G, req, m)
                    req.DeleteBackupMs(m)
                    break
    if not result:
        return False
    return True


def BackupAndPlace(G: Graph, req: Request):
    for i in range(req.backupLimit):
        m_origin = req.MsList[i+1][0]
        m_new = Microservice(
            req.reqId,
            i+1,
            len(req.MsList[i+1]) + 1,
            m_origin.cpuReq,
            m_origin.reLambda,
            m_origin.gamma,
            m_origin.procDelay
        )
        for parent in m_origin.Parents:
            # print(f' m_origin: m{m_origin.msId}({m_origin.instId})')
            # print(f' m_origins parent: m{parent.msId}({parent.instId})')
            m_new.Parents.append(parent)
            parent.Sons.append(m_new)
            originLink = Tools.FindLink(req, req.MsList[parent.msId][0], m_origin)

            newLink = MicroserviceLink(
                req.reqId,
                ((parent.msId, parent.instId), (m_new.msId, m_new.instId)),
                originLink.bwReq,
                originLink.reLambda,
                originLink.ddl
            )
            # print(f' 添加了新parent link! {newLink.msLink}')
            req.MsLinkList.append(newLink)
        for son in m_origin.Sons:
            # print(f' m_origin: m{m_origin.msId}({m_origin.instId})')
            # print(f' m_origins son: m{son.msId}({son.instId})')
            m_new.Sons.append(son)
            son.Parents.append(m_new)
            originLink = Tools.FindLink(req, m_origin, req.MsList[son.msId][0])

            newLink = MicroserviceLink(
                req.reqId,
                ((m_new.msId, m_new.instId), (son.msId, son.instId)),
                originLink.bwReq,
                originLink.reLambda,
                originLink.ddl
            )
            req.MsLinkList.append(newLink)
            # print(f' 添加了新son link！ {newLink.msLink}')\
        req.MsList[i+1].append(m_new)
        BackupResult = Placement(G, req, m_new)
        if not BackupResult:
            req.CancelMicroservicePlacement(G, req, m_new)
            req.DeleteBackupMs(m_new)


def printName():
    print('----------This is GRD-B----------')
