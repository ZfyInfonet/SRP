import pandas as pd
import numpy as np

import winreg

key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders')
desktop = winreg.QueryValueEx(key, "Desktop")[0]

# 读取CSV文件
df1 = pd.read_csv('./results/BW.csv', header=None)
df2 = pd.read_csv(desktop + '\\ReliabilitySim_sharedlink\\results\\BW.csv', header=None)
# 显示数据
fully_data = df1.values.tolist()
shared_data = df2.values.tolist()

fig_data = [fully_data[0], fully_data[1], fully_data[2],fully_data[3],fully_data[4], shared_data[4], shared_data[5]]
minLen = 999999
for data in fig_data:
    if len(data) < minLen:
        minLen = len(data)
    for i in range(len(data)):
        fig_data[fig_data.index(data)][i] /= 100
for data in fig_data:
    if len(data) > minLen:
        fig_data[fig_data.index(data)] = data[: minLen]

x_row = [i for i in range(minLen)]

final_fig = np.zeros([8, len(x_row)])
for i in range(len(x_row)):
    final_fig[0, i] = i
for x in range(7):
    for y in range(minLen):
        final_fig[x + 1, y] = fig_data[x][y]

data1 = fig_data[4]
data2 = fig_data[6]
max_idx = 0
max_v = 0
for i in range(minLen):
    diff = data1[i] - data2[i]
    if diff > max_v:
        max_v = diff
        max_idx = i

print(max_idx, data1[max_idx], data2[max_idx])

array = np.array(final_fig)
array = np.transpose(array)
df = pd.DataFrame(array)

df.to_csv(f'./results/figRc.csv', header=False, index=False, sep=',')

df_x = pd.read_csv('./results/figRc.csv', header=None)