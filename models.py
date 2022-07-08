import uuid
import datetime
from typing import Optional, Dict, List
from pydantic import BaseModel, HttpUrl

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