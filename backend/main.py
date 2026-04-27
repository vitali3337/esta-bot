from fastapi import FastAPI
import asyncpg, os

app = FastAPI()
DB = os.getenv("DATABASE_URL")

async def db():
    return await asyncpg.connect(DB)

@app.post("/property")
async def create_property(data: dict):
    conn = await db()

    await conn.execute("""
        INSERT INTO properties (title, price)
        VALUES ($1,$2)
    """, data["title"], data["price"])

    await conn.close()
    return {"ok": True}

@app.get("/properties")
async def get_props():
    conn = await db()
    rows = await conn.fetch("SELECT * FROM properties ORDER BY created_at DESC")
    await conn.close()
    return [dict(r) for r in rows]
