#!/usr/bin/env python3
"""
ESTA · Parser
Парсер makler.md и 999.md → PostgreSQL
Запуск каждые 30 минут
"""

import asyncio
import asyncpg
import aiohttp
import os
import logging
import hashlib
from datetime import datetime
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

DATABASE_URL = os.environ.get("DATABASE_URL")

CITY_MAP = {
    "тирасполь": 3, "tiraspol": 3,
    "бендеры": 4, "bender": 4, "tighina": 4,
    "рыбница": 5, "ribnita": 5,
    "дубоссары": 6, "dubasari": 6,
    "кишинёв": 1, "chisinau": 1, "кишинев": 1,
    "бельцы": 2, "balti": 2,
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

async def get_db():
    return await asyncpg.connect(DATABASE_URL)

def make_external_id(source, url):
    return f"{source}_{hashlib.md5(url.encode()).hexdigest()[:12]}"

def detect_city(text):
    text = text.lower()
    for key, city_id in CITY_MAP.items():
        if key in text:
            return city_id
    return 1

def parse_price(text):
    if not text:
        return None, "USD"
    text = text.strip()
    currency = "USD"
    if "€" in text or "eur" in text.lower():
        currency = "EUR"
    elif "lei" in text.lower() or "лей" in text.lower() or "mdl" in text.lower():
        currency = "MDL"
    digits = "".join(c for c in text if c.isdigit())
    return (float(digits) if digits else None), currency

async def parse_makler(session, db):
    """Парсер makler.md"""
    categories = [
        ("https://makler.md/ru/real-estate/apartments/sell/", "apartment", "sale"),
        ("https://makler.md/ru/real-estate/apartments/rent/", "apartment", "rent"),
        ("https://makler.md/ru/real-estate/houses/sell/",    "house",     "sale"),
        ("https://makler.md/ru/real-estate/commercial/sell/","commercial","sale"),
        ("https://makler.md/ru/real-estate/garages/sell/",   "garage",    "sale"),
    ]
    count = 0
    for url, prop_type, deal_type in categories:
        try:
            async with session.get(url, headers=HEADERS, timeout=aiohttp.ClientTimeout(total=20)) as resp:
                if resp.status != 200:
                    continue
                html = await resp.text()
            soup = BeautifulSoup(html, "lxml")
            items = soup.select(".announcement-block, .listing-item, article.item")
            for item in items[:20]:
                try:
                    title_el = item.select_one("h2, h3, .title, .announcement-title")
                    price_el = item.select_one(".price, .cost, .announcement-price")
                    link_el  = item.select_one("a[href]")
                    loc_el   = item.select_one(".location, .city, .address")

                    title = title_el.get_text(strip=True) if title_el else ""
                    price_text = price_el.get_text(strip=True) if price_el else ""
                    link  = link_el["href"] if link_el else url
                    if not link.startswith("http"):
                        link = "https://makler.md" + link
                    location = loc_el.get_text(strip=True) if loc_el else ""

                    price, currency = parse_price(price_text)
                    if not price or not title:
                        continue

                    ext_id  = make_external_id("makler", link)
                    city_id = detect_city(location + " " + title)

                    existing = await db.fetchval(
                        "SELECT id FROM properties WHERE external_id=$1", ext_id
                    )
                    if existing:
                        continue

                    rates = {"USD": 1.0, "EUR": 1.08, "MDL": 0.056}
                    price_usd = round(price * rates.get(currency, 1.0), 2)

                    await db.execute("""
                        INSERT INTO properties
                        (external_id, source, deal_type, property_type, city_id,
                         title, price, currency, price_usd, source_url, is_active)
                        VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,TRUE)
                    """, ext_id, "makler", deal_type, prop_type, city_id,
                        title, price, currency, price_usd, link)
                    count += 1
                except Exception as e:
                    logger.debug(f"Item error: {e}")
        except Exception as e:
            logger.warning(f"Makler category error {url}: {e}")
    logger.info(f"Makler: добавлено {count} объявлений")
    return count

async def parse_999(session, db):
    """Парсер 999.md"""
    categories = [
        ("https://999.md/ru/list/real-estate/apartments-and-rooms",    "apartment", "sale"),
        ("https://999.md/ru/list/real-estate/apartments-and-rooms?s%5Brent%5D=1", "apartment", "rent"),
        ("https://999.md/ru/list/real-estate/houses-and-dachas",       "house",     "sale"),
        ("https://999.md/ru/list/real-estate/commercial-real-estate",  "commercial","sale"),
        ("https://999.md/ru/list/real-estate/garages-and-parking",     "garage",    "sale"),
    ]
    count = 0
    for url, prop_type, deal_type in categories:
        try:
            async with session.get(url, headers=HEADERS, timeout=aiohttp.ClientTimeout(total=20)) as resp:
                if resp.status != 200:
                    continue
                html = await resp.text()
            soup = BeautifulSoup(html, "lxml")
            items = soup.select(".ads-list-photo-item, .js-item, li.ads-list-photo-item")
            for item in items[:20]:
                try:
                    title_el = item.select_one(".ads-list-photo-item-title, h2, h3")
                    price_el = item.select_one(".ads-list-photo-item-price, .price")
                    link_el  = item.select_one("a[href]")
                    loc_el   = item.select_one(".ads-list-photo-item-description, .location")

                    title = title_el.get_text(strip=True) if title_el else ""
                    price_text = price_el.get_text(strip=True) if price_el else ""
                    link  = link_el["href"] if link_el else url
                    if not link.startswith("http"):
                        link = "https://999.md" + link
                    location = loc_el.get_text(strip=True) if loc_el else ""

                    price, currency = parse_price(price_text)
                    if not price or not title:
                        continue

                    ext_id  = make_external_id("999md", link)
                    city_id = detect_city(location + " " + title)

                    existing = await db.fetchval(
                        "SELECT id FROM properties WHERE external_id=$1", ext_id
                    )
                    if existing:
                        continue

                    rates = {"USD": 1.0, "EUR": 1.08, "MDL": 0.056}
                    price_usd = round(price * rates.get(currency, 1.0), 2)

                    await db.execute("""
                        INSERT INTO properties
                        (external_id, source, deal_type, property_type, city_id,
                         title, price, currency, price_usd, source_url, is_active)
                        VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,TRUE)
                    """, ext_id, "999md", deal_type, prop_type, city_id,
                        title, price, currency, price_usd, link)
                    count += 1
                except Exception as e:
                    logger.debug(f"Item error: {e}")
        except Exception as e:
            logger.warning(f"999md category error {url}: {e}")
    logger.info(f"999.md: добавлено {count} объявлений")
    return count

async def run_parser():
    logger.info("Запуск парсера ESTA...")
    db = await get_db()
    async with aiohttp.ClientSession() as session:
        c1 = await parse_makler(session, db)
        c2 = await parse_999(session, db)
        logger.info(f"Итого добавлено: {c1 + c2} объявлений")
    await db.close()

async def main():
    while True:
        try:
            await run_parser()
        except Exception as e:
            logger.error(f"Ошибка парсера: {e}")
        logger.info("Следующий запуск через 30 минут...")
        await asyncio.sleep(1800)

if __name__ == "__main__":
    asyncio.run(main())
