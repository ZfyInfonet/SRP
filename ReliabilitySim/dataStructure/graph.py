import networkx as nx
import numpy as np
import Paras


def PlusR(a, b):
    return a + b - a * b


def CalculateDisjointPathMatrix(g: nx.Graph):
    n_num = g.number_of_nodes()
    disjoint_paths = np.array([[None for _ in range(n_num)] for _ in range(n_num)], dtype=list)
    for i in range(n_num):
        for j in range(n_num):
            paths = list(nx.node_disjoint_paths(g, i, j, cutoff=Paras.path_max_num))
            disjoint_paths[i, j] = paths
    return disjoint_paths


class Graph:
    def __init__(self, graph_id, node_list, edge_list, adj_matrix, g: nx.Graph):
        self.graphId = graph_id
        self.nodeList = node_list
        self.edgeList = edge_list
        self.adjMatrix = adj_matrix
        self.pathRMatrix = None
        self.topoGraph = g
        self.disjointPaths = CalculateDisjointPathMatrix(g)

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

    def FindDisjointPaths(self, nodeId1, nodeId2, maxNum):
        disjoint_paths = self.disjointPaths[nodeId1, nodeId2]
        paths = []
        for i in range(maxNum):
            if i < len(disjoint_paths):
                paths.append(disjoint_paths[i])
            else:
                break
        return paths

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

    def GetInnerPathReliability(self, path, keyNodes):
        if len(path) < 2:
            return 1
        R = 1
        for i in range(len(path) - 1):
            if i != 0 and path[i] not in keyNodes:
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
