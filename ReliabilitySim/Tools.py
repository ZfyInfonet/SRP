import networkx as nx
import matplotlib.pyplot as plt
import os
import json
import numpy as np
import Paras
import random
from dataStructure.ms import Microservice
from dataStructure.msLink import MicroserviceLink
from dataStructure.request import Request
from dataStructure.node import Node
from dataStructure.edge import Edge
from dataStructure.graph import Graph
from itertools import *


# random.seed = 1


def Initialization(req_num, node_num, edge_p, graph_num, is_full_back, if_change_topo):
    arrNode_num = int(node_num * Paras.access_node_ratio)
    Graphs = CreateGraph(graph_num, node_num, edge_p, if_change_topo)
    reqList = CreateReq(req_num, arrNode_num, is_full_back)

    return Graphs, reqList


def OptimalInitialization(req_num, node_num, edge_p, graph_num, is_full_back, if_change_topo):
    arrNode_num = int(node_num * Paras.access_node_ratio)
    Graphs = CreateGraph(graph_num, node_num, edge_p, if_change_topo)
    reqList = CreateOptimalReq(req_num, arrNode_num, is_full_back)

    return Graphs, reqList


def CustomizedTopoInitialization(req_num, topo_name, is_full_back):
    graph, arrNode_num = CreateCustomizedGraph(topo_name)
    reqList = CreateReq(req_num, arrNode_num, is_full_back)
    return graph, reqList


def ReqArriveIndex(req_num, arrive_rate):
    req_count = 0
    req_arrive_index = []
    while req_count < req_num:
        arrived_req_num = np.random.poisson(arrive_rate)
        if arrived_req_num + req_count > req_num:
            req_arrive_index.append(req_num - req_count)
            req_count += req_num - req_count
        else:
            req_arrive_index.append(arrived_req_num)
            req_count += arrived_req_num
    while req_arrive_index[0] == 0:
        req_arrive_index.remove(0)
    return req_arrive_index


def CreateTopo(node_num, edge_p, index):
    G = None  # nx.erdos_renyi_graph(node_num, edge_p, directed=False)
    Connected = False
    while not Connected:
        Flag = True
        G = nx.erdos_renyi_graph(node_num, edge_p, directed=False)
        for i in range(node_num):
            if G.degree[i] == 0:
                Flag = False
                break
        if Flag:
            Connected = True

    nodes = []
    for i in G.nodes:
        nodes.append(i)
    edges = []
    acc_nodes = []
    degree = [0] * node_num
    nodes_c = nodes.copy()
    for i in G.edges:
        edges.append(i)
    for i, j in G.edges:
        degree[i] += 1
        degree[j] += 1
    nodes_c.sort(key=lambda x: degree[x])
    for i in range(int(node_num * Paras.access_node_ratio)):  # the number of access nodes is 20% node numbers.
        acc_nodes.append(nodes_c[i])
    topo = {'nodes': nodes, 'accNodes': acc_nodes, 'edges': edges}
    with open(f"./topo/node_{node_num}_edge_{edge_p}_{index}.json", 'w') as f:
        f.write(json.dumps(topo))

    return topo


def GetCustomizedTopo(topo_name):
    with open(f'./customized_topo/{topo_name}.json', 'r') as f:
        topo = json.loads(f.read())
    return topo


def GetTopo(node_num, edge_p, index, if_change_topo):
    if not if_change_topo and node_num == 50:
        with open(f'./topo/node_50_edge_0.2_0_mainSim.json', 'r') as f:
            topo = json.loads(f.read())
        return topo

    # if os.path.exists(f'./topo/node_{node_num}_edge_{edge_p}_{index}.json'):
    #     with open(f'./topo/node_{node_num}_edge_{edge_p}_{index}.json', 'r') as f:
    #         topo = json.loads(f.read())
    # else:
    #
    topo = CreateTopo(node_num, edge_p, index)
    return topo


def DrawTopo(path):
    with open(path, 'r') as f:
        topo = json.loads(f.read())
        G = nx.Graph()
        G.add_edges_from(topo['edges'])
        nx.draw(G, with_labels=True)
        plt.show()


def CreateMs(req_id, ms_num, id_list, parent_ms=None):
    ms_list = []
    for i in range(ms_num):
        ms = Microservice(req_id=req_id,
                          ms_id=id_list[i],
                          inst_id=1,
                          cpu=random.uniform(*Paras.ms_cpuReq_range),
                          reLambda=random.uniform(*Paras.ms_lambda_range),
                          gamma=random.uniform(*Paras.ms_gamma_range),
                          proc_delay=random.uniform(*Paras.ms_delay_range))
        if parent_ms is not None:
            ms.Parents.append(parent_ms)
        ms_list.append(ms)
    return ms_list


