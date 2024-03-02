import Paras
import Tools
from algs import PRP, GRD_B, GRD, RRSP, DAIP
from itertools import *
import Tools
import copy
import numpy as np
import pandas as pd
a = [1]
b = [1,2,3]
c = [1, 2]
f = [1, 2]
d = [b, c, f]
out = [[1]]
nextOut = [[1]]
print(6666)
for mnlist in d:
    nextOut = []
    print(out)
    for id in mnlist:
        print(id)
        for j in range(len(out)):
            x = out[j] + [id]
            nextOut.append(x)
    out = nextOut
print(nextOut)
