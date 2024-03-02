import copy
from dataStructure.ms import Microservice
from dataStructure.msLink import MicroserviceLink
from dataStructure.request import Request
from dataStructure.node import Node
from dataStructure.graph import Graph
import networkx as nx
import Tools

backtraceLimit = 3


def run(G: Graph, req: Request, cutoff: int):
    print(f'Req {req.reqId} arrived at Node {req.arriveNodeId} with {len(req.MsList) - 1} Microservices')
    print(f'BackupLimit: {req.backupLimit}')
    backtrace = 0
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
            if m.msId != 1 and backtrace < backtraceLimit:
                for parent in m.Parents:
                    req.CancelMicroservicePlacement(G, parent)
                    parent.banedNodes.append(parent.nodeId)
                backtrace += 1
                continue
            else:
                result = False
                break
        result = MicroservicePlacement(G, req, m, candNodes, cutoff)
    if result:
        print('Before Backup')
        print(f'request link num: {len(req.MsLinkList)}')
        print(f'Backup limit: {req.backupLimit} After Backup')
        Tools.EvaluatePlacementReliability(G, req)
        if req.backupLimit > 0:
            BackupPlacement(G, req, cutoff, req.backupLimit)
    else:
        Tools.ClearRequestFromGraph(G, req)
        print('Placement Failed.')


def MicroservicePlacement(G: Graph, req: Request, mInst: Microservice, candNodes: [Node], cutoff: int):
    n_max = None
    r_max = 0
    for n in candNodes:
        n.AddMs(mInst)
        r_f = 1
        available_flag = True
        parentIdList = []
        for parent in mInst.Parents:
            if parent.msId not in parentIdList:
                r_b = 0
                parentInstList = req.MsList[parent.msId]
                InstFailedCount = 0
                for pInst in parentInstList:
                    link = Tools.FindLink(req, pInst, mInst)
                    if pInst.nodeId != n.nodeId:
                        disjoint_paths = G.FindDisjointPaths(n.nodeId, pInst.nodeId, cutoff)
                        if len(disjoint_paths) == 0:
                            InstFailedCount += 1
                            continue
                        paths = []
                        pathTotR = 0
                        for path in disjoint_paths:
                            if Tools.CheckLinkConstraints(link, path, G, req):
                                paths.append(path)
                                pathR = G.GetInnerPathReliability(path)
                                pathR *= link.R
                                pathTotR = pathTotR + pathR - pathTotR * pathR
                        r_b = r_b + pathTotR - r_b * pathTotR
                    else:
                        r_b = r_b + link.R - r_b * link.R
                parentIdList.append(parent.msId)
                if InstFailedCount == len(parentInstList):
                    available_flag = False
                    break
                r_f *= r_b
        if not available_flag:
            n.DelMs(mInst)
            continue
        flag = True
        for parent in mInst.Parents:
            if parent.nodeId == n.nodeId:
                flag = False
                break
        if flag:
            r_f *= n.R

        print(f' node: {n.nodeId} r_max: {r_max}, r_f: {r_f}')
        if r_max < r_f:
            r_max = r_f
            n_max = n
        n.DelMs(mInst)
    if n_max is None:
        return False
    n_max.AddMs(mInst)
    print(f'Req {req.reqId}: M{mInst.msId} has been placed to Node {n_max.nodeId}')
    r_b = 0
    r_f = 1
    for parent in mInst.Parents:
        parentInstList = req.MsList[parent.msId]
        for pInst in parentInstList:
            link = None
            for msLink in req.MsLinkList:
                if ((pInst.msId, pInst.instId), (mInst.msId, mInst.instId)) == msLink.msLink:
                    link = msLink
                    break
            paths = []
            pathTotR = 0
            if pInst.nodeId == n_max.nodeId:
                pathTotR = link.R
                link.linkPaths = []
            else:
                for path in nx.node_disjoint_paths(G.topoGraph, mInst.nodeId, pInst.nodeId, cutoff=cutoff):
                    if Tools.CheckLinkConstraints(link, path, G, req):
                        paths.append(path)
                        # ---Place Link---
                        for edge in G.GetEdgeFromPathNodes(path):
                            edge.AddLink(link)
                        # -----------------
                        pathR = G.GetInnerPathReliability(path)
                        pathR *= link.R
                        pathTotR = pathTotR + pathR - pathTotR * pathR
                link.linkPaths = paths
            r_b = r_b + pathTotR - r_b * pathTotR
        r_f *= r_b
    r_f *= n_max.R
    mInst.sigma = r_f * mInst.R
    if mInst.instId > 1:
        for son in mInst.Sons:
            sonInstList = req.MsList[son.msId]
            for sonInst in sonInstList:
                link = None
                for msLink in req.MsLinkList:
                    if ((mInst.msId, mInst.instId), (sonInst.msId, sonInst.instId)) == msLink.msLink:
                        link = msLink
                        break
                paths = []
                if sonInst.nodeId == n_max.nodeId:
                    link.linkPaths = []
                else:

                    for path in nx.node_disjoint_paths(G.topoGraph, mInst.nodeId, sonInst.nodeId, cutoff=cutoff):
                        if Tools.CheckLinkConstraints(link, path, G, req):
                            paths.append(path)
                            # ---Place Link---
                            for edge in G.GetEdgeFromPathNodes(path):
                                edge.AddLink(link)

                            # -----------------
                    link.linkPaths = paths
    return True