def CreateOptimalReq(req_num, acc_node_num, isFullBack):
    MsNum = 2
    if isFullBack:
        BackNum = MsNum
    else:
        BackNum = random.randint(1, MsNum)
    Req = []
    for req_idx in range(req_num):
        req_arriveNodeId = random.randint(0, acc_node_num - 1)
        G = nx.DiGraph()
        ms_Num = MsNum  # random.randint(*Paras.ms_num_range)
        ms_links = [(0, 1)]
        ms_List = []
        m0 = Microservice(req_id=req_idx,
                          ms_id=0,
                          inst_id=1,
                          cpu=0,
                          reLambda=0,
                          gamma=0,
                          proc_delay=0)
        m1 = Microservice(req_id=req_idx,
                          ms_id=1,
                          inst_id=1,
                          cpu=random.uniform(*Paras.ms_cpuReq_range),
                          reLambda=random.uniform(*Paras.ms_lambda_range),
                          gamma=random.uniform(*Paras.ms_gamma_range),
                          proc_delay=random.uniform(*Paras.ms_delay_range))
        m0.nodeId = req_arriveNodeId
        m0.Sons.append(m1)
        m1.Parents.append(m0)
        ms_List.append(m0)
        ms_List.append(m1)
        # ms_Idx = 1
        layerMsNumList = []
        while sum(layerMsNumList) + 1 < ms_Num:
            layerMsNum = random.randint(1, ms_Num - 1 - sum(layerMsNumList))
            layerMsNumList.append(layerMsNum)
        layerFirstMs = ms_List[1]
        for i in range(len(layerMsNumList)):
            layerNum = layerMsNumList[i]
            id_list = [len(ms_List) + i for i in range(layerNum)]
            layerMsList = CreateMs(req_idx, layerNum, id_list)
            for ms in layerMsList:
                if layerFirstMs.msId == 1:
                    ms.Parents.append(layerFirstMs)
                    layerFirstMs.Sons.append(ms)
                    ms_links.append((layerFirstMs.msId, ms.msId))
                else:
                    last_layer_num = layerMsNumList[i - 1]
                    parentId = random.randint(layerMsList[0].msId - last_layer_num, layerMsList[0].msId - 1)
                    ms.Parents.append(ms_List[parentId])
                    ms_List[parentId].Sons.append(ms)
                    ms_links.append((parentId, ms.msId))
            layerFirstMs = layerMsList[0]
            ms_List += layerMsList
        layerFirstId = 2
        for i in range(len(layerMsNumList)):
            if layerMsNumList[i] > 1:
                for inLayerOrder in range(layerMsNumList[i] - 1):
                    msId = layerFirstId + inLayerOrder
                    for leftOrder in range(layerMsNumList[i] - 1 - inLayerOrder):
                        msSonId = msId + leftOrder + 1
                        if 0.5 <= random.uniform(0, 1) < 1:
                            ms_List[msId].Sons.append(ms_List[msSonId])
                            ms_List[msSonId].Parents.append(ms_List[msId])
                            a, b = msId, msSonId
                            ms_links.append((a, b))
                            G.add_edges_from(ms_links)
                            if not nx.is_directed_acyclic_graph(G):
                                ms_links.remove((a, b))
                                G.remove_edge(a, b)
                                ms_List[msId].Sons.remove(ms_List[msSonId])
                                ms_List[msSonId].Parents.remove(ms_List[msId])
            layerFirstId += layerMsNumList[i]

        MsList = []
        for ms in ms_List:
            MsList.append([ms])

        Ms_links = []
        for link in ms_links:
            bw = random.uniform(*Paras.msLink_bwReq_range)
            Link = MicroserviceLink(req_id=req_idx,
                                    ms_link=((link[0], 1), (link[1], 1)),
                                    bandwidth=bw,
                                    re_lambda=random.uniform(*Paras.msLink_lambda_range),
                                    ddl=ms_List[link[1]].gamma / bw + ms_List[link[1]].procDelay +
                                        random.uniform(*Paras.msLink_ddl_range),
                                    )
            Ms_links.append(Link)

        # --- check ---
        # for ms in ms_List:
        #     print(ms.reqId, ms.msId, ms.instId, ms.cpuRequest, ms.reLambda, ms.gamma, ms.procDelay, '\n')
        #     print([pars.msId for pars in ms.Parents], [pars.msId for pars in ms.Sons], '\n')
        # for Link in Ms_links:
        #     print(Link.msLink, Link.bwRequest, Link.reLambda, Link.ddl, '\n')
        G2 = nx.DiGraph()
        G2.add_edges_from(ms_links)
        if not nx.is_directed_acyclic_graph(G2):
            raise Exception("This graph is not DAG.")
        # nx.draw(G2, with_labels=True)
        # plt.show()

        req = Request(
            req_id=req_idx,
            nodeId=req_arriveNodeId,
            ms_list=MsList,
            ms_link_list=Ms_links,
            backup_limit=BackNum,
            lifetime=random.uniform(*Paras.lifetime_range),
            topo=G2
        )
        # print(req.reqId, req.arriveNodeId, len(req.MsList), len(req.MsLinkList))
        Req.append(req)
    print(f'{req_num} requests have been generated.')
    return Req


