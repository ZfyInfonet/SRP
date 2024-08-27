import Paras
import Tools
import math
from algs import SRP, GRD_B, GRD, RRSP, DAIP, SRP_S
from itertools import *
import Tools
import copy
import numpy as np
import pandas as pd


repeat_num = 20    # sim times
node_num = 50
edge_p = 0.2
arrive_rate = 1     # x req arrive at 1 time unit
req_num = 100
graph_num = 1
isFullBackup = True    # req backup limit = req ms number when True
ifChangeTopo = False
fig_x_num = 101     # Fig 1 coordinate axis x number

algs = [GRD, GRD_B, RRSP, DAIP, SRP, SRP_S]

reqArriveIndex = Tools.ReqArriveIndex(req_num, arrive_rate)
print(reqArriveIndex)
time = len(reqArriveIndex)
bwUsedList = [[0] * time,[0] * time,[0] * time,[0] * time,[0] * time, [0] * time, [0] * time]

x_row = []
for i in range(time):
    x_row.append(i)
dataPlacementR = np.zeros([req_num, len(algs)])
dataPlacementNum = np.zeros([req_num, len(algs)])
dataFaultNum = np.zeros([time, len(algs)])
for repeat_round in range(repeat_num):
    print(f' current round: {repeat_round}')
    Graphs, reqList = Tools.Initialization(req_num, node_num, edge_p, graph_num, isFullBackup, ifChangeTopo)
    G = Graphs[0]
    print(G.topoGraph)
    algR = []
    for alg in algs:
        reqFaultNum = np.zeros(len(reqList))
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
                placeR = Tools.EvaluatePlacementReliability(tmpG, req)
                dataPlacementR[req.reqId][algs.index(alg)] += placeR
                if placeR > 0.01:
                    dataPlacementNum[req.reqId][algs.index(alg)] += 1

            for req in tmpReqList:

                isWork = Tools.ReqIsWorking(tmpG, req)
                if req.isPlaced and not isWork:
                    reqFaultNum[req.reqId] = 1

            req_id += reqArriveIndex[t]

            dataFaultNum[t][algs.index(alg)] += sum(reqFaultNum)
            for edge in tmpG.edgeList:
                bwUsedList[algs.index(alg)][t] += edge.bwUsed


for bwList in bwUsedList:
    for bwUsed in bwList:
        bwUsedList[bwUsedList.index(bwList)][bwList.index(bwUsed)] /= repeat_num




dataPlacementR[:, :] /= dataPlacementNum[:, :]
dataFaultNum[:, :] /= repeat_num
dataPlacementR[np.isnan(dataPlacementR)] = 0.0
print(dataPlacementR)
print(dataFaultNum)
minR = np.amin(dataPlacementR[dataPlacementR > 0.01])
maxR = np.amax(dataPlacementR)
interval = maxR - minR
print(minR, maxR)
last_x = minR
dataPlacementR_new = np.zeros([fig_x_num, len(algs) + 2])

for x in range(fig_x_num):
    if x == 0:
        std = minR
    elif x == fig_x_num - 1:
        std = maxR + 0.001
    else:
        interval = (maxR - last_x) / 4
        std = last_x + interval

    dataPlacementR_new[x, 0] = x
    dataPlacementR_new[x, -1] = std
    for i in range(req_num):
        for j in range(len(algs)):
            if dataPlacementR[i, j] < std:
                dataPlacementR_new[x, j + 1] += 1
    last_x = std

df_1 = pd.DataFrame(dataPlacementR_new)
df_1.to_csv(f'./results/fig2overall_CDF.csv',
            header=False, index=False, sep=',')
df_2 = pd.DataFrame(dataFaultNum)
df_2.to_csv(f'./results/fig2overall_n{node_num}e{edge_p}a{arrive_rate}r{req_num}.csv',
            header=False, index=False, sep=',')
df_3 = pd.DataFrame(bwUsedList)
df_3.to_csv(f'./results/fig2overall_BW.csv',
            header=False, index=False, sep=',')
