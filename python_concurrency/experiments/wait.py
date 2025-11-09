import random
import asyncio 

from logger import get_logger, LogColors 

logger = get_logger(
    'wait_for', color_mapping = {
        "worker": LogColors.CYAN
    }, file_name = rf'C:\Users\shaik\learning\concurrency\python_concurrency\logs\wait_for.py'
)

async def worker(id):
    sleep_time = round(random.uniform(.1, .5),1)
    logger.debug(f'{id}; sleep_time: {sleep_time}')
    await asyncio.sleep(sleep_time)
    logger.debug(f'{id} COMPLETED')


async def with_loop(awaitables: list[asyncio.Task]):
    
    iterations = 0
    completed = set()
    while True:
        iterations += 1
        if not awaitables:
            break
        logger.debug(f'[{iterations}] [Awaitbales = {"| ".join(aws.get_name() for aws in awaitables)}]')
        done, pending = await asyncio.wait(awaitables, timeout = .2)
        logger.debug(f'[{iterations}] [Done = {"| ".join(aws.get_name() for aws in done)!r}]')
        awaitables = pending
        completed |= {(aws.get_name(), iterations) for aws in done}
    
    logger.error(f'{sorted(completed, key = lambda x:x[1]) = !r}')

async def without_loop(aws: list[asyncio.Task]):
    logger.debug(f'[Awaitbales = {"| ".join(aw.get_name() for aw in aws)}]')
    done, pending = await asyncio.wait(aws, timeout = .6,return_when = 'FIRST_COMPLETED')
    logger.debug(f'[Done = {"| ".join(aw.get_name() for aw in done)!r}]')
    logger.debug(f'[Awaitbales = {"| ".join(aw.get_name() for aw in aws)}]')

async def main(func: callable):
    nWorkers = random.randint(6,9)
    logger.debug(f'"{nWorkers}" to be launched.')
    awaitables: list[asyncio.Task] = [asyncio.create_task(worker(i), name = f'worker - {i}') for i in range(1,nWorkers+1)]
    await func(awaitables)
asyncio.run(main(without_loop))