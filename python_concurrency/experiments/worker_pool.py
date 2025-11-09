from dataclasses import dataclass 
from datetime import datetime
import asyncio 
import json 
import time
import aiohttp 
import aiofiles
from logger import get_logger, LogColors 

logger = get_logger(
    "worker_pool", color_mapping = {
        'fetch': LogColors.PINK,
        'worker': LogColors.YELLOW,'launcher': LogColors.GREEN,'consolidater': LogColors.RED
    }, file_name = r"C:\Users\shaik\learning\concurrency\python_concurrency\logs\worker_pool_3.log", fh = True, filemode='w'
)

    
@dataclass 
class Job:
    id: int 
    result: str  = None


async def fetch():
    logger.debug('Fetch generator called')
    async with aiohttp.ClientSession() as session:
        num = None 
        while True:
            logger.info(f'Fetching for {num}')
            
            if num is None:
                logger.info('Fetch primed')
                num = yield 
            logger.info(f"URL: https://xkcd.com/{num}/info.0.json")
            async with session.get(f"http://localhost:8000/{num}") as resp:
                num = yield (await resp.json() if resp.status != 404 else {})

async def worker(id: int, jobs: asyncio.Queue, consolidate: asyncio.Queue):

    logger.debug(f'Worker id: {id} launched,{jobs}')
    
    src = fetch()
    await src.asend(None)

    logger.info(f'Worker id: {id}; src geneator initalized and primed')
    logger.info(f'Worker id: {id}; jobs and stop tasks created.')
    iter_ = 0
    while True:
        iter_ += 1
        logger.info(f'TASKS STATE: Worker ID: {id}, ITER: {iter_}')
        # async for earliest_connect in as_completed(tasks)

        req = await jobs.get()
        # for task in done_tasks:
        #     if  task is stop_task:
        #         logger.info(f'Worker id: {id}; received signal to STOP')
        #         await src.aclose()
        #         await stop.put(True)
        #         return 
        if req is None:
            logger.info(f'Worker: {id} CLOSED_STOPPED')
            await consolidate.put(None)
            await jobs.put(None)
            return  
            
        # req: Job = task.result()
        # logger.info(f'Worker id: {id}; receievd {req!r},{req.id} Request to process')
        req.result = await src.asend(req.id)
        logger.info(f'Worker id: {id}; receieved result from src req.{req.id} JOB ID')
        await consolidate.put(req)
        logger.info(f'Worker id: {id}; put req in consolidate.{req.id} JOB ID')
        logger.info(f'-------------------------------------------- {req.id} ------------------------------------------')
        



async def consolidater(consolidate: asyncio.Queue, nWorkers):
    logger.debug("Consolidator received")
    all_jobs_fetched = False
    none_seen = 0
    async with aiofiles.open("test.jsonl",'w', encoding = "utf-8") as file:
        while none_seen != nWorkers:
            logger.info(f'Queue size: {len(consolidate._queue)}')
            req: Job|None = await consolidate.get()
            if req is None:
                none_seen += 1
                continue

            
            
                


   
               
                
            
            
                
            logger.info(f'Consolidate for Job ID: {req.id}')
            logger.info(f"Consolodator received from {req} from job.; Will await on req.result and then write it to file")
            dct = req.result
            dct["job_id"] = req.id
            await file.write(json.dumps(dct)+'\n')
            logger.info(f'-------------------------------------------------------- {req.id} ---------------------------------------------')

        
            
                
async def launcher(job: asyncio.Queue, stop: asyncio.Queue):
    logger.info("Launcher launched")
    for job_id in range(3140+1):
        logger.info(f'Job ID: {job_id}')
        await job.put(Job(id = job_id))

    logger.info(f'Sending Stop signal on Stop.')
    await job.put(None)
    logger.info(f'Sent Stop signal on Stop.')


async def main():
    t1 = time.perf_counter()
    n_workers = 5
    stop = asyncio.Queue(maxsize=1)
    jobs = asyncio.Queue(maxsize = 30)
    consolidate = asyncio.Queue()
    logger.info(f"WOrkers; {n_workers}, Jobs: 41")

    await asyncio.gather(
        launcher(jobs, stop), consolidater(consolidate, n_workers), *(worker(id, jobs, consolidate) for id in range(1, n_workers+1))
    )
    logger.info(f"Completed at {time.perf_counter() - t1:.2f} Seconds")

asyncio.run(main())

