import copy
import numpy as np
from dataStructure.ms import Microservice
from dataStructure.msLink import MicroserviceLink
from dataStructure.request import Request
from dataStructure.node import Node
from dataStructure.graph import Graph
import networkx as nx
import Tools
import Paras


class Solution:
    def __init__(self, solution, is_valid):
        self.solution = solution
        self.isValid = is_valid


maxNum = Paras.path_max_num


def run(g: Graph, req: Request):
    n_num = len(g.nodeList)
    solution_result = np.zeros([n_num, n_num, n_num])
    solution_list = []
    max_reliability = 0
    final_solution = None
    final_reliability = 0
    final_id = 1
    for mid in [1, 2]:
        optimal_solution = None
        optimal_reliability = 0
        for i in range(n_num):
            for j in range(n_num):
                for x in range(n_num):
                    req_cp = copy.deepcopy(req)
                    req_cp = backup(req_cp, mid)
                    g_cp = copy.deepcopy(g)
                    solution = [i, j, x]
                    # print(f'mid: {mid}, solution: {solution}')
                    cor_ms_instance_id = [1, 1, 2]
                    solution_list.append(Solution(solution, 0))
                    solution_valid = True
                    result = [False, False, False]
                    for n in g_cp.nodeList:
                        for dst in solution:
                            s_id = solution.index(dst)
                            if s_id == 0:
                                ms_id = 1
                            elif s_id == 1:
                                ms_id = 2
                            else:
                                ms_id = mid
                            mInst = req_cp.MsList[ms_id][cor_ms_instance_id[s_id]-1]
                            if dst == mInst.nodeId:
                                result[s_id] = True
                            elif n.nodeId == dst and n.cpuUsed + mInst.cpuReq <= n.CPU:
                                n.AddMs(req_cp.MsList[ms_id][cor_ms_instance_id[s_id]-1])
                                result[s_id] = True
                            else:
                                continue
                    if False in result:
                        solution_valid = False
                    if not solution_valid:
                        continue
                    link_valid = False
                    for link in req_cp.MsLinkList:
                        src_ms = req_cp.MsList[link.msLink[0][0]][link.msLink[0][1] - 1]
                        dst_ms = req_cp.MsList[link.msLink[1][0]][link.msLink[1][1] - 1]

                        src = src_ms.nodeId
                        dst = dst_ms.nodeId
                        # if (src is None or dst is None) and link.msLink[0][1] == 1 and link.msLink[1][1] == 1:
                        #     break
                        paths = []
                        if src == dst:
                            link.linkPaths = []
                            link_valid = True
                        else:
                            for path in g_cp.FindDisjointPaths(src, dst, maxNum):
                                if Tools.CheckLinkConstraints(link, path, g_cp, req_cp):
                                    paths.append(path)
                                    # ---Place Link---
                                    for edge in g_cp.GetEdgeFromPathNodes(path):
                                        edge.AddLink(link)
                                    # -----------------
                            if len(paths) > 0:
                                link.linkPaths = paths
                                link_valid = True
                    if not link_valid:
                        continue
                    req_cp.isPlaced = True

                    reliabiltiy = Tools.EvaluatePlacementReliability(g_cp, req_cp)
                    print('------------------------')
                    for tempNode in g_cp.nodeList:
                        print(f'node: {tempNode.nodeId}, reliability:{tempNode.R}, microservice:{tempNode.MicroservicesIdList}')
                    print(f'solution:{solution}, reliability:{reliabiltiy}')
                    print('------------------------')
                    if reliabiltiy > 0:
                        solution_list[-1].isValid = 1
                        solution_result[i, j, x] = reliabiltiy
                        if max_reliability < reliabiltiy:
                            max_reliability = reliabiltiy
                            print(f'maxR: {max_reliability}, solution: {solution}')
                            optimal_solution = solution_list[-1]
                            optimal_reliability = reliabiltiy
        if optimal_reliability > final_reliability:
            final_solution = optimal_solution
            final_reliability = optimal_reliability
            print(f'optR: {optimal_reliability}')
            if mid == 2:
                final_id = 2

    if not final_solution:
        return False
    else:
        print(f'final solution: {final_solution.solution}')

    req = backup(req, final_id)
    for n in g.nodeList:
        for s_id in range(len(final_solution.solution)):
            dst_nodeid = final_solution.solution[s_id]

            if s_id == 0:
                mInst = req.MsList[1][0]
            elif s_id == 1:
                mInst = req.MsList[2][0]
            else:
                mInst = req.MsList[final_id][1]

            if n.nodeId == dst_nodeid:
                n.AddMs(mInst)
    req.isPlaced = True
    for link in req.MsLinkList:
        src_ms = req.MsList[link.msLink[0][0]][link.msLink[0][1] - 1]
        dst_ms = req.MsList[link.msLink[1][0]][link.msLink[1][1] - 1]
        src = src_ms.nodeId
        dst = dst_ms.nodeId
        paths = []
        if src == dst:
            link.linkPaths = []
        else:
            for path in g.FindDisjointPaths(src, dst, maxNum):
                if Tools.CheckLinkConstraints(link, path, g, req):
                    paths.append(path)
                    # ---Place Link---
                    for edge in g.GetEdgeFromPathNodes(path):
                        edge.AddLink(link)
                    # -----------------
            if len(paths) > 0:
                link.linkPaths = paths
    print(f'The True placement Reliability:{Tools.EvaluatePlacementReliability(g, req)}')
    return True


def printName():
    print('----------This is Optimal----------')


def backup(req, mid):
    m_obj = req.MsList[mid][0]
    m_obj_new = Microservice(
        req.reqId,
        mid,
        len(req.MsList[mid]) + 1,
        m_obj.cpuReq,
        m_obj.reLambda,
        m_obj.gamma,
        m_obj.procDelay
    )

    for parent in m_obj.Parents:
        m_obj_new.Parents.append(parent)
        parent.Sons.append(m_obj_new)
        originLink = Tools.FindLink(req, req.MsList[parent.msId][0], req.MsList[m_obj_new.msId][0])
        newLink = MicroserviceLink(
            req.reqId,
            ((parent.msId, parent.instId), (m_obj_new.msId, m_obj_new.instId)),
            originLink.bwReq,
            originLink.reLambda,
            originLink.ddl
        )
        req.MsLinkList.append(newLink)
    for son in m_obj.Sons:
        m_obj_new.Sons.append(son)
        son.Parents.append(m_obj_new)
        originLink = Tools.FindLink(req, req.MsList[m_obj_new.msId][0], req.MsList[son.msId][0])
        newLink = MicroserviceLink(
            req.reqId,
            ((m_obj_new.msId, m_obj_new.instId), (son.msId, son.instId)),
            originLink.bwReq,
            originLink.reLambda,
            originLink.ddl
        )
        req.MsLinkList.append(newLink)

    req.MsList[mid].append(m_obj_new)
    return req
