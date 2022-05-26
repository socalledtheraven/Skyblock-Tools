# SETUP
import json, os, re, time, asyncio, asyncpixel, aiohttp, logging, git, datetime, pytimeparse
from pyinstrument import Profiler
import pandas as pd

apiKey = os.environ["apiKey"]

logging.basicConfig(filename='latest.log', filemode='w+', format='%(asctime)s: [%(levelname)s] %(message)s', datefmt='%d-%b-%y %H:%M:%S') # sets up config logging
 
with open("./database.json", "r+") as database:
  db = json.load(database) #database setup - always needs to run
  start_db = db

repo = git.Repo("./neu-repo")
repo.remotes.origin.pull()
logging.info("NEU update")
# updates neu repo

# ALL SUBROUTINES

async def static_database_updater():
  async with aiohttp.ClientSession() as session:
    items = await get_json("https://api.hypixel.net/resources/skyblock/items", session) # gets the items from the resources endpoint via aiohttp
  items = sorted(items["items"], key=lambda d: d["id"])
  hypixel = asyncpixel.Hypixel(apiKey) 
  bazaar_data = await hypixel.bazaar()
  bazaar_data = bazaar_data.bazaar_items
  bazaar_products = [item.product_id for item in bazaar_data] # aquires bz data from asyncpixel and formats it to also get the bazaarables
  auctions = await hypixel.auctions()
  auction_pages = auctions.total_pages
  auction_data = []
  for i in range(auction_pages):
    page = await hypixel.auctions(page=i)
    page = page.auctions
    auction_data.extend(page) #runs through all the auction pages to add all the auctions together

  auctions = auction_data # redeclares for clarity's sake
  print("setup finished")

  for i in range(len(items)): # runs through every item in the game
    # variable defining sections
    current_item = items[i]
    current_item_name = current_item["id"]
    print(current_item_name) # debug purposes
    current_item_data = {}
    current_item_data["recipe"] = ""
    current_item_data["craft_cost"] = 0
    current_item_data["ingredients"] = {}
    total_ingredients = []
    file = "./neu-repo/items/" + current_item_name + ".json"
    current_item_data["name"] = remove_formatting(current_item["name"])
    current_item_data["id"] = current_item_name
    current_item_data["image_link"] = f"https://sky.shiiyu.moe/item/{current_item_name}" 
    # note - update this with local assets at some point 
    current_item_data["stats"] = current_item["stats"]
    if "npc_sell_price" in current_item:
      current_item_data["npc_salable"] = True
      current_item_data["npc_sell_price"] = current_item["npc_sell_price"]
    
    if "requirements" in current_item:
      current_item_data["use_requirements"] = current_item["requirements"]
      current_item_data["pretty_use_requirements"] = ""
      for x in current_item["requirements"]:
        current_item_data["pretty_use_requirements"] += x["type"].title() + " " + x["level"]
    
    # simple easy declarations
    if current_item_name in bazaar_products:
      current_item_data["bazaarable"] = True
      current_item_bazaar_data = bazaar_data[bazaar_products.index(current_item_name)].quick_status
      current_item_data["bazaar_buy_price"] = round(current_item_bazaar_data.buy_price, 1)
      current_item_data["bazaar_sell_price"] = round(current_item_bazaar_data.sell_price, 1)
      current_item_data["bazaar_profit"] = float(round(current_item_data["bazaar_sell_price"] - current_item_data["bazaar_buy_price"], 1))
      try:
        current_item_data["bazaar_percentage_profit"] = round(current_item_data["bazaar_profit"]/current_item_data["bazaar_buy_price"], 2)
      except ZeroDivisionError:
        logging.error(f"{current_item_name}'s bz price is 0")
    # checks bazaarability and adds any relevant bazaar data
        
    elif current_item_name not in bazaar_products:
      current_item_data["bazaarable"] = False
      bins = list(filter(lambda d: d.bin == True, auctions))
      bin_data = sorted(list(filter(lambda d: d.item_name == current_item_name, bins)), key=lambda d: d.starting_bid)[:2] # lowest two bins
      auction_data = sorted(list(filter(lambda d: d.item_name == current_item_name, auctions)), key=lambda d: d.starting_bid) # lowest auctions
      zero_bid_auction_data = list(filter(lambda d: d.bids == [], auction_data)) # lowest 0 bid auctions
      ending_soon_zero_bid_auction_data = sorted(zero_bid_auction_data, key=lambda d: d.end) # ending soon 0 bid auction
      
      if auction_data != [] or bin_data != []:
        current_item_data["auctionable"] = True
        # gets bin values
        if len(bin_data) > 1:
          current_item_data["lowest_bin"] = bin_data[0].starting_bid
          current_item_data["second_lowest_bin"] = bin_data[1].starting_bid
          
        elif len(bin_data) == 1:
          current_item_data["lowest_bin"] = bin_data[0].starting_bid
          
        else:
          # case for if it's unbinnable
          current_item_data["lowest_bin"] = 0
          current_item_data["second_lowest_bin"] = 0

        if len(auction_data) == 1:
          # adds standard auctions
          current_item_data["lowest_auction"] = auction_data[0].starting_bid
          
        if len(auction_data) > 1:
          # adds standard auctions
          current_item_data["lowest_auction"] = auction_data[0].starting_bid
          current_item_data["second_lowest_auction"] = auction_data[1].starting_bid
          
        if len(zero_bid_auction_data) != 0:
          current_item_data["lowest_0_bid_auction"] = zero_bid_auction_data[0].starting_bid
          current_item_data["lowest_0_bid_ending_soon_auction"] = ending_soon_zero_bid_auction_data[0].starting_bid
          
        else:
          # exception for unauctionables
          current_item_data["lowest_auction"] = 0
          current_item_data["lowest_0_bid_auction"] = 0
      else:
        current_item_data["auctionable"] = False

    
    # begin the data from files section
    try:
      with open(file, "r") as item_file:
        item_file = json.load(item_file)
    except FileNotFoundError:
      pass

    if "slayer_req" in item_file:
      # special case for slayers - crafting and use requirements are always the same
      current_item_data["pretty_use_requirements"] = f"{item_file['slayer_req'][:-1].replace('_', '').title()} {item_file['slayer_req'][-1]}"
      current_item_data["pretty_craft_requirements"] = current_item_data["use_requirements"]
    elif "crafttext" in item_file:
      # add the normal craft requirements
      current_item_data["craft_requirements"] = item_file["crafttext"]

    # crafting
    if "recipe" in item_file:
      current_item_data["recipe"] = item_file["recipe"]
    else:
      logging.info(f"{current_item_name} has no recipe")
      current_item_data["recipe"] = ""
    
    if current_item_data["recipe"] != "" and current_item_data["recipe"] != None and current_item_data["recipe"] != {'A1': '', 'A2': '', 'A3': '', 'B1': '', 'B2': '', 'B3': '', 'C1': '', 'C2': '', 'C3': ''}:
      current_item_data["craftable"] = True
      for j in range(9):
        # separates the ingredients
        ingredients = [ingredient for ingredient in current_item_data["recipe"].values() if ingredient != ""]
      
      for item_type in ingredients:
        item, count = item_type.split(":")
        count = int(count)
        item = log_formatter(item)
        total_ingredients.append({item: count})
        # reassigns variables to set up items

      final_ingredients = {}
      for item in total_ingredients:
        item_name = list(item.keys())[0]
        item_count = list(item.values())[0]
        if item_name in final_ingredients:
          final_ingredients[item_name] += item_count
        else:
          final_ingredients[item_name] = item_count
      ingredients = final_ingredients
      # fixes the ingredients by collating all the duplicates - finally managed to remove some unnecessary imports

      current_item_data["recipe"] = ""
      
      for item in ingredients:
        # better ingredients and recipe formatting
        try:
          item = item.replace("-", ":")
          if isBazaarable(item):
            item_cost = get_bazaar_price(item,"Buy Price")*ingredients[item]
            current_item_data["ingredients"][item] = {"count": ingredients[item], "cost": item_cost}
            current_item_data["craft_cost"] += item_cost
            
            if len(ingredients) > 1 and item != list(ingredients.keys())[-1]: # checks if I should put a comma or not
              current_item_data["recipe"] += f"{ingredients[item]}x {id_to_name(item)} (costing {item_cost}), "
            else:
              current_item_data["recipe"] += f"{ingredients[item]}x {id_to_name(item)} (costing {item_cost})"
              
          elif isAuctionable(item):
            item_cost = get_lowest_bin(item, ingredients[item])
            current_item_data["ingredients"][item] = {"count": ingredients[item], "cost": item_cost}
            if item_cost != "N/A":
              current_item_data["craft_cost"] += item_cost
              
            if len(ingredients) > 1 and item != list(ingredients.keys())[-1]:
              current_item_data["recipe"] += f"{ingredients[item]}x {id_to_name(item)} (costing {item_cost}), "
            else:
              current_item_data["recipe"] += f"{ingredients[item]}x {id_to_name(item)} (costing {item_cost})"
          
          elif db[item]["npc_salable"]:
            item_cost = db[item]["npc_sell_price"] * ingredients[item]
            current_item_data["ingredients"][item] = {"count": ingredients[item], "cost": item_cost}
            if item_cost != "N/A":
              current_item_data["craft_cost"] += item_cost
              
            if len(ingredients) > 1 and item != list(ingredients.keys())[-1]:
              current_item_data["recipe"] += f"{ingredients[item]}x {id_to_name(item)} (costing {item_cost}), "
            else:
              current_item_data["recipe"] += f"{ingredients[item]}x {id_to_name(item)} (costing {item_cost})"
              
          else:
            current_item_data["ingredients"][item] = {"count": ingredients[item], "cost": "N/A"}
            if len(ingredients) > 1 and item != list(ingredients.keys())[-1]:
              current_item_data["recipe"] += f"{ingredients[item]}x {id_to_name(item)}, "
            else:
              current_item_data["recipe"] += f"{ingredients[item]}x {id_to_name(item)}"
              
        except KeyError:
          if "WOOL" not in item or "FISH" not in item or "LEAVES" not in item:
            logging.warning(f"{item} isn't in the database yet")

      # calculates any craft profits
      if current_item_data["bazaarable"]:
        current_item_data["craft_profit"] = float(round(current_item_data["bazaar_sell_price"] - current_item_data["craft_cost"], 1))
        try:
          current_item_data["craft_percentage_profit"] = round(current_item_data["craft_profit"]/current_item_data["craft_cost"], 2)
        except ZeroDivisionError:
          logging.error(f"{current_item_name} costs 0 coins to craft")
          
      elif current_item_data["auctionable"]:
        current_item_data["craft_profit"] = float(round(current_item_data["lowest_bin"] - current_item_data["craft_cost"], 1))
        try:
          current_item_data["craft_percentage_profit"] = round(current_item_data["craft_profit"]/current_item_data["craft_cost"], 2)
        except ZeroDivisionError:
          logging.error(f"{current_item_name} costs 0 coins to craft")
          
      elif current_item_data["npc_salable"]:
        current_item_data["craft_profit"] = float(round(current_item_data["npc_sell_price"] - current_item_data["craft_cost"], 1))
        try:
          current_item_data["craft_percentage_profit"] = round(current_item_data["craft_profit"]/current_item_data["craft_cost"], 2)
        except ZeroDivisionError:
          logging.error(f"{current_item_name} costs 0 coins to craft")
          
    else:
      current_item_data["craftable"] = False
      
    # FORGE STARTS HERE
      
    # gets lore in place
    lore = [remove_formatting(line) for line in item_file["lore"]]
    current_item_data["lore"] = lore
    current_item_data["deformatted_lore"] = " ".join(lore)
    # separates the lore into blocks
    grouped_lore = ["N/A" if line == "" else line + " " for line in lore]
    grouped_lore = "".join(grouped_lore).split("N/A")

    # detects forgability
    if "Required" in current_item_data["deformatted_lore"]:
      current_item_data["forgable"] = True
      duration = lore[-1].replace("Duration: ", "")
      current_item_data["pretty_duration"] = duration
      current_item_data["duration"] = pytimeparse.timeparse.timeparse(duration)
      
      # does this whole massive long thing to get the ingredients on their owm
      splits = []
      splits = [re.split(r"x(?=\d)", line) for line in grouped_lore if "Items Required" in line if line[line.index("x")+1].isdigit()][0]
      splits = [line.replace("Items Required", "").strip() for line in splits]
      splits = [split.split(' ', maxsplit=1) if split != splits[0] else [split] for split in splits]
      splits = [z for sub in splits for z in sub]
      splits = [int(z) if z.isdigit() else z for z in splits]
      splits = [splits[z:z + 2] for z in range(0, len(splits), 2)]
      splits = {(name_to_id(split[0].strip()) if 'Coins' not in split[0] else split[0]): (split[1] if 'Coins' not in split[0] else 1) for split in splits} # such a whole thing just to handle coins

      current_item_data["recipe"] = "Ingredients: "
      current_item_data["forge_cost"] = 0
      # iterates through the ingredients and actually properly formats them and the recipe
      for item in list(splits.keys()):
        print(item)
        if item == "50,000 Coins":
          current_item_data["forge_cost"] += 50000
          current_item_data["ingredients"]["50,000 Coins"] = {"count": 50000, "cost": 50000}
          current_item_data["recipe"] += item
          
        elif item == "50,000,000 Coins":
          current_item_data["forge_cost"] += 50000000
          current_item_data["ingredients"]["50,000,000 Coins"] = {"count": 50000000, "cost": 50000000}
          current_item_data["recipe"] += item
          
        elif item == "25,000 Coins":
          current_item_data["forge_cost"] += 25000
          current_item_data["ingredients"]["25,000 Coins"] = {"count": 25000, "cost": 25000}
          current_item_data["recipe"] += item
        # deals with edge cases for forging recipes involving money
          
        elif isAuctionable(item):
          item_count = splits[item]
          item_cost = get_lowest_bin(item, item_count)
          current_item_data["ingredients"][item] = {"count": item_count, "cost": item_cost}
          current_item_data["forge_cost"] += item_cost
          
          if len(splits) > 1 and item != list(splits.keys())[-1]:
            current_item_data["recipe"] += f"{item_count}x {id_to_name(item)} (costing {item_cost}), "
          else:
            current_item_data["recipe"] += f"{item_count}x {id_to_name(item)} (costing {item_cost})"
            
        elif isBazaarable(item):
          item_count = splits[item]
          item_cost = round((get_bazaar_price(item, "Buy Price") * item_count), 1)
          current_item_data["ingredients"][item] = {"count": item_count, "cost": item_cost}
          current_item_data["forge_cost"] += item_cost
          
          if len(splits) > 1 and item != list(splits.keys())[-1]:
            current_item_data["recipe"] += f"{item_count}x {id_to_name(item)} (costing {item_cost}), "
          else:
            current_item_data["recipe"] += f"{item_count}x {id_to_name(item)} (costing {item_cost})"
            
        elif db[item]["npc_salable"]:
          item_count = splits[item]
          item_cost = db[item]["npc_sell_price"] * item_count
          current_item_data["ingredients"][item] = {"count": item_count, "cost": item_cost}
          current_item_data["forge_cost"] += item_cost
          
          if len(splits) > 1 and item != list(splits.keys())[-1]:
            current_item_data["recipe"] += f"{item_count}x {id_to_name(item)} (costing {item_cost}), "
          else:
            current_item_data["recipe"] += f"{item_count}x {id_to_name(item)} (costing {item_cost})"
            
        else:
          item_count = splits[item]
          current_item_data["ingredients"][item] = {"count": item_count, "cost": 0}
          
          if len(splits) > 1 and item != list(splits.keys())[-1]:
            current_item_data["recipe"] += f"{item_count}x {id_to_name(item)}, "
          else:
            current_item_data["recipe"] += f"{item_count}x {id_to_name(item)}"
            
      if current_item_data["bazaarable"]:
        current_item_data["forge_profit"] = current_item_data["bazaar_sell_price"] - current_item_data["forge_cost"]
        
        try:
          current_item_data["forge_percentage_profit"] = round(current_item_data["forge_profit"]/current_item_data["bazaar_sell_price"], 1)
        except ZeroDivisionError:
          pass
        
        current_item_data["forge_profit_per_hour"] = round(current_item_data["forge_profit"]/(current_item_data["duration"]/3600), 1)
        
      elif current_item_data["auctionable"]:
        current_item_data["forge_profit"] = current_item_data["lowest_bin"] - current_item_data["forge_cost"]
        
        try:
          current_item_data["forge_percentage_profit"] = round(current_item_data["forge_profit"]/current_item_data["lowest_bin"], 1)
        except ZeroDivisionError:
          pass
          
        current_item_data["forge_profit_per_hour"] = round(current_item_data["forge_profit"]/(current_item_data["duration"]/3600), 1)
        
      elif current_item_data["npc_salable"]:
        current_item_data["forge_profit"] = current_item_data["npc_sell_price"] - current_item_data["forge_cost"]
        
        try:
          current_item_data["forge_percentage_profit"] = round(current_item_data["forge_profit"]/current_item_data["npc_sell_price"], 1)
        except ZeroDivisionError:
          pass
          
        current_item_data["forge_profit_per_hour"] = round(current_item_data["forge_profit"]/(current_item_data["duration"]/3600), 1)
        
      
    else:
      current_item_data["forgable"] = False
    
    db[current_item_name] = current_item_data # adds the new data to the database

  await hypixel.close()
  with open("./database.json", "w+") as database:
    json.dump(db, database, indent=2) # DO NOT COMMENT OUT! UPDATES DATABASE
  print("database done")