def CreateReq(req_num, acc_node_num, isFullBack):
    MsNum = random.randint(1, 5)
    if isFullBack:
        BackNum = MsNum
    else:
        BackNum = random.randint(1, MsNum)
    Req = []
    for req_idx in range(req_num):
        req_arriveNodeId = random.randint(0, acc_node_num - 1)
        G = nx.DiGraph()
        ms_Num = MsNum  # random.randint(*Paras.ms_num_range)
        ms_links = [(0, 1)]
        ms_List = []
        m0 = Microservice(req_id=req_idx,
                          ms_id=0,
                          inst_id=1,
                          cpu=0,
                          reLambda=0,
                          gamma=0,
                          proc_delay=0)
        m1 = Microservice(req_id=req_idx,
                          ms_id=1,
                          inst_id=1,
                          cpu=random.uniform(*Paras.ms_cpuReq_range),
                          reLambda=random.uniform(*Paras.ms_lambda_range),
                          gamma=random.uniform(*Paras.ms_gamma_range),
                          proc_delay=random.uniform(*Paras.ms_delay_range))
        m0.nodeId = req_arriveNodeId
        m0.Sons.append(m1)
        m1.Parents.append(m0)
        ms_List.append(m0)
        ms_List.append(m1)
        # ms_Idx = 1
        layerMsNumList = []
        while sum(layerMsNumList) + 1 < ms_Num:
            layerMsNum = random.randint(1, ms_Num - 1 - sum(layerMsNumList))
            layerMsNumList.append(layerMsNum)
        layerFirstMs = ms_List[1]
        for i in range(len(layerMsNumList)):
            layerNum = layerMsNumList[i]
            id_list = [len(ms_List) + i for i in range(layerNum)]
            layerMsList = CreateMs(req_idx, layerNum, id_list)
            for ms in layerMsList:
                if layerFirstMs.msId == 1:
                    ms.Parents.append(layerFirstMs)
                    layerFirstMs.Sons.append(ms)
                    ms_links.append((layerFirstMs.msId, ms.msId))
                else:
                    last_layer_num = layerMsNumList[i - 1]
                    parentId = random.randint(layerMsList[0].msId - last_layer_num, layerMsList[0].msId - 1)
                    ms.Parents.append(ms_List[parentId])
                    ms_List[parentId].Sons.append(ms)
                    ms_links.append((parentId, ms.msId))
            layerFirstMs = layerMsList[0]
            ms_List += layerMsList
        layerFirstId = 2
        for i in range(len(layerMsNumList)):
            if layerMsNumList[i] > 1:
                for inLayerOrder in range(layerMsNumList[i] - 1):
                    msId = layerFirstId + inLayerOrder
                    for leftOrder in range(layerMsNumList[i] - 1 - inLayerOrder):
                        msSonId = msId + leftOrder + 1
                        if 0.5 <= random.uniform(0, 1) < 1:
                            ms_List[msId].Sons.append(ms_List[msSonId])
                            ms_List[msSonId].Parents.append(ms_List[msId])
                            a, b = msId, msSonId
                            ms_links.append((a, b))
                            G.add_edges_from(ms_links)
                            if not nx.is_directed_acyclic_graph(G):
                                ms_links.remove((a, b))
                                G.remove_edge(a, b)
                                ms_List[msId].Sons.remove(ms_List[msSonId])
                                ms_List[msSonId].Parents.remove(ms_List[msId])
            layerFirstId += layerMsNumList[i]

        MsList = []
        for ms in ms_List:
            MsList.append([ms])

        Ms_links = []
        for link in ms_links:
            bw = random.uniform(*Paras.msLink_bwReq_range)
            Link = MicroserviceLink(req_id=req_idx,
                                    ms_link=((link[0], 1), (link[1], 1)),
                                    bandwidth=bw,
                                    re_lambda=random.uniform(*Paras.msLink_lambda_range),
                                    ddl=ms_List[link[1]].gamma / bw + ms_List[link[1]].procDelay +
                                        random.uniform(*Paras.msLink_ddl_range),
                                    )
            Ms_links.append(Link)

        # --- check ---
        # for ms in ms_List:
        #     print(ms.reqId, ms.msId, ms.instId, ms.cpuRequest, ms.reLambda, ms.gamma, ms.procDelay, '\n')
        #     print([pars.msId for pars in ms.Parents], [pars.msId for pars in ms.Sons], '\n')
        # for Link in Ms_links:
        #     print(Link.msLink, Link.bwRequest, Link.reLambda, Link.ddl, '\n')
        G2 = nx.DiGraph()
        G2.add_edges_from(ms_links)
        if not nx.is_directed_acyclic_graph(G2):
            raise Exception("This graph is not DAG.")
        # nx.draw(G2, with_labels=True)
        # plt.show()

        req = Request(
            req_id=req_idx,
            nodeId=req_arriveNodeId,
            ms_list=MsList,
            ms_link_list=Ms_links,
            backup_limit=BackNum,
            lifetime=random.uniform(*Paras.lifetime_range),
            topo=G2
        )
        # print(req.reqId, req.arriveNodeId, len(req.MsList), len(req.MsLinkList))
        Req.append(req)
    print(f'{req_num} requests have been generated.')
    return Req


