import random,string,os


def _encode_decimal62(num):
    chars = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJELMNOPQRSTUVWXYZ"
    base = len(chars)
    string = ""
    while True:
        string = chars[num % base] + string
        num = num // base
        if num == 0:
            break
    return string

def _crypto(src, key):
    if src and key:
        xor_code = key
        while len(src) > len(xor_code):
            xor_code += key
        if not(len(src) == len(xor_code)):
            xor_code=xor_code[0:len(src)]
        return int(xor_code)^int(src)

def create_inv(base):
    if base > 999:
        base = base % 999
    return _encode_decimal62(_crypto("".join(random.choices(string.digits, k=8))+str(base).zfill(3),os.environ.get("XOR_KEY")))



if __name__ == "__main__":
#環境変数XOR_KEYに自然数をSET
#6~7桁
    for i in range(0,10):
        print(create_inv(1))