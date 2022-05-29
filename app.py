from fastapi import FastAPI
from typing import Optional
from pydantic import BaseModel
import main, uvicorn
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
    return {**db[item]["recipe"], **db[item]["ingredients"]}
  else:
    return {**db[item]["craftable"], **db[item]["forgable"]}
  
@app.get("/api/item/{item}/lowest_bin")
async def lowest_bin(item):
  if db[item]["auctionable"]:
    return {**db[item]["lowest_bin"], **db[item]["second_lowest_bin"]}
  else:
    return {**db[item]["auctionable"]}

@app.get("/api/item/{item}/bazaar")
async def bazaar(item):
  if db[item]["bazaarable"]:
    return {**db[item]["bazaar_buy_price"], **db[item]["bazaar_sell_price"], **db[item]["bazaar_profit"], **db[item]["bazaar_percentage_profit"]}
  else:
    return {**db[item]["bazaarable"]}
    
@app.get("/api/item/{item}/price")
async def price(item):
  if db[item]["bazaarable"]:
    return {**db[item]["bazaar_buy_price"], **db[item]["bazaar_sell_price"], **db[item]["bazaar_profit"], **db[item]["bazaar_percentage_profit"]}
  elif db[item]["auctionable"]:
    return {**db[item]["lowest_bin"], **db[item]["second_lowest_bin"], **db[item]["lowest_auction"], **db[item]["second_lowest_auction"], **db[item]["lowest_zero_bid_auction"], **db[item]["lowest_zero_bid_ending_soon_auction"]}
  elif db[item]["npc_salable"]:
    return {**db[item]["npc_sell_price"]}
  else:
    return ["N/A"]

@app.get("/api/item/{item}/forge")
async def forge(item):
  if db[item]["forgable"]:
    return {**db[item]["forge_cost"], **db[item]["forge_profit"], **db[item]["duration"], **db[item]["forge_profit_per_hour"], **db[item]["forge_percentage_profit"], **db[item]["recipe"], **db[item]["ingredients"]}
  else:
    return {**db[item]["forgable"]}

if __name__ == "__main__":
  uvicorn.run(app, host='0.0.0.0', debug=True, port=8080)