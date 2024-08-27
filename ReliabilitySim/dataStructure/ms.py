class Microservice:
    def __init__(self, req_id, ms_id, inst_id, cpu, reLambda, gamma, proc_delay):
        self.reqId = req_id
        self.msId = ms_id
        self.instId = inst_id
        self.cpuReq = cpu
        self.reLambda = reLambda
        self.isValid = True
        self.gamma = gamma
        self.procDelay = proc_delay
        self.Parents = []
        self.Sons = []
        self.nodeId = None
        self.R = 0.99
        self.banedNodes = []
        self.sigma = 0
        self.inQueue = False
        self.isWork = True
