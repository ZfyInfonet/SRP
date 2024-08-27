# ---topo---
access_node_ratio = 0.2

# ---microservice---
c_ms = 1
ms_cpuReq_range = [0.1 * c_ms, 1 * c_ms]  # CPU
ms_gamma_range = [0.1, 5]  # MB
ms_delay_range = [0.01, 0.05]  # s    propagation delay limit, since processing delay and sending delay are fixed.

# ---microservice link---
c_link = 1
msLink_bwReq_range = [0.1 * c_link, 10 * c_link]     # [0.1 * c_link, 10 * c_link]  # MBps
msLink_ddl_range = [0.01, 0.1]  # s

# ---node---
node_cpu_range = [8, 16]    # CPU [8, 16]
node_threshold_range = [0.5, 0.5]

# ---edge---
edge_bw_range = [100, 1000]     # MBps [100, 1000]
edge_delay_range = [0.001, 0.01]  # s
edge_shared_ratio = 2
path_max_num = 3

# ---request---
lifetime_range = [1, 100]    # s
ms_num_range = [1, 5]

# ---reliability---
c_fault = 0.001
node_reLow_range = [1 - c_fault, 1 - 0.1 * c_fault]     # [0.99, 0.999]
node_reHigh_range = [1 - 0.1 * c_fault, 1 - 0.01 * c_fault]

c_r = 0.00001
ms_lambda_range = [c_r, c_r]
msLink_lambda_range = [c_r, c_r]
edge_lambda_range = [c_r, c_r]

# ---natural constant---
e = 2.71828

