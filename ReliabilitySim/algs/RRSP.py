import copy
from dataStructure.ms import Microservice
from dataStructure.msLink import MicroserviceLink
from dataStructure.request import Request
from dataStructure.node import Node
from dataStructure.graph import Graph
import networkx as nx
import Tools
import Paras

T = 500
maxNum = Paras.path_max_num


def run(G: Graph, req: Request):
    # print(f'Req {req.reqId} arrived at Node {req.arriveNodeId} with {len(req.MsList) - 1} Microservices')
    # print(f'BackupLimit: {req.backupLimit}')
    BackupMsDegreeOrder = []
    for msList in req.MsList:
        if msList[0].msId == 0:
            continue
        ms = msList[0]
        degree = len(ms.Parents) + len(ms.Sons)
        BackupMsDegreeOrder.append((ms.msId, degree))

    BackupMsDegreeOrder = sorted(BackupMsDegreeOrder, key=lambda x: x[1], reverse=True)
    for i in range(req.backupLimit):

        mId = BackupMsDegreeOrder[0][0]
        backMsList = req.MsList[mId]
        m_origin = backMsList[0]
        m_new = Microservice(
            req.reqId,
            mId,
            len(backMsList) + 1,
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
            originLink = Tools.FindLink(req, req.MsList[parent.msId][0], req.MsList[mId][0])

            newLink = MicroserviceLink(
                req.reqId,
                ((parent.msId, parent.instId), (m_new.msId, m_new.instId)),
                originLink.bwReq,
                originLink.reLambda,
                originLink.ddl
            )
            req.MsLinkList.append(newLink)
        for son in m_origin.Sons:
            # print(f' m_origin: m{m_origin.msId}({m_origin.instId})')
            # print(f' m_origins son: m{son.msId}({son.instId})')
            m_new.Sons.append(son)
            son.Parents.append(m_new)
            originLink = Tools.FindLink(req, req.MsList[mId][0], req.MsList[son.msId][0])

            newLink = MicroserviceLink(
                req.reqId,
                ((m_new.msId, m_new.instId), (son.msId, son.instId)),
                originLink.bwReq,
                originLink.reLambda,
                originLink.ddl
            )
            req.MsLinkList.append(newLink)
        req.MsList[mId].append(m_new)
        BackupMsDegreeOrder.remove(BackupMsDegreeOrder[0])

    CandNodes = []
    minReq = 999
    for msList in req.MsList:
        for ms in msList:
            if ms.cpuReq < minReq:
                minReq = ms.cpuReq
    for n in G.nodeList:
        if n.cpuUsed + minReq <= n.CPU:
            CandNodes.append(n)
    CandNodes = sorted(CandNodes, key=lambda x: x.R, reverse=True)
    P = DynamicGraphGrowth(req, CandNodes)

    # print([(pair[1].msId, pair[1].instId) for pair in pFinal])
    Q = Tools.GetMicroserviceQueue(req)
    # for link in req.MsLinkList:
    #     print(link.msLink)
    # print('-------------')
    # Placement Begin
    while P:
        pMax = getMaxInP(P, G, req)
        placeFlag = True
        while req.isPlaced is not True:
            m = None
            for msList in Q:
                if msList[0].nodeId is None:
                    m = msList[0]
                    break
            if m is None:
                req.isPlaced = True
                break
            for ms in req.MsList[m.msId]:
                n = None
                for pair in pMax:
                    if ms == pair[1]:
                        n = pair[0]
                        break

                if n.cpuUsed + ms.cpuReq > n.CPU:
                    placeFlag = False
                    break
                n.AddMs(ms)
                # print(f' m{ms.msId}({ms.instId}) has been placed to node {n.nodeId}')
                for parent in ms.Parents:
                    if parent.nodeId is None:
                        continue
                    link = Tools.FindLink(req, parent, ms)
                    if parent.nodeId == n.nodeId:
                        link.linkPaths = []
                    else:
                        paths = G.FindShortestPaths(n.nodeId, parent.nodeId, maxNum)
                        # print(f'src: {n.nodeId} , dst: {parent.nodeId}', paths)
                        while paths:
                            shortest_path = paths[0]
                            if not Tools.CheckLinkConstraints(link, shortest_path, G, req):
                                # print(f' path len: {len(shortest_path) - 1}')
                                paths.remove(shortest_path)
                            else:
                                for edge in G.GetEdgeFromPathNodes(shortest_path):
                                    edge.AddLink(link)
                                link.linkPaths = [shortest_path]
                                break
                        if not link.linkPaths:
                            placeFlag = False
                    if not placeFlag:
                        break
                for son in ms.Sons:
                    if son.nodeId is None:
                        continue
                    link = Tools.FindLink(req, ms, son)
                    if son.nodeId == n.nodeId:
                        link.linkPaths = []
                    else:
                        paths = G.FindShortestPaths(n.nodeId, son.nodeId, maxNum)
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
                            placeFlag = False
                    if not placeFlag:
                        break
                if not placeFlag:
                    n.DelMs(ms)
                    break
            if not placeFlag:
                break
        if not placeFlag:
            P.remove(pMax)
            continue
        return True
    Tools.ClearRequestFromGraph(G, req)
    return False


def calNodeReliability(p, g: Graph, req: Request):
    allPlacedNode = []
    R = 1
    for pair in p:
        if pair[0].cpuUsed + pair[1].cpuReq <= pair[0].CPU:
            R *= pair[1].R
            if pair[0] not in allPlacedNode:
                allPlacedNode.append(pair[0])
        else:
            return -1
    for node in allPlacedNode:
        R *= node.R

    return R


def DynamicGraphGrowth(req: Request, candNodes: [Node]):
    totMsNum = len(req.MsList) + req.backupLimit - 1
    # print(totMsNum)
    Options = []
    for node in candNodes:
        for msList in req.MsList:
            for ms in msList:
                # print('ms: {ms.msId, ms.instId}')
                if ms.msId == 0:
                    continue
                if ms.cpuReq + node.cpuUsed <= node.CPU:
                    Options.append([node, ms, True])  # False is a flag to mark the pair not used.
    t = 0
    P = []
    # print('O length:  {len(Options)}')
    while t < T:
        # print(t)
        S_sub = []
        p = []
        for op in Options:
            # print(op)
            if not op[2]:
                continue
            flag = True
            for ms in S_sub:
                # print('ms: {ms.msId, ms.instId}, op[1]: {op[1].msId, op[1].instId}')
                if op[1] == ms:
                    flag = False
            # print(flag)
            if flag:
                p.append((op[0], op[1]))
                S_sub.append(op[1])
                op[2] = False
                if len(S_sub) == totMsNum:
                    break
        if len(S_sub) == totMsNum:
            P.append(p)
            # print(p)
        t += 1
    # print(len(P))
    return P


def getMaxInP(P, G: Graph, req: Request):
    P_Reliability = []
    for p in P:
        P_Reliability.append(calNodeReliability(p, G, req))
    maxIdx = P_Reliability.index(max(P_Reliability))
    pMax = P[maxIdx]
    return pMax


def printName():
    print('----------This is RRSP----------')
