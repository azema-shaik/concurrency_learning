import asyncio 
from logger import get_logger, LogColors 

logger = get_logger("queues_learn",color_mapping = {
    'producer': LogColors.DARK_BLUE,
    'worker': LogColors.YELLOW}, file_name = r"C:\Users\shaik\learning\concurrency\python_concurrency\logs\queues_l.log")

async def producer(q: asyncio.Queue):
    while True:
        t = await q.get()
        if t is True:
            break


async def worker(id: int, q: asyncio.Queue):
    for i in range(5):
        logger.debug(f'Put: {i}')
        await q.put(i)
        logger.debug(f'Put Completed putting item: "{i}"')
    await q.put(True)



async def main(q):
    
    await asyncio.gather(
        worker(1,q), producer(q)
    )
q = asyncio.Queue(maxsize = 2)
asyncio.run(main(q))