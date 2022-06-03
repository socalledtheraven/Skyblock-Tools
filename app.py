from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi_utils.tasks import repeat_every
from typing import Optional
from pydantic import BaseModel
from pyinstrument import Profiler
import main, uvicorn, asyncio, json, uuid, datetime, logging
mylist = []
with open("database.json", "r") as database:
  db = json.load(database)
  temp_db = db
  
description = """
The Skyblock Tools api tries to put all information a hypixel dev using the api would need at their fingertips

## Items

Provides an interface to **see all data about all items, data for a specific item or specific data generally.**

Contact me at quintbrit#5857 if you need help or run into an error!
"""

tags_metadata = [
  {
    "name": "items",
    "description": "Operations dealing with ✧･ﾟindividual items✧･ﾟ",
  },
  {
    "name": "constants",
    "description": "Constant lists of things, such as what items are auctionable.",
  },
  {
    "name": "player",
    "description": "Adding utilities for players and profiles",
  },
  {
    "name": "simplified",
    "description": "Simplifying complex endpoints for dev use",
  },
]

logging.basicConfig(filename='latest.log', filemode='w+', format='%(asctime)s: [%(levelname)s] %(message)s', datefmt='%d-%b-%y %H:%M:%S')

app = FastAPI(
  title="Skyblock Tools",
  description=description,
  version="0.0.1",
  openapi_tags=tags_metadata,
  license_info={
    "name": "GNU General Public License v3.0",
    "url": "https://choosealicense.com/licenses/gpl-3.0/",
  },
)

class Items(BaseModel):
  item: dict

class Item(BaseModel):
  recipe: Optional[str] = None
  craft_cost: Optional[float] = None
  ingredients: Optional[dict] = None
  name: Optional[str] = None
  id: Optional[str] = None
  image_link: Optional[str] = None
  npc_salable: Optional[bool] = None
  bazaarable: Optional[bool] = None
  auctionable: Optional[bool] = None
  pretty_craft_requirements: Optional[str] = None
  craftable: Optional[bool] = None
  lore: Optional[list] = None
  deformatted_lore: Optional[str] = None
  forgable: Optional[bool] = None
  npc_sell_price: Optional[float] = None
  bazaar_buy_price: Optional[float] = None
  bazaar_sell_price: Optional[float] = None
  bazaar_profit: Optional[float] = None
  bazaar_percentage_profit: Optional[float] = None
  craft_profit: Optional[float] = None
  craft_percentage_profit: Optional[float] = None
  pretty_use_requirements: Optional[str] = None
  pretty_duration: Optional[str] = None
  duration: Optional[int] = None
  forge_cost: Optional[float] = None
  forge_profit: Optional[float] = None
  forge_percentage_profit: Optional[float] = None
  forge_profit_per_hour: Optional[float] = None
  
class Recipe(BaseModel):
  recipe: str
  ingredients: dict

class Bins(BaseModel):
  lowest: float
  second_lowest: float

class BazaarItem(BaseModel):
  buy: float
  sell: float
  profit: float
  percentage_profit: float

class Price(BaseModel):
  buy: Optional[float] = None
  sell: Optional[float] = None
  profit: Optional[float] = None
  percentage_profit: Optional[float] = None
  lowest_bin: Optional[float] = None
  second_lowest_bin: Optional[float] = None
  lowest_auction: Optional[float] = None
  second_lowest_auction: Optional[float] = None
  lowest_zero_bid_auction: Optional[float] = None
  lowest_zero_bid_ending_soon_auction: Optional[float] = None

class ForgeItem(BaseModel):
  cost: float
  profit: float
  duration: int
  pretty_duration: str
  profit_per_hour: float
  percentage_profit: float
  recipe: str
  ingredients: dict

class Auction:
  uuid: uuid.UUID
  auctioneer: uuid.UUID
  profile_id: uuid.UUID
  coop: list
  start: datetime.date
  end: datetime.date
  item_name: str
  item_lore: str
  extra: str
  category: str
  tier: str
  starting_bid: float
  item_bytes: bytes
  claimed: bool
  claimed_bidders: list
  highest_bid_amount: float
  last_updated: datetime.date
  bin: bool
  bids: list
  item_uuid: uuid.UUID

@app.get("/", include_in_schema=False)
async def home():
  return RedirectResponse("/docs")
  
@app.get("/api/items/", tags=["items"])
async def items():
  return db
  
