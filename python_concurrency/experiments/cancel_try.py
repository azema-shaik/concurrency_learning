import asyncio 

async def task():
    await asyncio.sleep(.9)
    print("TASK")

async def canceller(task):
    print("taks cancl")
    task.cancel()
    print("completed  cancle sleep for .2")
    await asyncio.sleep(.3)

async def main():
    t1 = asyncio.create_task(task())
    t2 = asyncio.create_task(canceller(t1))

    print(await asyncio.wait([t1,t2], return_when = 'FIRST_EXCEPTION'))

asyncio.run(main())