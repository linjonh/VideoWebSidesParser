
import asyncio


async def test():
    arr=[printStr(f"test str {i}") for i in range(0,20)]
    asyncio.gather(*arr)

async def printStr(testStr):
    asyncio.sleep(1)
    print(testStr)
    
# asyncio.run(test())

x=1338 /60
print(f"{x:.2f}")

x=[1,2,3]
print(x[:-1])