def CreateCustomizedGraph(topo_name):
    topo = GetCustomizedTopo(topo_name=topo_name)
    nodes = topo['nodes']
    acc_nodes = topo['accNodes']
    edges = topo['edges']
    gNodes = []
    gEdges = []
    for edge in edges:
        gEdge = Edge(
            edge[0],
            edge[1],
            random.uniform(*Paras.edge_bw_range),
            random.uniform(*Paras.edge_lambda_range),
            random.uniform(*Paras.edge_delay_range))
        gEdges.append(gEdge)
    for nodeId in nodes:
        edgeList = []
        for gEdge in gEdges:
            if nodeId in gEdge.ends:
                edgeList.append(gEdge)
        gNode = Node(
            nodeId,
            random.uniform(*Paras.node_cpu_range),
            random.uniform(*Paras.node_reLow_range),
            random.uniform(*Paras.node_reHigh_range),
            random.uniform(*Paras.node_threshold_range),
            (nodeId in acc_nodes),
            edgeList
        )
        gNodes.append(gNode)
    G = nx.Graph()
    G.add_edges_from(edges)
    adj_matrix = nx.to_numpy_array(G)
    graph = Graph(0, gNodes, gEdges, adj_matrix, G)
    graph.printInfo()
    return graph, len(acc_nodes)


def CreateGraph(graph_num, node_num, edge_p, is_change_topo):
    Graphs = []
    for graphIdx in range(graph_num):
        topo = GetTopo(node_num, edge_p, graphIdx, is_change_topo)
        nodes = topo['nodes']
        acc_nodes = topo['accNodes']
        edges = topo['edges']
        gNodes = []
        gEdges = []
        for edge in edges:
            gEdge = Edge(
                edge[0],
                edge[1],
                random.uniform(*Paras.edge_bw_range),
                random.uniform(*Paras.edge_lambda_range),
                random.uniform(*Paras.edge_delay_range))
            gEdges.append(gEdge)
        for nodeId in nodes:
            edgeList = []
            for gEdge in gEdges:
                if nodeId in gEdge.ends:
                    edgeList.append(gEdge)
            gNode = Node(
                nodeId,
                random.uniform(*Paras.node_cpu_range),
                random.uniform(*Paras.node_reLow_range),
                random.uniform(*Paras.node_reHigh_range),
                random.uniform(*Paras.node_threshold_range),
                (nodeId in acc_nodes),
                edgeList
            )

            gNodes.append(gNode)

        G = nx.Graph()
        G.add_edges_from(edges)
        adj_matrix = nx.to_numpy_array(G)

        graph = Graph(graphIdx, gNodes, gEdges, adj_matrix, G)
        Graphs.append(graph)
        graph.printInfo()
        # nx.draw(G)
        # plt.show()
    return Graphs


