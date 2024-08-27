import copy
from dataStructure.ms import Microservice
from dataStructure.msLink import MicroserviceLink
from dataStructure.request import Request
from dataStructure.node import Node
from dataStructure.graph import Graph
import networkx as nx
import Tools
import Paras

backtraceLimit = 10
maxNum = Paras.path_max_num


def run(G: Graph, req: Request):

    backtrace = 0
    Q = Tools.GetMicroserviceQueue(req)
    result = True
    while req.isPlaced is not True and backtrace < backtraceLimit:

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
        result = MicroservicePlacement(G, req, m, candNodes, maxNum)
        if not result:
            req.CancelMicroservicePlacement(G, m)

            # print(f' Cancel m{m.msId}({m.instId}) placement.')
            if m.msId != 1 and backtrace < backtraceLimit:
                for parent in m.Parents:
                    req.CancelMicroservicePlacement(G, parent)

                    # print(f' Cancel m{parent.msId}({parent.instId}) placement.')
                    parent.banedNodes.append(parent.nodeId)
                backtrace += 1
            else:
                result = False
                break
    if result and req.isPlaced:
        if req.backupLimit > 0:
            BackupPlacement(G, req, maxNum, req.backupLimit)
            return req.isPlaced
    else:
        Tools.ClearRequestFromGraph(G, req)
        # print('Placement Failed.')
        return False