async def dynamic_database_updater():
  hypixel = asyncpixel.Hypixel(apiKey) 
  bazaar_data = await hypixel.bazaar()
  bazaar_data = bazaar_data.bazaar_items
  bazaar_products = [item.product_id for item in bazaar_data] # aquires bz data from asyncpixel and formats it to also get the bazaarables
  auctions = await hypixel.auctions()
  auction_pages = auctions.total_pages
  auction_data = []
  for i in range(auction_pages):
    page = await hypixel.auctions(page=i)
    page = page.auctions
    auction_data.extend(page) #runs through all the auction pages to add all the auctions together

  auctions = auction_data # redeclares for clarity's sake
  print("setup finished")

  for item in db: # runs through every item in the game
    # variable defining sections
    current_item_name = item
    print(current_item_name) # debug purposes
    current_item_data = db[item]
    file = "./neu-repo/items/" + current_item_name + ".json" # note - update this with local assets at some point 
    
    # simple easy declarations
    if current_item_data["bazaarable"]:
      current_item_bazaar_data = bazaar_data[bazaar_products.index(current_item_name)].quick_status
      current_item_data["bazaar_buy_price"] = round(current_item_bazaar_data.buy_price, 1)
      current_item_data["bazaar_sell_price"] = round(current_item_bazaar_data.sell_price, 1)
      current_item_data["bazaar_profit"] = float(round(current_item_data["bazaar_buy_price"] - current_item_data["bazaar_sell_price"], 1))
      try:
        current_item_data["bazaar_percentage_profit"] = round(current_item_data["bazaar_profit"]/current_item_data["bazaar_buy_price"], 2)
      except ZeroDivisionError:
        logging.error(f"{current_item_name}'s bz price is 0")
    # checks bazaarability and adds any relevant bazaar data
        
    elif current_item_data["auctionable"]:
      bins = list(filter(lambda d: d.bin == True, auctions))
      bin_data = sorted(list(filter(lambda d: d.item_name == current_item_name, bins)), key=lambda d: d.starting_bid)[:2] # lowest two bins
      auction_data = sorted(list(filter(lambda d: d.item_name == current_item_name, auctions)), key=lambda d: d.starting_bid) # lowest auctions
      zero_bid_auction_data = list(filter(lambda d: d.bids == [], auction_data)) # lowest 0 bid auctions
      ending_soon_zero_bid_auction_data = sorted(zero_bid_auction_data, key=lambda d: d.end) # ending soon 0 bid auction
      if len(bin_data) > 1:
        current_item_data["lowest_bin"] = bin_data[0].starting_bid
        current_item_data["second_lowest_bin"] = bin_data[1].starting_bid
        
      elif len(bin_data) == 1:
        current_item_data["lowest_bin"] = bin_data[0].starting_bid
        
      else:
        # case for if it's unbinnable
        current_item_data["lowest_bin"] = 0
        current_item_data["second_lowest_bin"] = 0
        
      if len(auction_data) != 0:
        # adds standard auctions
        current_item_data["lowest_auction"] = auction_data[0].starting_bid
      
      if len(zero_bid_auction_data) != 0:
        current_item_data["lowest_0_bid_auction"] = zero_bid_auction_data[0].starting_bid
        current_item_data["lowest_0_bid_ending_soon_auction"] = ending_soon_zero_bid_auction_data[0].starting_bid
          
      else:
        # exception for unauctionables
        current_item_data["lowest_auction"] = 0
        current_item_data["lowest_0_bid_auction"] = 0

    
    # begin the data from files section
    try:
      with open(file, "r") as item_file:
        item_file = json.load(item_file)
    except FileNotFoundError:
      continue
    
    if current_item_data["craftable"]:
      current_item_data["recipe"] = ""
      for item in current_item_data["ingredients"]:
        # better ingredients and recipe formatting
        item_cost = current_item_data["ingredients"][item]["cost"]
        item_count = current_item_data["ingredients"][item]["count"]
        if item_cost != "N/A":
          current_item_data["craft_cost"] += item_cost
          
        try:
          item = item.replace("-", ":")
          if isBazaarable(item):
            if len(current_item_data["ingredients"]) > 1 and item != list(current_item_data["ingredients"].keys())[-1]: # checks if I should put a comma or not
              current_item_data["recipe"] += f"{item_count}x {id_to_name(item)} (costing {item_cost}), "
            else:
              current_item_data["recipe"] += f"{item_count}x {id_to_name(item)} (costing {item_cost})"
              
          elif isAuctionable(item):
            if len(current_item_data["ingredients"]) > 1 and item != list(current_item_data["ingredients"].keys())[-1]: # checks if I should put a comma or not
              current_item_data["recipe"] += f"{item_count}x {id_to_name(item)} (costing {item_cost}), "
            else:
              current_item_data["recipe"] += f"{item_count}x {id_to_name(item)} (costing {item_cost})"
          
          else:
            if len(current_item_data["ingredients"]) > 1 and item != list(current_item_data["ingredients"].keys())[-1]: # checks if I should put a comma or not
              current_item_data["recipe"] += f"{item_count}x {id_to_name(item)} (costing {item_cost}), "
            else:
              current_item_data["recipe"] += f"{item_count}x {id_to_name(item)} (costing {item_cost})"
              
        except KeyError:
          logging.error(f"{item} isn't in the database yet")
  
        # calculates any craft profits
        if current_item_data["bazaarable"]:
          current_item_data["craft_profit"] = float(round(current_item_data["bazaar_sell_price"] - current_item_data["craft_cost"], 1))
          try:
            current_item_data["craft_percentage_profit"] = round(current_item_data["craft_profit"]/current_item_data["craft_cost"], 2)
          except ZeroDivisionError:
            logging.error(f"{current_item_name} costs 0 coins to craft")
            
        elif current_item_data["auctionable"]:
          current_item_data["craft_profit"] = float(round(current_item_data["lowest_bin"] - current_item_data["craft_cost"], 1))
          try:
            current_item_data["craft_percentage_profit"] = round(current_item_data["craft_profit"]/current_item_data["craft_cost"], 2)
          except ZeroDivisionError:
            logging.error(f"{current_item_name} costs 0 coins to craft")
            
      
    # FORGE STARTS HERE
    if current_item_data["forgable"]:
      current_item_data["recipe"] = "Ingredients: "
      # iterates through the ingredients and actually properly formats them and the recipe
      for item in list(current_item_data["ingredients"].keys()):
        try:
          if item == "50,000 Coins":
            current_item_data["forge_cost"] += 50000
            current_item_data["recipe"] += item
            
          elif item == "50,000,000 Coins":
            current_item_data["forge_cost"] += 50000000
            current_item_data["recipe"] += item
            
          elif item == "25,000 Coins":
            current_item_data["forge_cost"] += 25000
            current_item_data["recipe"] += item
          # deals with edge cases for forging recipes involving money
            
          elif isAuctionable(item):
            current_item_data["forge_cost"] += item["cost"]
            if len(current_item_data["ingredients"]) > 1 and item != list(current_item_data["ingredients"].keys())[-1]:
              current_item_data["recipe"] += f"{item['count']}x {id_to_name(item)} (costing {item['cost']}), "
            else:
              current_item_data["recipe"] += f"{item['count']}x {id_to_name(item)} (costing {item['cost']})"
              
          elif isBazaarable(item):
            current_item_data["forge_cost"] += item["cost"]
            if len(current_item_data["ingredients"]) > 1 and item != list(current_item_data["ingredients"].keys())[-1]:
              current_item_data["recipe"] += f"{item['count']}x {id_to_name(item)} (costing {item['cost']}), "
            else:
              current_item_data["recipe"] += f"{item['count']}x {id_to_name(item)} (costing {item['cost']})"
              
        except Exception as e:
          logging.exception(e)

    db[current_item_name] = current_item_data # adds the new data to the database
    
  with open("./database.json", "w+") as database:
    json.dump(db, database, indent=2) # DO NOT COMMENT OUT! UPDATES DATABASE
  print("database done")