@app.get("/api/item/{item}/", tags=["items"])
async def item(item: str):
  return db[item]
  
@app.get("/api/item/{item}/name/", tags=["items"])
async def name(item: str):
  return db[item]["name"]

@app.get("/api/item/{item}/recipe/", tags=["items"])
async def recipe(item: str):
  if db[item]["craftable"] or db[item]["forgable"]:
    return {"recipe": db[item]["recipe"], "ingredients": db[item]["ingredients"]}
  else:
    return {"craftable": db[item]["craftable"], "forgable": db[item]["forgable"]}
  
@app.get("/api/item/{item}/lowest_bin/", tags=["items"])
async def lowest_bin(item: str):
  if db[item]["auctionable"]:
    return {"lowest": db[item]["lowest_bin"], "second_lowest": db[item]["second_lowest_bin"]}
  else:
    return {"auctionable": db[item]["auctionable"]}
    
@app.get("/api/item/{item}/auctions/", tags=["items"])
async def item_auctions(item: str):
  auctions = await main.get_auctions()
  auctions = [d for d in auctions if main.remove_formatting(main.name_to_id(d["item_name"])) == item]
  return auctions

@app.get("/api/item/{item}/bazaar/", tags=["items"])
async def bazaar(item: str):
  if db[item]["bazaarable"]:
    return {"buy": db[item]["bazaar_buy_price"], "sell": db[item]["bazaar_sell_price"], "profit": db[item]["bazaar_profit"], "%profit": db[item]["bazaar_percentage_profit"]}
  else:
    return {"bazaarable": db[item]["bazaarable"]}
  
@app.get("/api/item/{item}/price/", tags=["items"])
async def price(item: str):
  if db[item]["bazaarable"]:
    return {"buy": db[item]["bazaar_buy_price"], "sell": db[item]["bazaar_sell_price"], "profit": db[item]["bazaar_profit"], "%profit": db[item]["bazaar_percentage_profit"]}
  elif db[item]["auctionable"]:
    return {"lowest_bin": db[item]["lowest_bin"], "second_lowest_bin": db[item]["second_lowest_bin"], "lowest_auction": db[item]["lowest_auction"], "second_lowest_auction": db[item]["second_lowest_auction"], "lowest_zero_bid_auction": db[item]["lowest_zero_bid_auction"], "lowest_zero_bid_ending_soon_auction": db[item]["lowest_zero_bid_ending_soon_auction"]}
  elif db[item]["npc_salable"]:
    return {"sell": db[item]["npc_sell_price"]}
  else:
    return {"value": "N/A"}

@app.get("/api/item/{item}/forge/", tags=["items"])
async def forge(item: str):
  if db[item]["forgable"]:
    return {"cost": db[item]["forge_cost"], "profit": db[item]["forge_profit"], "duration": db[item]["duration"], "pretty_duration": db[item]["pretty_duration"], "profit_per_hour": db[item]["forge_profit_per_hour"], "%profit": db[item]["forge_percentage_profit"], "recipe": db[item]["recipe"], "ingredients": db[item]["ingredients"]}
  else:
    return {"forgable": db[item]["forgable"]}

@app.get("/api/bazaarables/", tags=["constants"])
async def bazaarables():
  bazaarables = [item for item in db if db[item]["bazaarable"]]
  return bazaarables
  
@app.get("/api/auctionables/", tags=["constants"])
async def auctionables():
  auctionables = [item for item in db if db[item]["auctionable"]]
  return auctionables
  
@app.get("/api/craftables/", tags=["constants"])
async def craftables():
  craftables = [item for item in db if db[item]["craftable"]]
  return craftables

@app.get("/api/forgables/", tags=["constants"])
async def forgables():
  forgables = [item for item in db if db[item]["forgable"]]
  return forgables

@app.get("/api/auctions", tags=["simplified"])
async def auctions(page: int = 0):
  auctions = await main.get_auctions()
  auctions = list(main.chunks(auctions, 5000))
  return auctions[page]

@app.on_event("startup")
@repeat_every(seconds=30, logger=logging.Logger)
async def dynamic_database_updater_task():
  print("dynamic")
  db = await main.dynamic_database_updater(temp_db)

@app.on_event("startup")
@repeat_every(seconds=60*10, wait_first=True, logger=logging.Logger)
async def static_database_updater_task():
  print("static")
  db = await main.static_database_updater(temp_db)

if __name__ == "__main__":
  uvicorn.run(app, host='0.0.0.0', debug=True, port=8080)