import Paras
import Tools
import math
from algs import SRP, GRD_B, GRD, RRSP, DAIP, Optimal, SRP_S
from itertools import *
from datetime import datetime
import Tools
import copy
import numpy as np
import pandas as pd

repeat_num = 500  # sim times
node_num = 10
low_node_num = 10
edge_p = 1
arrive_rate = 1  # x req arrive at 1 time unit
req_num = 1
graph_num = 1
isFullBackup = False  # req backup limit = req ms number when True
ifChangeTopo = True
x_num = 101  # Fig 1 coordinate axis x number
Axis_granularity = 100
algs = [GRD, GRD_B, RRSP, DAIP, SRP, SRP_S, Optimal]

time = 1

bwUsedList = [[0] * time] * len(algs)
x_row = []
for i in range(time):
    x_row.append(i)

dataPlacementR = np.zeros([req_num, len(algs)])
dataPlacementNum = np.zeros([req_num, len(algs)])
dataFaultNum = np.zeros([time, len(algs)])
for repeat_round in range(repeat_num):
    init_time = datetime.now()
    print(f' current round: {repeat_round}')
    G, reqList = Tools.SingleInitialization(req_num, node_num, edge_p, isFullBackup, ifChangeTopo, low_node_num)
    print(G.topoGraph)
    algR = []
    for alg in algs:
        reqFaultNum = np.zeros(len(reqList))
        tmpG = copy.deepcopy(G)
        tmpReqList = copy.deepcopy(reqList)
        alg.printName()
        req_id = 0

        for t in range(1):
            print(f' time: {t}')
            Tools.UpdateGraphAndReqs(tmpG, tmpReqList, t)
            Tools.UpdateGraphAndReqsAvailability(tmpG, tmpReqList)

            for i in range(1):
                req = tmpReqList[req_id + i]
                req.arriveTime = t
                algResult = alg.run(tmpG, req)
                placeR = Tools.EvaluatePlacementReliability(tmpG, req)
                for tempNode in tmpG.nodeList:
                    print(f'node: {tempNode.nodeId}, reliability:{tempNode.R}, microservice:{tempNode.MicroservicesIdList}')
                print(f'Reliability: {placeR}')
                dataPlacementR[req.reqId][algs.index(alg)] += placeR
                if placeR > 0.01:
                    dataPlacementNum[req.reqId][algs.index(alg)] += 1

            for req in tmpReqList:

                isWork = Tools.ReqIsWorking(tmpG, req)
                # print(f' alg: {alg} req: {req.reqId}, is placed: {req.isPlaced}, is worked: {isWork}')
                if req.isPlaced and not isWork:
                    reqFaultNum[req.reqId] = 1

            dataFaultNum[t][algs.index(alg)] += sum(reqFaultNum)
            for edge in tmpG.edgeList:
                bwUsedList[algs.index(alg)][t] += edge.bwUsed
    over_time = datetime.now()
    print(f'one round time: {(over_time-init_time).total_seconds()}s')


for bwList in bwUsedList:
    for bwUsed in bwList:
        bwUsedList[bwUsedList.index(bwList)][bwList.index(bwUsed)] /= repeat_num

dataPlacementR[:, :] /= dataPlacementNum[:, :]
dataFaultNum[:, :] /= repeat_num
dataPlacementR[np.isnan(dataPlacementR)] = 0.0
dataOptimalR = np.average(dataPlacementR, axis=0)

minR = np.amin(dataPlacementR[dataPlacementR > 0.01])
maxR = np.amax(dataPlacementR)
interval = maxR - minR
last_x = minR
dataPlacementR_new = np.zeros([x_num, len(algs) + 2])

for x in range(x_num):
    if x == 0:
        std = minR
    elif x == x_num - 1:
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
df_2 = pd.DataFrame(dataFaultNum)
df_3 = pd.DataFrame(dataOptimalR)
df_1.to_csv(f'./results/figOptimal_CDF.csv', header=False, index=False, sep=',')
df_2.to_csv(f'./results/figOptimal.csv', header=False, index=False, sep=',')
df_3.to_csv(f'./results/figOptimal_Avr.csv', header=False, index=False, sep=',')
