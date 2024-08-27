import Paras
import Tools
from algs import SRP, GRD_B, GRD, RRSP, DAIP
from itertools import *
import Tools
import copy
import numpy as np
import pandas as pd


if __name__ == '__main__':
    repeat_num = 50    # sim times
    node_num = 50
    edge_p = 0.2
    arrive_rate = 1     # x req arrive at 1 time unit
    req_num = 100
    graph_num = 1
    algs = [GRD, GRD_B, RRSP, DAIP, SRP]
    reqArriveIndex = Tools.ReqArriveIndex(req_num, arrive_rate)
    print(reqArriveIndex)
    time = len(reqArriveIndex)
    x_row = []
    for i in range(time):
        x_row.append(i)
    dataTot = np.zeros([time, len(algs)])
    for repeat_round in range(repeat_num):
        print(f' current round: {repeat_round}')
        Graphs, reqList = Tools.Initialization(req_num, node_num, edge_p, graph_num)
        G = Graphs[0]
        print(G.topoGraph)
        algR = []
        for alg in algs:
            reqFaultNum = np.zeros(len(reqList))
            algTotR = 0
            algSuccessReqNUm = 0
            tmpG = copy.deepcopy(G)
            tmpReqList = copy.deepcopy(reqList)
            alg.printName()
            req_id = 0

            for t in range(len(reqArriveIndex)):

                Tools.UpdateGraphAndReqs(tmpG, tmpReqList, t)
                Tools.UpdateGraphAndReqsAvailability(tmpG, tmpReqList)
                for i in range(reqArriveIndex[t]):
                    req = tmpReqList[req_id + i]
                    req.arriveTime = t
                    algResult = alg.run(tmpG, req)
                for req in tmpReqList:
                    placeR = Tools.EvaluatePlacementReliability(tmpG, req)
                    if req.isPlaced and not Tools.ReqIsWorking(tmpG, req):
                        reqFaultNum[req.reqId] = 1

                req_id += reqArriveIndex[t]
                dataTot[t][algs.index(alg)] += sum(reqFaultNum)

    #             dataTot[x_row.index(x)][algs.index(alg)] += sum(algFaultNum)
    dataTot[:, :] /= repeat_num
    print(dataTot)
    #     print(dataTot)
    # df = pd.DataFrame(dataTot)
    # df.to_csv(f'./results/Fault_All_{repeat_num}times_n{node_num}e{edge_p}a{arrive_rate}r{req_num}.csv',
    #           header=False, index=False,  sep=',')
    df = pd.DataFrame(dataTot)
    df.to_csv(f'./results/faultNum_n{node_num}e{edge_p}a{arrive_rate}r{req_num}.csv',
              header=False, index=False,  sep=',')

            # Fig1
    #         dataCut = data[-1][: -1]
    #         print(alg.__name__, tot_success_num)
    #         algIndex = algs.index(alg)
    #         for idx in range(len(dataCut)):
    #             dataTot[idx][algIndex] += dataCut[idx]
    # for i in range(len(dataTot)):
    #     for j in range(len(dataTot[0])):
    #         dataTot[i][j] = dataTot[i][j] / float(repeat_num)
    #
    # dataTot[-1][-1] = time
    # print(dataTot)
    # df = pd.DataFrame(dataTot)
    # df.to_csv(f'./results/All_{repeat_num}times_n{node_num}e{edge_p}a{arrive_rate}r{req_num}.csv',
    #           header=False, index=False,  sep=',')
    # Fig2


