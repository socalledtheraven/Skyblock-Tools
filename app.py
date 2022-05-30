from fastapi import FastAPI
from typing import Optional
from pydantic import BaseModel
import main, uvicorn, asyncio
db = main.db

app = FastAPI()

class Item(BaseModel):
  name: str

@app.get("/api/items")
async def items():
  return db
  
@app.get("/api/item/{item}")
async def item(item):
  return db[item]
  
@app.get("/api/item/{item}/name")
async def name(item):
  return db[item]["name"]

@app.get("/api/item/{item}/recipe")
async def recipe(item):
  if db[item]["craftable"] or db[item]["forgable"]:
    return {"recipe": db[item]["recipe"], "ingredients": db[item]["ingredients"]}
  else:
    return {"craftable": db[item]["craftable"], "forgable": db[item]["forgable"]}
  
@app.get("/api/item/{item}/lowest_bin")
async def lowest_bin(item):
  if db[item]["auctionable"]:
    return {"lowest": db[item]["lowest_bin"], "second_lowest": db[item]["second_lowest_bin"]}
  else:
    return {"auctionable": db[item]["auctionable"]}

@app.get("/api/item/{item}/bazaar")
async def bazaar(item):
  if db[item]["bazaarable"]:
    return {"buy": db[item]["bazaar_buy_price"], "sell": db[item]["bazaar_sell_price"], "profit": db[item]["bazaar_profit"], "%profit": db[item]["bazaar_percentage_profit"]}
  else:
    return {"bazaarable": db[item]["bazaarable"]}
    
@app.get("/api/item/{item}/price")
async def price(item):
  if db[item]["bazaarable"]:
    return {"buy": db[item]["bazaar_buy_price"], "sell": db[item]["bazaar_sell_price"], "profit": db[item]["bazaar_profit"], "%profit": db[item]["bazaar_percentage_profit"]}
  elif db[item]["auctionable"]:
    return {"lowest": db[item]["lowest_bin"], "second_lowest": db[item]["second_lowest_bin"], "lowest_auction": db[item]["lowest_auction"], "second_lowest_auction": db[item]["second_lowest_auction"], "lowest_zero_bid": db[item]["lowest_zero_bid_auction"], "lowest_zero_bid_ending_soon": db[item]["lowest_zero_bid_ending_soon_auction"]}
  elif db[item]["npc_salable"]:
    return {"sell": db[item]["npc_sell_price"]}
  else:
    return ["N/A"]

@app.get("/api/item/{item}/forge")
async def forge(item):
  if db[item]["forgable"]:
    return {"cost": db[item]["forge_cost"], "profit": db[item]["forge_profit"], "duration": db[item]["duration"], "pretty_duration": db[item]["pretty_duration"], "profit_per_hour": db[item]["forge_profit_per_hour"], "%profit": db[item]["forge_percentage_profit"], "recipe": db[item]["recipe"], "ingredients": db[item]["ingredients"]}
  else:
    return {"forgable": db[item]["forgable"]}

if __name__ == "__main__":
  uvicorn.run(app, host='0.0.0.0', debug=True, port=8080)

while True:
  asyncio.run(main.static_database_updater())
  asyncio.sleep(50)

while True:
  asyncio.run(main.dynamic_database_updater())
  asyncio.sleep(10)