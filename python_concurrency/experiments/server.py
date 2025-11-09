import  uuid 
import random
import json 
import logging
import asyncio
from datetime import datetime 


import aiohttp.web as web 
from logger import LogColors, Logger, LogLevel 


tasks = {}
routes = web.RouteTableDef()
logger = Logger("root", fh = True, file_name = r"C:\Users\shaik\learning\concurrency\python_concurrency\logs\server.py")
logging.basicConfig(level = LogLevel.DEBUG.value)
app = web.Application()
lock = asyncio.Lock()

@routes.post("/batch/")
@logger.register(LogColors.YELLOW)
async def batch_request(request: web.Request):
    req_id = f'{uuid.uuid4()}'
    
    async with lock:
        logger.debug(f'lock acquired by batch_request to process request id: {req_id!r}')
        tasks[req_id] = {"created_at": (created_at := datetime.now()),
                     "process_time": (process_time := random.randint(4,8))}
    
    logger.debug(f'lock released by batch_request for request id: {req_id}')
    return web.Response(
        body = json.dumps(
            {"id":req_id,"created_at": created_at.timestamp(), 'process_time': process_time}
        ), status = 202
    )


@routes.post("/status/{id}/")
@logger.register(LogColors.GREEN)
async def batch_response(request: web.Request):
    req_id = request.match_info["id"]
    logger.info(f"{req_id!r} queried!")

    async with lock:
        logger.debug(f'batch_response acquired lock')
        item = tasks.get(req_id)

    if item is None:
        raise web.HTTPNotFound(body = json.dumps({"status":"not_found"}))
    if (datetime.now() - item["created_at"]).seconds > item["process_time"]:
        async with lock:
            logger.debug('batch_response acquired lock again')
            tasks.pop(req_id)
        return web.Response(body = json.dumps(
            {"status": "complete", "req_id": req_id}
        ), status = 200)
    else:
        
        return web.Response(body = json.dumps({"status":"pending"}), status = 200)

    
app.add_routes(routes)
web.run_app(app, port = 8000)