async def deletion_time():
  for item in db:
    try:
      if db[item]["forgable"]:
        pass
    except KeyError:
      db[item]["forgable"] = False
  
           

def log_formatter(log):
  if "WOOD" in log and log != "WOOD":
    if log[-1].isdigit():
      log = "WOOD:" + log[-1]
    else:
      log = "WOOD"
  elif "LOG" in log:
    log = log.replace("-", ":")
    if log == "LOG:4":
      log = "LOG_2"
    elif log == "LOG:5":
      log = "LOG_2:1"
  
  return log

def bazaar_flipper():
  final_products = {}
  final_products["item_name"] = {}
  final_products["buy_order_price"] = {}
  final_products["sell_order_price"] = {}
  final_products["product_margins"] = {}
  final_products["profit_percentage"] = {}
  bazaarables = []
  
  for item in db:
    if db[item]["bazaarable"]:
      if db[item]["bazaar_profit"] > 0:
        bazaarables.append(db[item])
  # initialising variables

  for i in range(len(bazaarables)):
    current_item_data = bazaarables[i]
    final_products["item_name"][i] = current_item_data["name"]
    print(current_item_data["id"])
    final_products["buy_order_price"][i] = commaify(current_item_data["bazaar_buy_price"])
    final_products["sell_order_price"][i] = commaify(current_item_data["bazaar_sell_price"])
    final_products["product_margins"][i] = commaify(current_item_data["bazaar_profit"])
    final_products["profit_percentage"][i] = str(current_item_data["bazaar_percentage_profit"]) + "%"
  
  final_products = pd.DataFrame({"Item": final_products["item_name"], "Product Margin": final_products["product_margins"], "Profit %": final_products["profit_percentage"], "Buy Price": final_products["buy_order_price"], "Sell Price": final_products["sell_order_price"]})
  
  return final_products

