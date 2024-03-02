import Paras
import Tools
from algs import PRP, GRD_B, GRD, RRSP, DAIP
from itertools import *
import Tools
import copy
import numpy as np
import pandas as pd


if __name__ == '__main__':
    repeat_num = 1    # sim times
    node_num = 40
    edge_p = 0.2
    arrive_rate = 1     # x req arrive at 1 time unit
    req_num = 1
    graph_num = 1
    c_ms = -3
    algs = [GRD, GRD_B, RRSP, DAIP, PRP]
    reqArriveIndex = Tools.ReqArriveIndex(req_num, arrive_rate)
    print(reqArriveIndex)
    dataTot = np.zeros([6, len(algs)])
    time = len(reqArriveIndex)
    for mag in range(6):
        c_ms += 4
        Paras.c_ms = c_ms
        Paras.ms_cpuReq_range = [0.1 * c_ms, 1 * c_ms]

        print(Paras.c_ms, Paras.ms_cpuReq_range)
        for repeat_round in range(repeat_num):
            print(f' current round: {repeat_round}')
            Graphs, reqList = Tools.Initialization(req_num, node_num, edge_p, graph_num)
            G = Graphs[0]
            print(G.topoGraph)
            algR = []
            for alg in algs:
                algTotR = 0
                algSuccessReqNUm = 0
                tmpG = copy.deepcopy(G)
                tmpReqList = copy.deepcopy(reqList)
                alg.printName()
                req_id = 0
                data = np.zeros([req_num + 1, len(reqArriveIndex) + 1])     # [ ....+ averageR]
                tot_success_num = 0
                for t in range(len(reqArriveIndex)):
                    totR_t, available_req_num = 0.0, 0
                    Tools.UpdateGraphAndReqs(tmpG, tmpReqList, t)
                    for i in range(reqArriveIndex[t]):
                        req = tmpReqList[req_id + i]
                        req.arriveTime = t
                        algResult = alg.run(tmpG, req)
                        if req.isPlaced:
                            tot_success_num += 1
                    for req in tmpReqList:
                        isWork = Tools.ReqIsWorking(tmpG, req)
                        print(f' req {req.reqId} is working? : {isWork}')
                        placeR = Tools.EvaluatePlacementReliability(tmpG, req)
                        data[req.reqId, t] = placeR
                        if placeR > 0.01:
                            totR_t += placeR
                            available_req_num += 1
                    if available_req_num != 0:
                        data[-1, t] = totR_t / available_req_num
                    req_id += reqArriveIndex[t]

                data[data < 0.001] = np.nan
                for i in range(req_num):
                    data[:, -1] = np.nanmean(data[i])
                data[np.isnan(data)] = 0
                data[req_num, len(reqArriveIndex)] = tot_success_num
                dataCut = data[0: req_num, -1]
                dataCut[dataCut < 0.001] = np.nan
                reqAvrR = np.nanmean(dataCut)
                if np.isnan(reqAvrR):
                    reqAvrR = 0
                dataCut[np.isnan(dataCut)] = 0
                dataTot[mag][algs.index(alg)] += reqAvrR
        dataTot[mag, :] /= repeat_num
        print(dataTot)

    Paras.c_ms = 1
    Paras.ms_cpuReq_range = [0.1, 1]
    df = pd.DataFrame(dataTot)
    df.to_csv(f'./results/MsCPU_All_{repeat_num}times_n{node_num}e{edge_p}a{arrive_rate}r{req_num}.csv',
              header=False, index=False,  sep=',')
            # algR.append((algTotR, algSuccessReqNUm, algTotR / algSuccessReqNUm))
            # print(data)
            # df = pd.DataFrame(data)
            # df.to_csv(f'./results/n{node_num}e{edge_p}a{arrive_rate}r{req_num}_{alg.__name__}.csv',
            #           header=False, index=False,  sep=',')
            # print(data[-1])
            #
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