def BackupPlacement(G: Graph, req: Request, cutoff: int, backupLimit):
    backupNum = 0
    BackupMs = copy.deepcopy(req.MsList)

    BackupMs.remove(BackupMs[0])
    while backupNum < backupLimit and len(BackupMs) > 0:
        m_min_id = None
        r_min = 1.0
        for msList in BackupMs:
            if r_min >= msList[0].sigma:
                r_min = msList[0].sigma
                m_min_id = msList[0].msId
        m_new = None
        for msList in req.MsList:
            m_origin = msList[0]
            if m_origin.msId == m_min_id:
                m_new = Microservice(
                    req.reqId,
                    m_min_id,
                    len(msList) + 1,
                    m_origin.cpuReq,
                    m_origin.reLambda,
                    m_origin.gamma,
                    m_origin.procDelay
                )
                for parent in m_origin.Parents:
                    m_new.Parents.append(parent)
                    parent.Sons.append(m_new)
                    originLink = Tools.FindLink(req, req.MsList[parent.msId][0], req.MsList[m_new.msId][0])
                    newLink = MicroserviceLink(
                        req.reqId,
                        ((parent.msId, parent.instId), (m_new.msId, m_new.instId)),
                        originLink.bwReq,
                        originLink.reLambda,
                        originLink.ddl
                    )
                    req.MsLinkList.append(newLink)
                for son in m_origin.Sons:
                    m_new.Sons.append(son)
                    son.Parents.append(m_new)
                    originLink = Tools.FindLink(req, req.MsList[m_new.msId][0], req.MsList[son.msId][0])
                    newLink = MicroserviceLink(
                        req.reqId,
                        ((m_new.msId, m_new.instId), (son.msId, son.instId)),
                        originLink.bwReq,
                        originLink.reLambda,
                        originLink.ddl
                    )
                    req.MsLinkList.append(newLink)
                msList.append(m_new)
                break
        candNodes = []
        for node in G.nodeList:
            if node not in m_new.banedNodes and node.cpuUsed + m_new.cpuReq <= node.CPU:
                candNodes.append(node)
        if len(candNodes) == 0:
            for backupMsList in BackupMs:
                if backupMsList[0].msId == m_new.msId:
                    BackupMs.remove(backupMsList)
        else:

            isPlaced = MicroservicePlacement(G, req, m_new, candNodes, cutoff)
            if isPlaced:
                backupNum += 1
                print(f'Backup M{m_new.msId}({m_new.instId}) result: Success.')
                print(f'request link num: {len(req.MsLinkList)}')
                Tools.EvaluatePlacementReliability(G, req)
            else:
                print(f'Backup M{m_new.msId}({m_new.instId}) result: Failed.')


def printName():
    print('----------This is PRP-S----------')
