import asyncio
import pathlib
from experiments.tasks import task_factory
from experiments.logger import LogColors, get_logger


log_file = pathlib.Path(__file__).parents[0] / 'logs'/'tasks_one_aysn_one_await.log'
logger = get_logger("understanding tasks",color_mapping={"first": LogColors.PINK,"second":LogColors.DARK_BLUE},
                    fh = True, file_name=log_file)
async def first():
    logger.info("======== FIRST.FIRST ===================")
    await asyncio.sleep(4)
    # logger.info('========= FIRST.SECOND =========================')
    # await asyncio.sleep(.3)
    # logger.info('=========================== FIRST.THIRD =================')
    # await asyncio.sleep(.10)
    logger.info('========== END ===========')

async def second():
    logger.info("======== SECOND.FIRST ===================")
    await asyncio.sleep(.5)
    logger.info('========= SECOND.SECOND =========================')
    await asyncio.sleep(0)
    logger.info('=========================== SECOND.THIRD =================')
    await asyncio.sleep(.10)
    logger.info('========== END ===========')


async def main():
    logger.info("Main function calling")
    loop = asyncio.get_event_loop()
    task_factory.__file_path__ = log_file
    loop.set_task_factory(task_factory)
    await asyncio.gather(first())

asyncio.run(main())