import asyncio 
import random
from logger import Logger, LogColors

logger = Logger("events", file_name = r'C:\Users\shaik\learning\concurrency\python_concurrency\logs\events.log',
                fh = True, filemode = 'w')


@logger.register(LogColors.DARK_BLUE)
async def wait(id: int,event: asyncio.Event):
    logger.info(f"Event ID:{id}")
    iter = 0
    while True:
        if event.is_set():
            iter += 1
            logger.info(f"Event ID: {id} set waiting, iteration: {iter}")

        else:
            logger.info(f"Event ID: {id} is cleared breaking")
            break 
        await asyncio.sleep(.5)
    logger.info(f"Event ID: {id} exited")

@logger.register(LogColors.PURPLE)
async def launch(event: asyncio.Event):
    logger.info(f"Launcher will launch evnts after an evnt i set")
    iter = 0
    while True:
        if not event.is_set():
            iter += 1
            logger.info(f"Doing an important job and waiting for an event")
        else:
            logger.info(f"Event cleared launching events")
            break 
        await asyncio.sleep(3)
    await asyncio.gather(*(wait(i,event) for i in range(5)), event_wait(event))

    


@logger.register(LogColors.TURQUOISE)
async def event_set(event: asyncio.Event):
    sleep = random.randint(2,9)
    logger.info(f"Evnet will be set after {sleep}")
    await asyncio.sleep(sleep)
    event.set()
    logger.info(f"Evenr is set")

    
@logger.register(LogColors.GREEN)
async def event_wait(event: asyncio.Event):
    sleep = random.randint(9,30)
    logger.info(f"Will sleep after {sleep} second(s)")
    await asyncio.sleep(sleep) 
    logger.info(f"Event will be cleared")
    event.clear()       


@logger.register(LogColors.YELLOW)
async def main():
    event = asyncio.Event()
    
    await asyncio.gather(launch(event), event_set(event))

    
    

asyncio.run(main())