def craft_flipper():
  final_flips = {}
  final_flips["image"] = {}
  final_flips["name"] = {}
  final_flips["sell_price"] = {}
  final_flips["craft_cost"] = {}
  final_flips["requirements"] = {}
  final_flips["profit"] = {}
  final_flips["%profit"] = {}
  final_flips["formatted_ingredients"] = {}
  craftables = []
  for item in db:
    if db[item]["craftable"]:
      if db[item].get("craft_profit") != None and db[item].get("craft_profit") < 0:
        craftables.append(db[item])

  for i in range(len(craftables)):
    print(craftables[i]["id"])
    current_item_data = craftables[i]
    final_flips["image"][i] = f"<img src={current_item_data['image_link']}>"
    final_flips["name"][i] = current_item_data["name"]
    if current_item_data["bazaarable"]:
      final_flips["sell_price"][i] = commaify(current_item_data["bazaar_sell_price"])
    elif current_item_data["auctionable"]:
      final_flips["sell_price"][i] = commaify(current_item_data["lowest_bin"])
    else:
      final_flips["sell_price"][i] = 0
    final_flips["craft_cost"][i] = commaify(current_item_data["craft_cost"])
    final_flips["requirements"][i] = current_item_data.get("craft_requirements")
    final_flips["profit"][i] = commaify(current_item_data["craft_profit"])
    try:
      final_flips["%profit"][i] = commaify(current_item_data["craft_percentage_profit"])
    except KeyError:
      final_flips["%profit"][i] = 0
    final_flips["formatted_ingredients"][i] = current_item_data["recipe"]

  return pd.DataFrame({"Image": final_flips["image"], "Name": final_flips["name"], "Profit": final_flips["profit"], "% Profit": final_flips["%profit"], "Requirements": final_flips["requirements"], "Recipe": final_flips["formatted_ingredients"]})

