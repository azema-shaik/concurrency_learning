import uuid
import json
import random
from datetime import datetime
import asyncio
import aiohttp 
import asyncpg

from logger import Logger, LogColors 

logger = Logger(name = "root", file_name = r"C:\Users\shaik\learning\concurrency\python_concurrency\logs\events_l.py",
                fh = True )

class DB:
    def __init__(self, user, password, database):
        self.user = user
        self.password = password
        self.database = database   
        self.event = asyncio.Event()

    @logger.register(LogColors.DARK_BLUE)
    async def __aenter__(self):
        self.conn = await asyncpg.connect(user = self.user, password = self.password, database = self.database) 
        logger.info(f"Connection extablished")
        return self
    
    async def set(self):
        await asyncio.sleep(random.randint(5*60, 9*60))
        self.event.set()
        await asyncio.sleep(random.randint(15,30) * 60)
        self.event.clear()


    @logger.register(LogColors.DARK_BLUE)
    async def execute(self, stmt, vals):
        if not self.event.is_set():
            return False 
        
        await self.conn.execute(stmt, vals)
        logger.info(f"stmt: {stmt}; vals = {vals}")
        return True

        

    @logger.register(LogColors.DARK_BLUE)
    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.conn.close()
        logger.info("Connection closed")

@logger.register(LogColors.YELLOW)
async def fetch(queue: asyncio.Queue):
    async with aiohttp.ClientSession() as session:
        async with session.get("http://localhost:8000") as resp:
            await resp.json()

@logger.register(LogColors.GREEN)
async def write()

async def main():
    conn = await 
    results = await fetch()
    result = results[0]
    await conn.execute("""INSERT INTO event(tick_id, site_code, product_sku, ts,currency, 
                     promo, stock_qty, rating_avg, scrape_meta) VALUES 
                    ($1, $2, $3, $4, $5, $6, $7, $8, $9)""",
                    uuid.UUID(result["tick_id"]),
                    result["site_code"],
                    result["product_sku"],
                    datetime.strptime(result["ts"],"%Y-%m-%dT%H:%M:%SZ"),
                    result["currency"],
                    json.dumps(result["promo"]),
                    result["stock_qty"],
                    result["rating_qty"],
                    json.dumps(result["scrape_meta"])
                    )
    await conn.close()


asyncio.run(main())