
def dec_to_n(x, n):
    result = ""
    while x > 0:
        a = x % n
        result = result + str(a)
        x = x // n
    return result[::-1]

n_num = 10
m_num = 3
search_space = n_num ** m_num

print(bin(1023), type(bin(1023)))