def build_table(table_data, HTMLFILE):
  f = open(HTMLFILE, 'w+')  # opens the file
  htmlcode = table_data.to_html(index=False, classes='table table-striped') # transforms it into a table with module magic
  htmlcode = htmlcode.replace('<table border="1" class="dataframe table table-striped">','<table class="table table-striped" border="1" style="border: 1px solid #000000; border-collapse: collapse;" cellpadding="4" id="data">')
  f.write(htmlcode)  # writes the table to the file
  f.close()


def isVanilla(itemname):
  vanilla_items = ["WOOD_AXE", "WOOD_HOE", "WOOD_PICKAXE", "WOOD_SPADE", "WOOD_SWORD", "GOLD_AXE", "GOLD_HOE","GOLD_PICKAXE", "GOLD_SPADE", "GOLD_SWORD", "ROOKIE_HOE"]
  if itemname in vanilla_items or db[itemname]["vanilla"] == True:
    return True
  else:
    return False 


def is_file_empty(file_name):
  #Check if file is empty by reading first character in it
  #open file in read mode
  try:
    with open(file_name, 'r') as read_obj:
      # read first character
      one_char = read_obj.read(1)
      # if not fetched then file is empty
      if not one_char:
        return True
    return False
  except TypeError:
    return False


def isAuctionable(itemname):
  return db[itemname].get("auctionable")