def CheckLinkConstraints(link: MicroserviceLink, path, g: Graph, req: Request):
    msList = req.MsList
    son_msId = link.msLink[1][0]
    son_instId = link.msLink[1][1]
    m = msList[son_msId][son_instId - 1]
    if m.nodeId is None:
        raise Exception(f'Microservice {m.msId} has not been placed.')
    edgeList = g.GetEdgeFromPathNodes(path)
    prop_daley = 0
    for e in edgeList:
        if e.bwUsed + link.bwReq > e.BW:
            return False
        prop_daley += e.propDelay

    delay = m.gamma / link.bwReq + m.procDelay + prop_daley
    if delay <= link.ddl:
        return True
    else:
        return False


def FindLink(req: Request, parent: Microservice, son: Microservice):
    for link in req.MsLinkList:
        if link.msLink == ((parent.msId, parent.instId), (son.msId, son.instId)):
            return link
    return None


def GetKeyNodes(req: Request):
    keyNodes = []
    for msList in req.MsList:
        commonNodeId = msList[0].nodeId
        for ms in msList:
            if ms.nodeId != commonNodeId:
                commonNodeId = None
        if commonNodeId is not None and commonNodeId not in keyNodes:
            keyNodes.append(commonNodeId)
    return keyNodes


def EvaluatePlacementReliability(g: Graph, req: Request):
    if not req.isPlaced:
        return 0
    keyNodes = GetKeyNodes(req)

    # print(keyNodes)
    placeR = 1

    for msLink in req.MsLinkList:
        # link reliability
        tmpR = msLink.R
        # all paths reliability
        if msLink.linkPaths:
            pathTotR = 0
            for path in msLink.linkPaths:
                innerPathR = g.GetInnerPathReliability(path, keyNodes)

                pathTotR = innerPathR + pathTotR - innerPathR * pathTotR

            tmpR *= pathTotR
        elif msLink.linkPaths is None:
            # if msLink.msLink[0][1] == 1 and msLink.msLink[1][1] == 1:
            #     print(f'Req {req.reqId} has not been fully placed. Reason is link {msLink.msLink} is None.')
            tmpR = 0
        msLink.kappa = tmpR
        # print(f' 2. Link: {msLink.msLink} has {len(msLink.linkPaths)} paths, kappa: {tmpR}')

    reliabilityMatrix = np.zeros([len(req.MsList), len(g.nodeList)])
    for msList in req.MsList:
        # print('--------------------')
        # print('ms {msList[0].msId} instance list length: {len(msList)}')
        # print('--------------------')

        for mb in msList:
            parentMsRList = [0.0] * len(req.MsList)
            mb_sigma = mb.R
            for parent in mb.Parents:
                link = FindLink(req, parent, mb)
                tmpR = parentMsRList[parent.msId]

                # print('link kappa: {link.kappa}, tmpR: {tmpR}, R sum: {tmpR + link.kappa - tmpR * link.kappa}')
                parentMsRList[parent.msId] = tmpR + link.kappa - tmpR * link.kappa
                # print('parentMsRList[{parent.msId}]: {parentMsRList[parent.msId]}')

            for parentR in parentMsRList:
                if parentR != 0:
                    mb_sigma *= parentR
            # print(f' ms{mb.msId}({mb.instId}) : {mb_sigma}')
            # mb.sigma = mb_sigma
            value = reliabilityMatrix[mb.msId][mb.nodeId]
            matrixValue = value + mb_sigma - value * mb_sigma
            reliabilityMatrix[mb.msId][mb.nodeId] = matrixValue
            # print(f' 3. ReliabilityMatrix[{mb.msId}][{mb.nodeId}] = {matrixValue}')
    #
    # for i in range(len(req.MsList)):
    #     if len(req.MsList[i]) > 1:
    #         for j in range(len(g.nodeList)):
    #             if j not in keyNodes and reliabilityMatrix[i][j] != 0:
    #                 reliabilityMatrix[i][j] *= g.nodeList[j].R
    # print(f' 3. ReliabilityMatrix[{i}][{j}] = {reliabilityMatrix[i][j]}')
    # print(reliabilityMatrix)
    MsRMatrix = [0] * len(req.MsList)
    for msId in range(len(req.MsList)):
        msSigma = 0
        for nodeR in reliabilityMatrix[msId]:
            nodeId = np.where(reliabilityMatrix[msId])[0][0]
            if nodeId not in keyNodes:
                nodeR *= g.nodeList[nodeId].R
            msSigma = msSigma + nodeR - msSigma * nodeR
        MsRMatrix[msId] = msSigma
    MsRMatrix[0] = req.MsList[0][0].R

    for R in MsRMatrix:
        placeR *= R
    # print(MsRMatrix, 'PlaceR:', placeR)
    for nodeId in keyNodes:
        n = g.nodeList[nodeId]
        placeR *= n.R
        # print(f' node{nodeId}: R: {n.R}, reLow: {n.reLow}, reHigh: {n.reHigh}, cpuUsed/CPU: {n.cpuUsed}/{n.CPU}, '
        #       f' thr: {n.threshold} then placeR = {placeR}')
        # for nMs in n.Microservices:
        #     print(f' m{nMs.msId}({nMs.instId})')
    # print(f'Req {req.reqId}: PR: {placeR}')
    return placeR


