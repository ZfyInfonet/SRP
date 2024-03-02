import networkx as nx
import numpy as np


def PlusR(a, b):
    return a + b - a * b


class Graph:
    def __init__(self, graph_id, node_list, edge_list, adj_matrix, g: nx.Graph):
        self.graphId = graph_id
        self.nodeList = node_list
        self.edgeList = edge_list
        self.adjMatrix = adj_matrix
        self.pathRMatrix = None
        self.topoGraph = g

    def printInfo(self):
        print(f'Graph {self.graphId}: node: {len(self.nodeList)}, '
              f'edge: {len(self.edgeList)} \nInternallyDisjointPathRMatrix: \n{self.pathRMatrix}')

    def FindAllPaths(self, nodeId1, nodeId2, maxNum):
        num = 0
        paths = []
        for path in nx.all_simple_paths(self.topoGraph, nodeId1, nodeId2):
            paths.append(path)
            num += 1
            if num == maxNum:
                break
        return paths

    def FindShortestPaths(self, nodeId1, nodeId2, maxNum):
        num = 0
        paths = []
        for path in nx.all_shortest_paths(self.topoGraph, nodeId1, nodeId2):
            paths.append(path)
            num += 1
            if num == maxNum:
                break
        return paths

    def FindDisjointPaths(self, nodeId1, nodeId2, maxNum, maxLength=None):
        paths = []
        for path in nx.node_disjoint_paths(self.topoGraph, nodeId1, nodeId2, cutoff=maxNum):
            paths.append(path)
        if maxLength is None:
            return paths
        else:
            newPaths = []
            for path in paths:
                if len(path) - 1 <= maxLength:
                    newPaths.append(path)
            return newPaths

    def UpdatePathRMatrix(self, k):
        node_num = len(self.nodeList)
        PRM = np.zeros((node_num, node_num))
        for i in range(node_num):
            for j in range(node_num):
                if i == j:
                    PRM[i, j] = 1
                elif i > j:
                    PRM[i, j] = PRM[j, i]
                else:
                    paths = self.FindDisjointPaths(i, j, k)
                    pathEdgesList = [self.GetEdgeFromPathNodes(path) for path in paths]
                    totR = 0
                    for pathNum in range(len(paths)):
                        path = paths[pathNum]
                        pathEdges = pathEdgesList[pathNum]
                        pathR = 1
                        path.remove(path[-1])  # src and dst reliabilities are useless.
                        path.remove(path[0])
                        for pathNodeId in path:
                            nodeR = self.nodeList[pathNodeId].R
                            pathR *= nodeR
                        for E in pathEdges:
                            pathR *= E.R
                        totR = PlusR(totR, pathR)
                    PRM[i, j] = totR
        self.pathRMatrix = PRM
        return PRM

    def GetEdgeFromPathNodes(self, node_id_list):
        pathEdges = []
        for i in range(len(node_id_list) - 1):
            node = self.nodeList[node_id_list[i]]
            next_nodeId = node_id_list[i + 1]
            for E in node.edgeList:
                if next_nodeId in E.ends:
                    pathEdges.append(E)
                    break
        return pathEdges

    def GetInnerPathReliability(self, path, singlePlacedNodes):
        if len(path) < 2:
            return 1
        R = 1
        for i in range(len(path) - 1):
            if i != 0 and path[i] not in singlePlacedNodes:
                R *= self.nodeList[path[i]].R
            node = self.nodeList[path[i]]
            next_nodeId = path[i + 1]
            for E in node.edgeList:
                if next_nodeId in E.ends:
                    R *= E.R
                    break
        return R

    def CheckPathsAvailable(self, paths):
        if paths is None:
            return False
        elif len(paths) == 0:
            return True
        isWork = False
        for path in paths:
            isPathWork = True
            for i in range(len(path) - 1):
                node = self.nodeList[path[i]]
                if not node.isValid:
                    isPathWork = False
                next_nodeId = path[i + 1]
                for E in node.edgeList:
                    if next_nodeId in E.ends:
                        if not E.isValid:
                            isPathWork = False
                        break
                if not isPathWork:
                    break
            if isPathWork:
                isWork = True
                break
        return isWork
