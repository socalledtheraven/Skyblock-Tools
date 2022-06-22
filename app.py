from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.concurrency import run_in_threadpool
from fastapi_utils.tasks import repeat_every
from scout_apm.api import Config
from scout_apm.async_.starlette import ScoutMiddleware
from typing import Optional, Dict, List
from pydantic import BaseModel, HttpUrl
import main
import uvicorn
import asyncio
import json
import uuid
import datetime
import logging
import aiofiles
  
description = """
The Skyblock Tools api tries to put all information a hypixel dev using the api would need at their fingertips
## Items
Provides an interface to **see all data about all items, data for a specific item or specific data generally.**
Create an issue on github (https://github.com/QuintBrit/Skyblock-Tools/issues) if you need help or run into an error!
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
    "name": "simplified",
    "description": "Simplifying complex endpoints for dev use",
  },
]

logging.basicConfig(filename='latest.log', filemode='w+', format='%(asctime)s: [%(levelname)s] %(message)s', datefmt='%d-%b-%y %H:%M:%S')

Config.set(
  name="Skyblock Tools - API"
)

app = FastAPI(
  title="Skyblock Tools",
  description=description,
  version="1.0.1",
  openapi_tags=tags_metadata,
  license_info={
    "name": "GNU General Public License v3.0",
    "url": "https://choosealicense.com/licenses/gpl-3.0/",
  },
)

app.add_middleware(ScoutMiddleware)

class Item(BaseModel):
  recipe: Optional[str] = ""
  craft_cost: Optional[float] = 0
  ingredients: Optional[dict] = {}
  name: Optional[str] = ""
  id: Optional[str] = ""
  image_link: Optional[HttpUrl] = None
  npc_salable: Optional[bool] = False
  bazaarable: Optional[bool] = False
  auctionable: Optional[bool] = False
  pretty_craft_requirements: Optional[str] = ""
  craftable: Optional[bool] = False
  lore: Optional[list] = []
  deformatted_lore: Optional[str] = ""
  forgable: Optional[bool] = False
  npc_sell_price: Optional[float] = 0
  bazaar_buy_price: Optional[float] = 0
  bazaar_sell_price: Optional[float] = 0
  bazaar_profit: Optional[float] = 0
  bazaar_percentage_profit: Optional[float] = 0
  craft_profit: Optional[float] = 0
  craft_percentage_profit: Optional[float] = 0
  pretty_use_requirements: Optional[str] = ""
  pretty_duration: Optional[str] = ""
  duration: Optional[int] = 0
  forge_cost: Optional[float] = 0
  forge_profit: Optional[float] = 0
  forge_percentage_profit: Optional[float] = 0
  forge_profit_per_hour: Optional[float] = 0
  lowest_bin: Optional[float] = 0
  second_lowest_bin: Optional[float] = 0
  lowest_auction: Optional[float] = 0
  second_lowest_auction: Optional[float] = 0
  lowest_zero_bid_auction: Optional[float] = 0
  lowest_zero_bid_ending_soon_auction: Optional[float] = 0

class Items(BaseModel):
  __root__: Dict[str, Item]

class Name(BaseModel):
  id: str
  name: str

class Recipe(BaseModel):
  recipe: Optional[str] = ""
  ingredients: Optional[dict] = {}

class Bins(BaseModel):
  lowest: Optional[float] = 0
  second_lowest: Optional[float] = 0
  
class BazaarItem(BaseModel):
  buy: Optional[float] = 0
  sell: Optional[float] = 0
  profit: Optional[float] = 0
  percentage_profit: Optional[float] = 0
  
class Price(BaseModel):
  buy: Optional[float] = 0 
  sell: Optional[float] = 0
  profit: Optional[float] = 0
  percentage_profit: Optional[float] = 0
  
class ForgeItem(BaseModel):
  cost: Optional[float] = 0
  profit: Optional[float] = 0 
  duration: Optional[int] = 0
  pretty_duration: Optional[str] = ""
  profit_per_hour: Optional[float] = 0
  percentage_profit: Optional[float] = 0
  recipe: Optional[str] = ""
  ingredients: Optional[dict] = {}
  
class Auction(BaseModel):
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
  
class Auctions(BaseModel):
  auctions: List[Auction]
  
@app.get("/", include_in_schema=False)
async def home():
  return RedirectResponse("/docs")
  
@app.get("/items/items/", tags=["items"], response_model=Items)
async def items() -> Items:
  return db
  
@app.get("/items/item/{item}/", tags=["items"], response_model=Item)
async def item(item: str) -> Item:
  return db[item]
  
@app.get("/items/item/{item}/name/", tags=["items"], response_model=Name)
async def name(item: str) -> Name:
  return Name(id=item, name=db[item]["name"])
  
@app.get("/items/item/{item}/recipe/", tags=["items"], response_model=Recipe)
async def recipe(item: str) -> Recipe:
  if db[item]["craftable"] or db[item]["forgable"]:
    return Recipe(recipe=db[item]["recipe"], ingredients=db[item]["ingredients"])
  else:
    return {"craftable": False, "forgable": False}
  
@app.get("/items/item/{item}/lowest_bin/", tags=["items"], response_model=Bins)
async def lowest_bin(item: str) -> Bins:
  if db[item].get("auctionable") == True:
    return Bins(lowest=db[item]["lowest_bin"], second_lowest=db[item]["second_lowest_bin"])
  else:
    return {"auctionable": False}
    
@app.get("/items/item/{item}/auctions/", tags=["items"], response_model=Auctions)
async def item_auctions(item: str):
  auctions = await main.get_auctions()
  auctions = [d for d in auctions if d["id"] == item]
  return auctions
  
@app.get("/items/item/{item}/bazaar/", tags=["items"], response_model=BazaarItem)
async def bazaar(item: str):
  if db[item].get("bazaarable") == True:
    return BazaarItem(buy=db[item]["bazaar_buy_price"], sell=db[item]["bazaar_sell_price"], profit=db[item]["bazaar_profit"], percentage_profit=db[item]["bazaar_percentage_profit"])
  else:
    return {"bazaarable": False}
  
@app.get("/items/item/{item}/price/", tags=["items"], response_model=Price)
async def price(item: str):
  if db[item].get("bazaarable") == True:
    return Price(buy=db[item]["bazaar_buy_price"], sell=db[item]["bazaar_sell_price"], profit=db[item]["bazaar_profit"], percentage_profit=db[item]["bazaar_percentage_profit"])
  elif db[item].get("auctionable") == True:
    return Price(buy=db[item]["lowest_bin"], sell=db[item]["second_lowest_bin"], profit=db[item]["bin_flip_profit"], percentage_profit=db[item]["bin_flip_percentage_profit"])
  elif db[item].get("npc_salable") == True:
    return Price(sell=db[item]["npc_sell_price"])
  else:
    return {"unsellable": True}
    
@app.get("/items/item/{item}/forge/", tags=["items"], response_model=ForgeItem)
async def forge(item: str):
  if db[item].get("forgable") == True:
    return ForgeItem(cost=db[item]["forge_cost"], profit=db[item]["forge_profit"], duration=db[item]["duration"], pretty_duration=db[item]["pretty_duration"], profit_per_hour=db[item]["forge_profit_per_hour"], percentage_profit=db[item]["forge_percentage_profit"], recipe=db[item]["recipe"], ingredients=db[item]["ingredients"])
  else:
    return {"forgable": False}
    
@app.get("/constants/bazaarables/", tags=["constants"], response_model=list)
async def bazaarables():
  bazaarables = [item for item in db if db[item]["bazaarable"]]
  return bazaarables
  
@app.get("/constants/auctionables/", tags=["constants"], response_model=list)
async def auctionables():
  auctionables = [item for item in db if db[item]["auctionable"]]
  return auctionables
  
@app.get("/constants/craftables/", tags=["constants"], response_model=list)
async def craftables():
  craftables = [item for item in db if db[item]["craftable"]]
  return craftables
  
@app.get("/constants/forgables/", tags=["constants"], response_model=list)
async def forgables():
  forgables = [item for item in db if db[item]["forgable"]]
  return forgables
  
@app.get("/simplified/auctions", tags=["simplified"], response_model=Auctions)
async def auctions(page: int = 0):
  auctions = await main.get_auctions()
  auctions = list(main.chunks(auctions, 5000))
  return auctions[page]
  
@app.on_event("startup")
async def load_db():
  global db
  async with aiofiles.open("database.json", "r") as database:
    database = await database.read()
    db = json.loads(database)
    
@app.on_event("startup")
@repeat_every(seconds=30, logger=logging.Logger)
async def dynamic_database_updater_task():
  global db
  print("dynamic")
  db = await run_in_threadpool(lambda: main.dynamic_database_updater(db, main.names))
  
@app.on_event("startup")
@repeat_every(seconds=60*10, wait_first=True, logger=logging.Logger)
async def static_database_updater_task():
  global db
  print("static")
  db = await run_in_threadpool(lambda: main.static_database_updater(db, main.names))

if __name__ == "__main__":
  uvicorn.run("app:app", port=8080, workers=4)