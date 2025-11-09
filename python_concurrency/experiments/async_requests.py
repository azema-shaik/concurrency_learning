import time
import asyncio 
import aiohttp

from logger import get_logger, LogColors

STOP = object()
logger = get_logger("async_requests_compare", color_mapping = {'req':LogColors.YELLOW, 'launcher': LogColors.RED},
                    file_name = r"C:\Users\shaik\learning\concurrency\python_concurrency\logs\async_requests_l.log", fh = True)

async def req(id: int, jobs: asyncio.Queue):
    async with aiohttp.ClientSession() as session:
        while True:
            job = await jobs.get()

            if job is STOP:
                logger.info(F'Worker: {id} recievd signal to STOP')
                return 
            logger.info(f'WOrker iD: {id}; {job}')
            async with session.get(f'http://localhost:8000/{job}',params = {"src":"async"}) as resp:
                logger.info(f'{job} sent request from worker id {id}')
                print(await resp.text())

async def launcher(jobs: asyncio.Queue, nWorkers: int):
    for job in range(5000+1):
        logger.info(f'JOB ID: {job}')
        await jobs.put(job)
    for _ in range(nWorkers):
        await jobs.put(STOP)

async def main():
    n_workers = 5
    jobs = asyncio.Queue(maxsize = 20)

    t1 = time.perf_counter()
    await asyncio.gather(
        launcher(jobs, n_workers), *(req(id, jobs) for id in range(n_workers))
    )
    print(f'Completed by {(time.perf_counter() - t1)/60} minute(s)')



asyncio.run(main())