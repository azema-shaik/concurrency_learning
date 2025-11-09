import json
import random
import logging
from dataclasses import dataclass
from datetime import datetime

import aiohttp.web as web 
from faker import Faker 

@dataclass 
class Product:
    uuid: str
    dkuid: str
    name: str
    category: str
    price: float
    currency: str
    stock: int
    sku: str
    manufacturer: str
    release_date: str
    rating: float
    is_active: bool

@dataclass 
class Promo:
    code: str 
    description: str 
    valid_from: str 
    valid_until: str 
    discount_pct: float 

    def json(self):
        return {
            "name": self.code,
            "dicount_pct": self.discount_pct,
            "valid_from": self.valid_from,
            "valid_until": self.valid_until
        }

logging.basicConfig(level = logging.DEBUG)
products = [Product(uuid='a1b2c3d4-e5f6-7890-abcd-ef1234567890',
         dkuid='DK-2024-001',
         name='Wireless Bluetooth Headphones',
         category='Electronics',
         price=79.99,
         currency='USD',
         stock=150,
         sku='WBH-2024-BLK',
         manufacturer='AudioTech',
         release_date='2024-03-15',
         rating=4.5,
         is_active=True),
 Product(uuid='b2c3d4e5-f6a7-8901-bcde-f12345678901',
         dkuid='DK-2024-002',
         name='Smart Fitness Watch',
         category='Wearables',
         price=199.99,
         currency='USD',
         stock=85,
         sku='SFW-2024-SLV',
         manufacturer='FitGear',
         release_date='2024-05-20',
         rating=4.7,
         is_active=True),
 Product(uuid='c3d4e5f6-a7b8-9012-cdef-123456789012',
         dkuid='DK-2024-003',
         name='Portable Power Bank 20000mAh',
         category='Accessories',
         price=34.99,
         currency='USD',
         stock=320,
         sku='PPB-2024-20K',
         manufacturer='ChargePlus',
         release_date='2024-01-10',
         rating=4.3,
         is_active=True),
 Product(uuid='d4e5f6a7-b8c9-0123-def1-234567890123',
         dkuid='DK-2024-004',
         name='4K Ultra HD Webcam',
         category='Electronics',
         price=129.99,
         currency='USD',
         stock=62,
         sku='UHD-2024-4K',
         manufacturer='VisionPro',
         release_date='2024-06-08',
         rating=4.6,
         is_active=True),
 Product(uuid='e5f6a7b8-c9d0-1234-ef12-345678901234',
         dkuid='DK-2024-005',
         name='Mechanical Gaming Keyboard',
         category='Gaming',
         price=89.99,
         currency='USD',
         stock=110,
         sku='MGK-2024-RGB',
         manufacturer='GameMaster',
         release_date='2024-04-12',
         rating=4.8,
         is_active=True),
 Product(uuid='f6a7b8c9-d0e1-2345-f123-456789012345',
         dkuid='DK-2024-006',
         name='Wireless Mouse Ergonomic',
         category='Accessories',
         price=29.99,
         currency='USD',
         stock=275,
         sku='WME-2024-BLK',
         manufacturer='ErgoTech',
         release_date='2024-02-18',
         rating=4.4,
         is_active=True),
 Product(uuid='a7b8c9d0-e1f2-3456-1234-567890123456',
         dkuid='DK-2024-007',
         name='USB-C Hub 7-in-1',
         category='Accessories',
         price=44.99,
         currency='USD',
         stock=190,
         sku='UCH-2024-7IN1',
         manufacturer='ConnectHub',
         release_date='2024-03-25',
         rating=4.2,
         is_active=True),
 Product(uuid='b8c9d0e1-f2a3-4567-2345-678901234567',
         dkuid='DK-2024-008',
         name='LED Ring Light 18 inch',
         category='Photography',
         price=69.99,
         currency='USD',
         stock=98,
         sku='LRL-2024-18',
         manufacturer='LightUp',
         release_date='2024-07-03',
         rating=4.5,
         is_active=True),
 Product(uuid='c9d0e1f2-a3b4-5678-3456-789012345678',
         dkuid='DK-2024-009',
         name='Laptop Stand Aluminum',
         category='Accessories',
         price=39.99,
         currency='USD',
         stock=145,
         sku='LSA-2024-ALU',
         manufacturer='DeskPro',
         release_date='2024-05-30',
         rating=4.6,
         is_active=True),
 Product(uuid='d0e1f2a3-b4c5-6789-4567-890123456789',
         dkuid='DK-2024-010',
         name='Noise Cancelling Earbuds',
         category='Electronics',
         price=149.99,
         currency='USD',
         stock=72,
         sku='NCE-2024-WHT',
         manufacturer='SoundWave',
         release_date='2024-08-14',
         rating=4.7,
         is_active=True)]
