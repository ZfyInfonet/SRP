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

    CreateBackup(req)
    # line 1
    LinkedList = sorted(G.nodeList, key=lambda x: ((x.CPU - x.cpuUsed) * x.R))
    Reserve_list = []

    for b in range(2):     # line 2
        for msList in Q:            # line 3
            if b + 1 > len(msList):
                continue
            m = msList[b]
            for n in LinkedList:    # line 4
                if Suitable(m, msList, n):
                    Reserve_list.append((m, n))
                    n.AddMs(m)
                    LinkedList.remove(n)
                    LinkedList = [n] + LinkedList
                    break
    Placement_list = Relocation(Reserve_list, G, req)
    # for tup in Placement_list:
    #     print(f' m{tup[0].msId}({tup[0].instId}) in node {tup[1].nodeId}')

    SelectPath(G, req)

    if selfCheck(req):
        return True
    else:
        Tools.ClearRequestFromGraph(G, req)
        return False


def selfCheck(req: Request):
    result = True
    for link in req.MsLinkList:
        parent = req.MsList[link.msLink[0][0]][link.msLink[0][1] - 1]
        son = req.MsList[link.msLink[1][0]][link.msLink[1][1] - 1]
        if parent.instId == 1 and son.instId == 1:
            if parent.nodeId is None or son.nodeId is None or link.linkPaths is None:
                result = False
                break
    req.isPlaced = result
    return result


def Relocation(reserve_list, g: Graph, req: Request):
    replace_node_tuple = []
    placement_list = []
    for (m, n_i) in reserve_list:
        already_moved = False
        for tup in replace_node_tuple:
            n_j = tup[1]
            if n_i == tup[0]:
                if n_j.cpuUsed + m.cpuReq <= n_j.CPU:
                    n_i.DelMs(m)
                    n_j.AddMs(m)
                    placement_list.append((m, n_j))
                else:
                    placement_list.append((m, n_i))
                already_moved = True
                break

        if already_moved:
            continue
        maxNode = n_i
        for n_j in g.nodeList:
            if n_j.nodeId == n_i.nodeId:
                continue
            if n_j.R > n_i.R and Suitable(m, req.MsList[m.msId], n_j):
                maxNode = n_j
        if maxNode != n_i:
            n_i.DelMs(m)
            maxNode.AddMs(m)
            replace_node_tuple.append((n_i, maxNode))

        placement_list.append((m, maxNode))

    return placement_list


def SelectPath(g: Graph, req: Request):
    for link in req.MsLinkList:
        parent = req.MsList[link.msLink[0][0]][link.msLink[0][1] - 1]
        son = req.MsList[link.msLink[1][0]][link.msLink[1][1] - 1]
        if parent.nodeId is None or son.nodeId is None:
            continue
        if parent.nodeId == son.nodeId:
            link.linkPaths = []
        else:
            paths = g.FindDisjointPaths(parent.nodeId, son.nodeId, maxNum)
            pathLength = [len(p) for p in paths]
            while paths:
                shortest_idx = pathLength.index(min(pathLength))
                shortest_path = paths[shortest_idx]
                if not Tools.CheckLinkConstraints(link, shortest_path, g, req):
                    # print(f' path len: {len(shortest_path) - 1}')
                    pathLength.remove(pathLength[shortest_idx])
                    paths.remove(shortest_path)
                else:
                    for edge in g.GetEdgeFromPathNodes(shortest_path):
                        edge.AddLink(link)
                    link.linkPaths = [shortest_path]
                    break
            if not link.linkPaths:
                if parent.instId == 1 and son.instId == 1:
                    break


def Suitable(m: Microservice, msList: [Microservice], n: Node):
    if m.cpuReq + n.cpuUsed > n.CPU:
        return False
    for ms in msList:
        if ms.nodeId == n.nodeId:
            return False
    return True


def CreateBackup(req: Request):
    backupNum = 0
    for msList in req.MsList:
        if backupNum == req.backupLimit:
            break
        if msList[0].msId == 0:
            continue
        m_origin = msList[0]
        m_new = Microservice(
            req.reqId,
            m_origin.msId,
            len(msList) + 1,
            m_origin.cpuReq,
            m_origin.reLambda,
            m_origin.gamma,
            m_origin.procDelay
        )
        for parent in m_origin.Parents:
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
            req.MsLinkList.append(newLink)
        for son in m_origin.Sons:
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
        msList.append(m_new)
        backupNum += 1


def printName():
    print('----------This is DAIP----------')