def render_item(itemname):
  return db[itemname]["link"]


def isBazaarable(itemname):
  return db[itemname].get("bazaarable")


def get_lowest_bin(itemname, count):
  if db[itemname].get("auctionable") and "lowest_bin" in db[itemname]:
    return db[itemname]["lowest_bin"] * count
  else:
    return "N/A"
  

def get_bazaar_price(itemname, value):
  if db[itemname]["bazaarable"]:
    if value == "Buy Price":
      return db[itemname]["bazaar_buy_price"]
    elif value == "Sell Price":
      return db[itemname]["bazaar_sell_price"]
  else:
    return "N/A"
  

def get_recipe(itemname):
  return db[itemname].get("recipe")

def forge_flipper():
  final_flips = {}
  final_flips["image"] = {}
  final_flips["name"] = {}
  final_flips["id"] = {}
  final_flips["sell_price"] = {}
  final_flips["craft_cost"] = {}
  final_flips["requirements"] = {}
  final_flips["formatted_ingredients"] = {}
  final_flips["profit"] = {}
  final_flips["%profit"] = {}
  final_flips["time"] = {} 
  i = 0
  with open("./constants/forgables.json") as forgables:
    forgables = json.load(forgables)
  #declares so many goddamn variables

  for item in forgables:
    current_item_data = db[item]
    final_flips["id"][i] = item
    final_flips["image"][i] = f"<img src={current_item_data['image_link']}>"
    final_flips["name"][i] = current_item_data["name"]
    if current_item_data["bazaarable"]:
      final_flips["sell_price"][i] = commaify(current_item_data["bazaar_sell_price"])
    elif current_item_data["auctionable"]:
      final_flips["sell_price"][i] = commaify(current_item_data["lowest_bin"])
    else:
      final_flips["sell_price"][i] = 0
    final_flips["craft_cost"][i] = commaify(current_item_data["forge_cost"])
    final_flips["requirements"][i] = current_item_data["craft_requirements"]
    final_flips["formatted_ingredients"][i] = current_item_data["recipe"]
    final_flips["profit"][i] = commaify(current_item_data["forge_profit"])
    final_flips["%profit"][i] = commaify(current_item_data["forge_percentage_profit"])
    final_flips["time"][i] = current_item_data["duration"]

  return pd.DataFrame({"Image": final_flips["image"], "Name": final_flips["name"], "Profit": final_flips["profit"], "% Profit": final_flips["%profit"], "Requirements": final_flips["requirements"], "Recipe": final_flips["formatted_ingredients"], "Duration": final_flips["time"]})    
      
  