sites = ["AMZ","EBY","FLIP","GGLE","META","KIO","APPL","BLNK"]
currency = ['USD', 'EUR', 'GBP', 'JPY', 'INR', 'AUD', 'CAD', 'CHF', 'CNY', 'SEK', 'NZD', 'MXN', 'SGD', 'HKD', 'NOK', 'KRW', 'TRY', 'RUB', 'BRL', 'ZAR', 'DKK', 'PLN', 'THB', 'MYR', 'IDR', 'HUF', 'CZK', 'ILS', 'CLP', 'PHP', 'AED', 'SAR', 'ARS', 'EGP', 'PKR', 'BDT', 'VND', 'NGN', 'UAH', 'RON', 'QAR', 'KWD', 'COP', 'PEN', 'TWD']
agent = ['CHR-001', 'CHR-002', 'FFX-001', 'FFX-002', 'SAF-001', 'SAF-002', 'EDG-001', 'EDG-002', 'OPR-001', 'OPR-002', 'BRV-001', 'BRV-002', 'VVD-001', 'UCB-001', 'SSB-001', 'TOR-001', 'YND-001', 'ARC-001', 'DLP-001', 'MIN-001']
promo = [Promo(code='WELCOME10', description='10% off for new customers', valid_from='2024-01-01', valid_until='2024-12-31', discount_pct=0.1), Promo(code='SAVE20NOW', description='$20 off orders over $100', valid_from='2024-03-01', valid_until='2024-09-30', discount_pct=0.2), Promo(code='FREESHIP', description='Free shipping on all orders', valid_from='2024-01-15', valid_until='2024-12-31', discount_pct=0.0), Promo(code='SUMMER25', description='25% off summer collection', valid_from='2024-06-01', valid_until='2024-08-31', discount_pct=0.25), Promo(code='FLASH50', description='$50 off flash sale', valid_from='2024-09-15', valid_until='2024-09-30', discount_pct=0.5), Promo(code='LOYAL15', description='15% off for loyalty members', valid_from='2024-01-01', valid_until='2025-12-31', discount_pct=0.15), Promo(code='BOGO50', description='Buy one get one 50% off', valid_from='2024-04-01', valid_until='2024-12-31', discount_pct=0.5), Promo(code='BUNDLE30', description='30% off bundle deals', valid_from='2024-02-01', valid_until='2024-11-30', discount_pct=0.3), Promo(code='WEEKEND10', description='$10 off weekend orders', valid_from='2024-01-01', valid_until='2024-12-31', discount_pct=0.1), Promo(code='VIP40', description='40% off VIP exclusive', valid_from='2024-05-01', valid_until='2024-12-31', discount_pct=0.4), Promo(code='EARLY20', description='20% early bird discount', valid_from='2024-03-15', valid_until='2024-06-15', discount_pct=0.2), Promo(code='REFER25', description='$25 referral bonus', valid_from='2024-01-01', valid_until='2025-01-01', discount_pct=0.25), Promo(code='HOLIDAY35', description='35% holiday special', valid_from='2024-11-15', valid_until='2024-12-31', discount_pct=0.35), Promo(code='STUDENT15', description='15% student discount', valid_from='2024-01-01', valid_until='2025-06-30', discount_pct=0.15), Promo(code='CLEARANCE60', description='60% off clearance items', valid_from='2024-07-01', valid_until='2024-09-30', discount_pct=0.6), Promo(code='APP10', description='$10 off mobile app orders', valid_from='2024-02-01', valid_until='2024-12-31', discount_pct=0.1), Promo(code='BIRTHDAY20', description='20% birthday month discount', valid_from='2024-01-01', valid_until='2025-12-31', discount_pct=0.2), Promo(code='SPRING18', description='18% spring refresh sale', valid_from='2024-03-01', valid_until='2024-05-31', discount_pct=0.18), Promo(code='BULK15', description='$15 off bulk orders', valid_from='2024-01-01', valid_until='2024-12-31', discount_pct=0.15), Promo(code='FIRST30', description='30% off first purchase', valid_from='2024-01-01', valid_until='2024-12-31', discount_pct=0.3)]

faker = Faker()
routes = web.RouteTableDef()
app = web.Application()

@routes.get("/")
async def generate(request: web.Request):
    body = []
    for i in range(random.randint(3,8)):
        product = random.choice(products)

        body += [{
            "tick_id": product.uuid, 
            "site_code": random.choice(sites),
            "product_sku": product.sku,
            "ts": faker.date_time_between(datetime(2020,1,1), datetime(2026,12,30)).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "currency": random.choice(currency),
            "stock_qty": random.randint(10,300),
            "promo": random.choice(promo).json(),
            "rating_qty": random.uniform(1.0,5.0),
            "scrape_meta": {"latency": random.uniform(1.0,6.2), "agent": random.choice(agent)}

        }]
    return web.Response(
        body = json.dumps(body),
        headers = {"Content-Type":"application/json"}
    )


app.add_routes(routes)
web.run_app(app, port = 8000)
