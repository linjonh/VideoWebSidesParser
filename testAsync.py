import asyncio

from MyLog import log


async def test():
    arr = [printStr(f"test str {i}") for i in range(0, 20)]
    asyncio.gather(*arr)


async def printStr(testStr):
    asyncio.sleep(1)
    print(testStr)


# asyncio.run(test())

x = 1338 / 60
print(f"{x:.2f}")

x = [1, 2, 3]
print(x[:-1])

try:
    int("abc")  # 无法转换字符串为整数
except Exception as e:
    log(e)

br = "\n".encode()
end=len("\n")
print(str(br))
print(end)

#############
# file = open("./videoInfo.json", "+rb")
# file2 = open("./videoInfo2.json", "+w")

# # for i in list:
# #     find=i.find()
# #     print(find)
    
# find=0
# linestr=""
# while(find!=-1):
#     line = file.read()
#     find=line.find("\n".encode())
#     a=line.replace("\n".encode(),"".encode())
#     linestr+=a.decode()
#     break
# file2.write(linestr)
# file.close()
# file2.close()
# print(linestr)

##### 
a=1234
b=2
print(f"number={a:5}")
print(f"number={b:5}")

name = "Alice"
print(f"name={name:10}")  # 左对齐，宽度 10