def GetMicroserviceQueue(req):
    Q = [req.MsList[0]]
    req.MsList[0][0].inQueue = True
    while True:
        for msList in req.MsList:
            if msList[0].msId == 0:
                continue
            m = msList[0]
            flag = True
            for parent in m.Parents:
                if not parent.inQueue:
                    flag = False
                    break
            if flag:
                Q.append(msList)
                for ms in msList:
                    ms.inQueue = True

        flag = True
        for msList in req.MsList:
            if msList[0].msId == 0:
                continue
            for ms in msList:
                if not ms.inQueue:
                    flag = False
                    break
        if flag:
            break
    Q.remove(req.MsList[0])
    return Q


def ReqIsWorking(g: Graph, req: Request):
    if not req.isPlaced:
        req.isValid = False
        return False
    possibleCombination = []

    for msList in req.MsList:
        idList = []
        for ms in msList:
            if ms.isValid and ms.nodeId is not None and g.nodeList[ms.nodeId].isValid:
                idList.append(ms.instId)
        possibleCombination.append(idList)
    if [] in possibleCombination:
        return False

    out = []
    for idList in possibleCombination:
        nextOut = []
        for instId in idList:
            if len(out) == 0:
                x = [instId]
                nextOut.append(x)
            for j in range(len(out)):
                x = out[j] + [instId]
                nextOut.append(x)
        out = nextOut
    for comb in out:
        FLAG = True
        combTuple = [(i, comb[i]) for i in range(len(comb))]

        for link in req.MsLinkList:
            if FLAG:
                if link.msLink[0] in combTuple and link.msLink[1] in combTuple:
                    if not link.isValid or not g.CheckPathsAvailable(link.linkPaths):
                        FLAG = False
                        break
            else:
                break
        if FLAG:
            req.isValid = True
            return True
    req.isValid = False
    return False


def ClearRequestFromGraph(g: Graph, req: Request):
    for n in g.nodeList:
        for ms in n.Microservices:
            if ms.reqId == req.reqId:
                n.DelMs(ms)
                ms.nodeId = None
    for edge in g.edgeList:
        for link in edge.linkList:
            if link.reqId == req.reqId:
                edge.DelLink(link)
                link.linkPaths = None
    req.isPlaced = False


def UpdateGraphAndReqs(g: Graph, reqList: [Request], t: int):
    for e in g.edgeList:
        e.R = 1.0 / pow(Paras.e, (e.reLambda * t))
    for req in reqList:
        passTime = t - req.arriveTime
        if passTime > req.lifetime:
            ClearRequestFromGraph(g, req)
            continue
        for link in req.MsLinkList:
            link.R = 1.0 / pow(Paras.e, (link.reLambda * passTime))
    for n in g.nodeList:
        for ms in n.Microservices:
            req = reqList[ms.reqId]
            passTime = t - req.arriveTime
            if passTime > req.lifetime:
                ClearRequestFromGraph(g, req)
            else:
                ms.R = 1.0 / pow(Paras.e, (ms.reLambda * passTime))


def UpdateGraphAndReqsAvailability(g: Graph, reqList: [Request]):
    for e in g.edgeList:
        if random.uniform(0, 1) > e.R:
            e.isValid = False
            # print('edge fault')

    for req in reqList:
        for link in req.MsLinkList:
            if random.uniform(0, 1) > link.R:
                link.isValid = False
                # print('link fault', link.R)
    for n in g.nodeList:
        x = random.uniform(0, 1)
        if x > n.R:
            n.isValid = False
            # print('node fault', x,  n.R)
        for ms in n.Microservices:
            if random.uniform(0, 1) > ms.R:
                ms.isValid = False
                # print('ms fault')
