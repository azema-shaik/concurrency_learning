import asyncio
import pathlib
from experiments.tasks import task_factory,init_logger
from experiments.logger import LogColors, get_logger


log_file = pathlib.Path(__file__).parents[0] / 'logs'/'another.log'
logger = get_logger("understanding tasks",color_mapping={"first": LogColors.PINK,"second":LogColors.DARK_BLUE},
                    fh = True, file_name=log_file)
async def rresult():
    logger.info({"msg":"rresult will sleep .1 second and return 9"})
    await asyncio.sleep(.1)
    logger.info({"msg": "sending 9 as result."})
    return 9

async def another():
    logger.info("=========== ANOTHER Will fetch resul=============")
    result = await rresult()
    logger.info({"msg":f"================ GOT RESULT {result}"})

async def first():
    logger.info("======== FIRST.FIRST Will sleep next for .4 seconds ===================")
    await asyncio.sleep(4)
    logger.info('========= FIRST.SECOND Will sleep next for .3 seconds=========================')
    await asyncio.sleep(.3)
    logger.info('=========================== FIRST.THIRD No sleep=================')
    # await asyncio.sleep(.10)
    logger.info('========== END ===========')

# async def second():
#     logger.info("======== SECOND.FIRST Will sleep for .5 seconds===================")
#     await asyncio.sleep(.5)
#     logger.info('========= SECOND.SECOND Will sleep for 0 second=========================')
#     await asyncio.sleep(0)
#     logger.info('=========================== SECOND.THIRD No sleep=================')
#     # await asyncio.sleep(.10)
#     logger.info('========== END ===========')

# async def third():
#     logger.info("======== SECOND.FIRST ===================")
#     await asyncio.sleep(.5)
#     logger.info('========= SECOND.SECOND =========================')
#     await asyncio.sleep(0)
#     logger.info('=========================== SECOND.THIRD =================')
#     await asyncio.sleep(.10)
#     logger.info('========== END ===========')

# async def noawait():
#     logger.info("================== no awaits =============")
async def main():
    logger.info("Main function calling")
    loop = asyncio.get_event_loop()
    init_logger(logger)
    loop.set_task_factory(task_factory)
    
    await asyncio.gather(another())#first(),second())#,third())
    

asyncio.run(main())