def name_to_id(itemname):
  if "Drill" in itemname:
    itemname = itemname.replace("Model", "").replace("  ", " ") # fixes inconsistencies because the hypixel devs hate me personally
  elif itemname == "Sapphire Crystal":
    return "SAPPHIRE_CRYSTAL" # the devs made a fucking SPELLING MISTAKE IN THE API 
    
  try:
    for item in db:
      if itemname == db[item]["name"]:
        return item
    return itemname
    
  except KeyError as e:
    logging.exception(e)
    return "AMMONITE;4"
    
  except ValueError as e:
    logging.exception(e)
    return itemname
  

def id_to_name(itemname):
  try:
    return db[itemname]["name"]
  except Exception as e:
    logging.error(e)
    return "failed :("

def remove_formatting(string):
  formatting_codes = ["§4", "§c", "§6", "§e", "§2", "§a", "§b", "§3", "§1", "§9", "§d", "§5", "§f", "§7", "§8", "§0", "§k", "§l", "§m", "§n", "§o", "§r"]  # sets up formatting codes so I can ignore them
  for i in range(len(formatting_codes)):
    string = string.replace("{}".format(formatting_codes[i]), "")  # as above

  string = "".join(c for c in string if ord(c)<128)
  return string

def commaify(num):
  return "{:,}".format(num)

async def get_json(url, session):
  async with session.get(url) as resp:
    return await resp.json(content_type=None)

    
#---------------------------------------------------------------------------------------------------------
#                                           SUBPROGRAMS
#---------------------------------------------------------------------------------------------------------

p = Profiler()
p.start()
# asyncio.run(static_database_updater())
asyncio.run(dynamic_database_updater())
# asyncio.run(deletion_time())
craft_flipper()
p.stop()
p.print()

'''TODO:
better reqs testing
'''