def MicroservicePlacement(G: Graph, req: Request, mInst: Microservice, candNodes: [Node], MaxNum: int):
    n_max = None
    r_max = 0
    # print(f' Begin finding node for Ms{mInst.msId}({mInst.instId})')
    keyNodes = Tools.GetKeyNodes(req)
    # print(f' keyNodes: {keyNodes}')

    for n in candNodes:
        n_originR = n.R
        n.AddMs(mInst)
        r_f = 1
        available_flag = True
        parentIdList = []
        for parent in mInst.Parents:
            # print(f' Ms{mInst.msId}({mInst.instId}) parent: Ms{parent.msId}({parent.instId}) ')
            # print(f' parentIdList: {parentIdList}')
            if parent.msId not in parentIdList:
                r_b = 0
                parentInstList = req.MsList[parent.msId]
                InstFailedCount = 0
                for pInst in parentInstList:
                    if pInst.nodeId is None:
                        continue
                    link = Tools.FindLink(req, pInst, mInst)
                    if pInst.nodeId != n.nodeId:
                        disjoint_paths = G.FindDisjointPaths(n.nodeId, pInst.nodeId, MaxNum)
                        if len(disjoint_paths) == 0:
                            InstFailedCount += 1
                            continue
                        paths = []
                        pathTotR = 0
                        for path in disjoint_paths:
                            if Tools.CheckLinkConstraints(link, path, G, req):
                                paths.append(path)
                                pathR = G.GetInnerPathReliability(path, keyNodes)
                                pathR *= link.R
                                pathTotR = pathTotR + pathR - pathTotR * pathR
                        # print(f' available path num: {len(paths)}')
                        r_b = r_b + pathTotR - r_b * pathTotR
                    else:
                        r_b = r_b + link.R - r_b * link.R
                parentIdList.append(parent.msId)
                if InstFailedCount == len(parentInstList):
                    available_flag = False
                    break
                # print(f' r_b: {r_b}')
                r_f *= r_b
        if not available_flag:
            n.DelMs(mInst)
            continue
        # print(f' node: {n.nodeId} r_max: {r_max}, r_f: {r_f}')
        if n.nodeId not in keyNodes:
            r_f *= n.R
        else:
            r_f *= n.R/n_originR

            # print(n.R)

        # print(f' node: {n.nodeId} r_max: {r_max}, r_f: {r_f}')
        if r_max < r_f:
            r_max = r_f
            n_max = n
        n.DelMs(mInst)
    if n_max is None:
        return False

    n_max.AddMs(mInst)
    r_f = 1
    parentIdList = []
    for parent in mInst.Parents:
        if parent.msId not in parentIdList:
            r_b = 0
            parentInstList = req.MsList[parent.msId]
            for pInst in parentInstList:
                link = Tools.FindLink(req, pInst, mInst)
                # print(f' mInst m{mInst.msId}({mInst.instId}) nodeId: {mInst.nodeId},'
                #       f' pInst m{pInst.msId}({pInst.instId}) nodeId: {pInst.nodeId}')
                paths = []
                pathTotR = 0
                if pInst.nodeId == n_max.nodeId:
                    pathTotR = link.R
                    link.linkPaths = []
                else:
                    for path in G.FindDisjointPaths(mInst.nodeId, pInst.nodeId, MaxNum):
                        if Tools.CheckLinkConstraints(link, path, G, req):
                            paths.append(path)
                            # ---Place Link---
                            for edge in G.GetEdgeFromPathNodes(path):
                                edge.AddLink(link)
                            # -----------------
                            pathR = G.GetInnerPathReliability(path, keyNodes)
                            pathR *= link.R
                            pathTotR = pathTotR + pathR - pathTotR * pathR
                    if len(paths) > 0:
                        link.linkPaths = paths
                r_b = r_b + pathTotR - r_b * pathTotR
            r_f *= r_b
            parentIdList.append(parent.msId)
    if n_max.nodeId not in keyNodes:
        r_f *= n_max.R
    mInst.sigma = r_f * mInst.R

    if mInst.instId > 1:
        msSigma = req.MsList[mInst.msId][mInst.instId - 2].sigma
        mInst.sigma = msSigma + mInst.sigma - msSigma * mInst.sigma

        sonIdList = []
        for son in mInst.Sons:
            if son.msId not in sonIdList:
                sonInstList = req.MsList[son.msId]
                for sonInst in sonInstList:
                    if sonInst.nodeId is None:
                        continue
                    link = Tools.FindLink(req, mInst, sonInst)
                    paths = []
                    if sonInst.nodeId == n_max.nodeId:
                        link.linkPaths = []
                    else:
                        for path in G.FindDisjointPaths(mInst.nodeId, sonInst.nodeId, MaxNum):
                            if Tools.CheckLinkConstraints(link, path, G, req):
                                paths.append(path)
                                # ---Place Link---
                                for edge in G.GetEdgeFromPathNodes(path):
                                    edge.AddLink(link)

                        if len(paths) > 0:
                            link.linkPaths = paths
                sonIdList.append(son.msId)

    # print(f'Req {req.reqId}: m{mInst.msId}({mInst.instId}) has been placed to Node {n_max.nodeId}')
    return True


def BackupPlacement(G: Graph, req: Request, Cutoff: int, backupLimit):
    backupNum = 0
    BackupMs = copy.deepcopy(req.MsList)
    unableBackupMsId = [0]
    while backupNum < backupLimit and len(BackupMs) > 0:

        m_min_id = None
        r_min = 1.0
        for msList in req.MsList:
            if msList[0].msId in unableBackupMsId:
                continue
            maxSigma = 0
            for ms in msList:
                if ms.sigma > maxSigma:
                    maxSigma = ms.sigma
            if r_min >= maxSigma:
                r_min = maxSigma
                m_min_id = msList[0].msId
        if m_min_id is None:
            break
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
            unableBackupMsId.append(m_new.msId)
            req.DeleteBackupMs(m_new)
        else:
            isPlaced = MicroservicePlacement(G, req, m_new, candNodes, Cutoff)
            if isPlaced:
                backupNum += 1
                # print(f' request link num: {len(req.MsLinkList)}')
                # Tools.EvaluatePlacementReliability(G, req)
            else:
                unableBackupMsId.append(m_new.msId)
                req.CancelMicroservicePlacement(G, m_new)
                # print(f' Cancel m{m_new.msId}({m_new.instId}) placement.')
                req.DeleteBackupMs(m_new)
    return True


def printName():
    print('----------This is SRP----------')
