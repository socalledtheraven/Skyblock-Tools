import requests, json, os, collections, functools, operator, re, time, replit, asyncio, asyncpixel, aiohttp
from replit import db
import pandas as pd
from git import Repo
apiKey = os.environ["apiKey"]


def static_database_updater():
  items = sorted(json.loads(requests.get("https://api.hypixel.net/resources/skyblock/items").text)["items"], key=lambda d: d['id'])
  bazaar_data = json.loads(requests.get("https://api.slothpixel.me/api/skyblock/bazaar/").text)
  bazaar_products = list(requests.get("https://sky.coflnet.com/api/items/bazaar/tags").text)
  # print(items)

  for i in range(len(items)):
    # variable defining sections
    current_item_name = ""
    current_item = items[i]
    current_item_name = current_item["id"]
    print(current_item_name)
    current_item_data = {}
    current_item_data["recipe"] = ""
    current_item_data["craft_cost"] = 0
    current_item_data["ingredients"] = {}
    total_ingredients = []
    file = "./neu-repo/items/" + current_item_name + ".json"
    
    try:
      auction_data = json.loads(requests.get(f"https://auction-api.up.railway.app/query?key=placeholder&item_id={current_item_name}&bin=false&limit=5000").text) # lowest auctions
    except json.decoder.JSONDecodeError:
      auction_data = []
      
    try:
      ending_soon_zero_bid_auction_data = json.loads(requests.get(f"https://auction-api.up.railway.app/query?key=placeholder&query=item_id={current_item_name}%20AND%20cardinality(bids)=0%20AND%20bin=false%20ORDER%20BY%20end_t").text) # ending soon 0 bid auctions
    except json.decoder.JSONDecodeError:
      ending_soon_zero_bid_auction_data = []
      
    try:
      zero_bid_auction_data = json.loads(requests.get(f"https://auction-api.up.railway.app/query?key=placeholder&query=item_id={current_item_name}%20AND%20cardinality(bids)=0%20AND%20bin=false").text) # lowest 0 bid auctions
    except json.decoder.JSONDecodeError:
      zero_bid_auction_data = []
    
    try:
      bin_data = json.loads(requests.get(f"https://auction-api.up.railway.app/query?key={auction_api_key}&item_id={current_item_name}&limit=2").text) # lowest two bins
    except json.decoder.JSONDecodeError:
      bin_data = []
    
    current_item_data["name"] = id_to_name(current_item_name)
    current_item_data["id"] = current_item_name
    current_item_data["image_link"] = f"https://sky.shiiyu.moe/item/{current_item_name}" # simple easy declarations

    # checks for bazaarability and prices
    if current_item_name in bazaar_products:
      current_item_data["bazaarable"] = True
      current_item_data["bazaar_buy_price"] = bazaar_data[current_item_name]["buy_summary"][0]["pricePerUnit"]
      current_item_data["bazaar_sell_price"] = bazaar_data[current_item_name]["sell_summary"][0]["pricePerUnit"]
      current_item_data["bazaar_profit"] = float(round(current_item_data["bazaar_sell_price"]-current_item_data["bazaar_buy_price"], 1))
      current_item_data["bazaar_percentage_profit"] = round(current_item_data["bazaar_profit"]/current_item_data["bazaar_buy_price"], 2)
    #checks for auctionability
    elif current_item_name not in bazaar_products:
      current_item_data["bazaarable"] = False
      if auction_data != [] or bin_data != []:
        current_item_data["auctionable"] = True
        # gets bin values
        if len(bin_data) > 1:
          current_item_data["lowest_bin"] = bin_data[0]["starting_bid"]
          current_item_data["second_lowest_bin"] = bin_data[1]["starting_bid"]
        elif len(bin_data) == 1:
          current_item_data["lowest_bin"] = bin_data[0]["starting_bid"]
        else:
          # case for if it's unbinnable
          current_item_data["lowest_bin"] = 0
          current_item_data["second_lowest_bin"] = 0
        if len(auction_data) != 0:
          # adds standard auctions
          current_item_data["lowest_auction"] = auction_data[0]["starting_bid"]
          current_item_data["lowest_0_bid_auction"] = zero_bid_auction_data[0]["starting_bid"]
          current_item_data["lowest_0_bid_ending_soon_auction"] = ending_soon_zero_bid_auction_data[0]["starting_bid"]
        else:
          # exception for unauctionables
          current_item_data["lowest_auction"] = 0
          current_item_data["lowest_0_bid_auction"] = 0
      else:
        current_item_data["auctionable"] = False

    try:
      # gets the recipe from coflnet
      current_item_data["recipe"] = json.loads(requests.get(f"https://sky.coflnet.com/api/craft/recipe/{current_item_name}").text)
    except json.decoder.JSONDecodeError:
      current_item_data["recipe"] = ""
    
    if current_item_data["recipe"] != "" and current_item_data["recipe"] != {'A1': '', 'A2': '', 'A3': '', 'B1': '', 'B2': '', 'B3': '', 'C1': '', 'C2': '', 'C3': ''}:
      current_item_data["craftable"] = True
      for j in range(9):
        #seperates the ingredients
        ingredients = [ingredient for ingredient in current_item_data["recipe"].values() if ingredient != ""]
      
      for item_type in ingredients:
        item, count = item_type.split(":")
        count = int(count)
        item = log_formatter(item)
        total_ingredients.append({item: count})
        # reassigns variables to set up items

      ingredients = dict(functools.reduce(operator.add, map(collections.Counter, total_ingredients)))

      current_item_data["recipe"] = ""
      
      for item in ingredients:
        # better ingredients and recipe formatting
        if isBazaarable(item):
          current_item_data["ingredients"][item] = {"count": ingredients[item], "cost": get_bazaar_price(item)["Buy Price"]*ingredients[item]}
          current_item_data["craft_cost"] += current_item_data["ingredients"][item]["cost"]
          if len(ingredients) > 1 and item != list(ingredients.keys())[-1]:
            current_item_data["recipe"] += f"{current_item_data['ingredients'][item]['count']}x {id_to_name(item)} (costing {current_item_data['ingredients'][item]['cost']}), "
          else:
            current_item_data["recipe"] += f"{current_item_data['ingredients'][item]['count']}x {id_to_name(item)} (costing {current_item_data['ingredients'][item]['cost']})"
        elif isAuctionable(item):
          current_item_data["ingredients"][item] = {"count": ingredients[item], "cost": get_lowest_bin(item, ingredients[item])}
          if current_item_data["ingredients"][item]["cost"] != "N/A":
            current_item_data["craft_cost"] += current_item_data["ingredients"][item]["cost"]
          if len(ingredients) > 1 and item != list(ingredients.keys())[-1]:
            current_item_data["recipe"] += f"{current_item_data['ingredients'][item]['count']}x {id_to_name(item)} (costing {current_item_data['ingredients'][item]['cost']}), "
          else:
            current_item_data["recipe"] += f"{current_item_data['ingredients'][item]['count']}x {id_to_name(item)} (costing {current_item_data['ingredients'][item]['cost']})"
        else:
          current_item_data["ingredients"][item] = {"count": ingredients[item], "cost": "N/A"}
          if len(ingredients) > 1 and item != list(ingredients.keys())[-1]:
            current_item_data["recipe"] += f"{current_item_data['ingredients'][item]['count']}x {id_to_name(item)} (costing {current_item_data['ingredients'][item]['cost']}), "
          else:
            current_item_data["recipe"] += f"{current_item_data['ingredients'][item]['count']}x {id_to_name(item)} (costing {current_item_data['ingredients'][item]['cost']})"

      # calculates any craft profits
      if current_item_data["bazaarable"]:
        current_item_data["craft_profit"] = float(round(current_item_data["bazaar_buy_price"] - current_item_data["craft_cost"], 1))
        current_item_data["craft_percentage_profit"] = round(current_item_data["craft_profit"]/current_item_data["craft_cost"], 2)
      elif current_item_data["auctionable"]:
        current_item_data["craft_profit"] = float(round(current_item_data["lowest_bin"] - current_item_data["craft_cost"], 1))
        current_item_data["craft_percentage_profit"] = round(current_item_data["craft_profit"]/current_item_data["craft_cost"], 2)
    else:
      current_item_data["craftable"] = False

    # begin the data from files section
    try:
      with open(file, "r") as item_file:
        item_file = json.load(item_file)
    except FileNotFoundError:
      print("neu goofed")

    if "slayer_req" in item_file:
      # special case for slayers - crafting and use requirements are always the same
      current_item_data["use_requirements"] = f"{item_file['slayer_req'][:-1].replace('_', '').title()} {item_file['slayer_req'][-1]}"
      current_item_data["craft_requirements"] = current_item_data["use_requirements"]
    elif "crafttext" in item_file:
      # add the normal craft requirements
      current_item_data["craft_requirements"] = item_file["crafttext"]

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
      current_item_data["forge_duration"] = lore[-1].replace("Duration: ", "")
      
      # does this whole massive long thing to get the ingredients on their owm
      splits = [re.split(r"x(?=\d)", line) for line in grouped_lore if "Items Required" in line if line[line.index("x")+1].isdigit()][0]
      splits = [line.replace("Items Required", "").strip() for line in splits]
      splits = [split.split(' ', maxsplit=1) if split != splits[0] else [split] for split in splits]
      splits = [z for sub in splits for z in sub]
      splits = [catch(int, z) for z in splits]
      splits = [splits[z:z + 2] for z in range(0, len(splits), 2)]
      for split in splits:
        split[0] = name_to_id(split[0].strip())
      
      current_item_data["recipe"] = "Ingredients: "
      # iterates through the ingredients and actually properly formats them and the recipe
      
      for item in splits:
        if item == ["50,000 Coins"]:
          current_item_data["forge_cost"] += 50000
          current_item_data["ingredients"]["50,000 Coins"] = {"count": 50000, "cost": 50000}
          current_item_data["recipe"] += item[0]
          continue
        elif item == ["50,000,000 Coins"]:
          current_item_data["forge_cost"] += 50000000
          current_item_data["ingredients"]["50,000,000 Coins"] = {"count": 50000000, "cost": 50000000}
          current_item_data["recipe"] += item[0]
          continue
        elif item == ["25,000 Coins"]:
          current_item_data["forge_cost"] += 25000
          current_item_data["ingredients"]["25,000 Coins"] = {"count": 25000, "cost": 25000}
          current_item_data["recipe"] += item[0]
          continue
        if isAuctionable(item[0]):
          current_item_data["ingredients"][item[0]] = {"count": item[1], "cost": get_lowest_bin(item[0], item[1])}
          if len(splits) > 1 and item != splits[-1]:
            current_item_data["recipe"] += f"{item[1]}x {id_to_name(item[0])} (costing {get_lowest_bin(item[0], item[1])}), "
          else:
            current_item_data["recipe"] += f"{item[1]}x {id_to_name(item[0])} (costing {get_lowest_bin(item[0], item[1])})"
        elif isBazaarable(item[0]):
          current_item_data["ingredients"][item[0]] = {"count": item[1], "cost": get_bazaar_price(item[0])["Buy Price"]*item[1]}
          if len(splits) > 1 and item != splits[-1]:
            current_item_data["recipe"] += f"{item[1]}x {id_to_name(item[0])} (costing {round(get_bazaar_price(item[0])['Buy Price']*item[1], 1)}), "
          else:
            current_item_data["recipe"] += f"{item[1]}x {id_to_name(item)} (costing {round(get_bazaar_price(item[0])['Buy Price']*item[1], 1)})"

    # sets the database values
    db[current_item_name] = current_item_data
  
      
    # https://railway.app/project/3a3efefb-a388-4fef-97d2-bee55909b58e/service/98472656-cca9-4757-9dac-95f98f0c7abc/domains
  
async def dynamic_database_updater():
  hypixel = asyncpixel.Hypixel(apiKey)
  final_start = time.perf_counter()
  bazaar_data = await hypixel.bazaar()
  bazaar_data = bazaar_data.bazaar_items
  bazaar_items = [item.product_id for item in bazaar_data]
  auctions = await hypixel.auctions()
  auction_pages = auctions.total_pages
  auction_data = []
  for i in range(auction_pages):
    page = await hypixel.auctions(page=i)
    page = page.auctions
    auction_data.extend(page)

  auctions = auction_data
  database = db
  with open("./constants/auctionables.json") as auctionables:
    auctionables = sorted(json.load(auctionables))
  with open("./constants/bazaarables.json") as bazaarables:
    bazaarables = json.load(bazaarables)
  with open("./constants/craftables.json") as craftables:
    craftables = sorted(json.load(craftables))
  with open("./constants/forgables.json") as forgables:
    forgables = sorted(json.load(forgables))

  start = time.perf_counter()
  for item in bazaarables:
    print("bazaar", item)
    current_item_data = database[item]
    current_item_bazaar_data = bazaar_data[bazaar_items.index(item)].quick_status
    current_item_data["bazaar_buy_price"] = round(current_item_bazaar_data.buy_price, 1)
    current_item_data["bazaar_sell_price"] = round(current_item_bazaar_data.sell_price, 1)
    current_item_data["bazaar_profit"] = float(round(current_item_data["bazaar_sell_price"]-current_item_data["bazaar_buy_price"], 1))
    current_item_data["bazaar_percentage_profit"] = round(current_item_data["bazaar_profit"]/current_item_data["bazaar_buy_price"], 1)
    db[item] = current_item_data
  end = time.perf_counter()
  t = end-start
  print(f"bazaar done in {t:.2f} seconds")

  start = time.perf_counter()
  for item in craftables:
    print("craft", item)
    current_item_data = database[item]
    current_item_data["recipe"] = ""
    current_item_data["craft_cost"] = 0
    ingredients = json.loads(replit.database.dumps(current_item_data["ingredients"]))
    for ingredient in ingredients:
      ingredient = log_formatter(ingredient)
      if isAuctionable(ingredient):
        current_item_data["ingredients"][ingredient]["cost"] = current_item_data["ingredients"][ingredient]["count"] * db[ingredient]["lowest_bin"]
        if len(ingredients) > 1 and ingredient != list(ingredients.keys())[-1]:
          current_item_data["recipe"] += f"{current_item_data['ingredients'][ingredient]['count']}x {id_to_name(ingredient)} (costing {current_item_data['ingredients'][ingredient]['cost']}), "
        else:
          current_item_data["recipe"] += f"{current_item_data['ingredients'][ingredient]['count']}x {id_to_name(ingredient)} (costing {current_item_data['ingredients'][ingredient]['cost']})"
        current_item_data["craft_cost"] += current_item_data["ingredients"][ingredient]["cost"]
      elif isBazaarable(ingredient):
        current_item_data["ingredients"][ingredient]["cost"] = current_item_data["ingredients"][ingredient]["count"] * db[ingredient]["bazaar_buy_price"]
        if len(ingredients) > 1 and ingredient != list(ingredients.keys())[-1]:
          current_item_data["recipe"] += f"{current_item_data['ingredients'][ingredient]['count']}x {id_to_name(ingredient)} (costing {current_item_data['ingredients'][ingredient]['cost']}), "
        else:
          current_item_data["recipe"] += f"{current_item_data['ingredients'][ingredient]['count']}x {id_to_name(ingredient)} (costing {current_item_data['ingredients'][ingredient]['cost']})"
        current_item_data["craft_cost"] += current_item_data["ingredients"][ingredient]["cost"]
      else:
        current_item_data["ingredients"][ingredient]["cost"] = 0
        if len(ingredients) > 1 and ingredient != list(ingredients.keys())[-1]:
          current_item_data["recipe"] += f"{current_item_data['ingredients'][ingredient]['count']}x {id_to_name(ingredient)}, "
        else:
          current_item_data["recipe"] += f"{current_item_data['ingredients'][ingredient]['count']}x {id_to_name(ingredient)}"
    current_item_data["ingredients"] = ingredients
          
    if current_item_data["bazaarable"]:
      if current_item_data["craft_cost"] != 0:
        current_item_data["craft_profit"] = float(round(current_item_data["bazaar_buy_price"] - current_item_data["craft_cost"], 1))
        current_item_data["craft_percentage_profit"] = round(current_item_data["craft_profit"]/current_item_data["craft_cost"], 2)
      else:
        current_item_data["craft_profit"] = 0
        current_item_data["craft_percentage_profit"] = 0
    elif current_item_data["auctionable"]:
      if current_item_data["craft_cost"] != 0:
        current_item_data["craft_profit"] = float(round(current_item_data["lowest_bin"] - current_item_data["craft_cost"], 1))
        current_item_data["craft_percentage_profit"] = round(current_item_data["craft_profit"]/current_item_data["craft_cost"], 2)
      else:
        current_item_data["craft_profit"] = 0
        current_item_data["craft_percentage_profit"] = 0
    
    db[item] = current_item_data
  end = time.perf_counter()
  t = end-start
  print(f"crafts done in {t:.2f} seconds")

  start = time.perf_counter()
  for item in forgables:
    print("forge", item)
    current_item_data = database[item]
    current_item_data["recipe"] = ""
    current_item_data["forge_cost"] = 0
    for ingredient in current_item_data["ingredients"]:
      if ingredient == "50,000 Coins":
        current_item_data["forge_cost"] += 50000
        current_item_data["recipe"] += ingredient
        continue
      elif ingredient == "50,000,000 Coins":
        current_item_data["forge_cost"] += 50000000
        current_item_data["recipe"] += ingredient
        continue
      elif ingredient == "25,000 Coins":
        current_item_data["forge_cost"] += 25000
        current_item_data["recipe"] += ingredient
        continue
      if db[ingredient]["auctionable"]:
        current_item_data["ingredients"][ingredient]["cost"] = current_item_data["ingredients"][ingredient]["count"] * db[ingredient]["lowest_bin"]
        try:
          if len(current_item_data["ingredients"]) > 1 and ingredient != current_item_data["ingredients"][-1]:
            current_item_data["recipe"] += f"{current_item_data['ingredients'][ingredient]['count']}x {id_to_name(ingredient)} (costing {current_item_data['ingredients'][ingredient]['cost']}), "
          else:
            current_item_data["recipe"] += f"{current_item_data['ingredients'][ingredient]['count']}x {id_to_name(ingredient)} (costing {current_item_data['ingredients'][ingredient]['cost']})"
        except:
          current_item_data["recipe"] += f"{current_item_data['ingredients'][ingredient]['count']}x {id_to_name(ingredient)} (costing {current_item_data['ingredients'][ingredient]['cost']}), "
        current_item_data["forge_cost"] += current_item_data["ingredients"][ingredient]["cost"]
      elif db[ingredient]["bazaarable"]:
        current_item_data["ingredients"][ingredient]["cost"] = current_item_data["ingredients"][ingredient]["count"] * db[ingredient]["bazaar_buy_price"]
        try:
          if len(current_item_data["ingredients"]) > 1 and ingredient != current_item_data["ingredients"][-1]:
            current_item_data["recipe"] += f"{current_item_data['ingredients'][ingredient]['count']}x {id_to_name(ingredient)} (costing {current_item_data['ingredients'][ingredient]['cost']}), "
          else:
            current_item_data["recipe"] += f"{current_item_data['ingredients'][ingredient]['count']}x {id_to_name(ingredient)} (costing {current_item_data['ingredients'][ingredient]['cost']})"
        except:
          current_item_data["recipe"] += f"{current_item_data['ingredients'][ingredient]['count']}x {id_to_name(ingredient)} (costing {current_item_data['ingredients'][ingredient]['cost']}), "
        current_item_data["forge_cost"] += current_item_data["ingredients"][ingredient]["cost"]
      else:
        current_item_data["ingredients"][ingredient]["cost"] = 0
        try:
          if len(current_item_data["ingredients"]) > 1 and ingredient != current_item_data["ingredients"][-1]:
            current_item_data["recipe"] += f"{current_item_data['ingredients'][ingredient]['count']}x {id_to_name(ingredient)}, "
          else:
            current_item_data["recipe"] += f"{current_item_data['ingredients'][ingredient]['count']}x {id_to_name(ingredient)}"
        except:
          current_item_data["recipe"] += f"{current_item_data['ingredients'][ingredient]['count']}x {id_to_name(ingredient)}, "
    
    
    db[item] = current_item_data
  end = time.perf_counter()
  t = end-start
  print(f"forge done in {t:.2f} seconds")

  start = time.perf_counter()
  for item in auctionables:
    print("auction", item)
    current_item_data = database[item]
    bins = list(filter(lambda d: d.bin == True, auctions))
    bin_data = sorted(list(filter(lambda d: d.item_name == item, bins)), key=lambda d: d.starting_bid)[:2] # lowest two bins
    auction_data = sorted(list(filter(lambda d: d.item_name == item, auctions)), key=lambda d: d.starting_bid) # lowest auctions
    zero_bid_auction_data = list(filter(lambda d: d.bids == [], auction_data)) # lowest 0 bid auctions
    ending_soon_zero_bid_auction_data = sorted(zero_bid_auction_data, key=lambda d: d.end)# ending soon 0 bid auction
      
    try:
      current_item_data["lowest_bin"] = bin_data["lowest"]
      current_item_data["second_lowest_bin"] = bin_data["secondLowest"]
    except:
      current_item_data["lowest_bin"] = 0
      current_item_data["second_lowest_bin"] = 0
      
    if len(auction_data) != 0:
      # adds standard auctions
      current_item_data["lowest_auction"] = auction_data[0]["starting_bid"]
      if zero_bid_auction_data != []:
        current_item_data["lowest_0_bid_auction"] = zero_bid_auction_data[0]["starting_bid"]
        current_item_data["lowest_0_bid_ending_soon_auction"] = ending_soon_zero_bid_auction_data[0]["starting_bid"]
    else:
      # exception for unauctionables
      current_item_data["lowest_auction"] = 0
      current_item_data["lowest_0_bid_auction"] = 0
          
    db[item] = current_item_data
  end = time.perf_counter()
  t = end-start
  print(f"auction done in {t:.2f} seconds")

      
  final_end = time.perf_counter()
  print(f"Complete time: {time.strftime('%H:%M:%S', time.gmtime(final_end-final_start))}")
  await hypixel.close()
  
def deletion_time():
  database = db
  bazaarables = []
  for item in database:
    print(item)
    if database[item]["bazaarable"]:
      bazaarables.append(item)

  with open("./constants/bazaarables.json", "w") as bazaarables_file:
    json.dump(bazaarables, bazaarables_file, ensure_ascii=True, indent=2)
      
           
def catch(func, *args, handle=lambda e : e, **kwargs):
  try:
    return func(*args, **kwargs)
  except Exception:
    return str(*args)

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
  i = 0
  database = db
  with open("./constants/bazaarables.json", "r") as bazaarables:
    bazaarables = json.load(bazaarables)
  # initialising variables

  for item in bazaarables:
    current_item_data = database[item]
    final_products["item_name"][i] = current_item_data["name"]
    final_products["buy_order_price"][i] = commaify(current_item_data["bazaar_buy_price"])
    final_products["sell_order_price"][i] = commaify(current_item_data["bazaar_sell_price"])
    final_products["product_margins"][i] = commaify(current_item_data["bazaar_profit"])
    final_products["profit_percentage"][i] = commaify(current_item_data["bazaar_percentage_profit"])
    i += 1
  
  final_products = pd.DataFrame({"Item": final_products["item_name"], "Product Margin": final_products["product_margins"], "Profit %": final_products["profit_percentage"], "Buy Price": final_products["buy_order_price"], "Sell Price": final_products["sell_order_price"]})
  
  return final_products


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
  print(itemname)
  return db[itemname]["auctionable"]


def render_item(itemname):
  return db[itemname]["link"]


def isBazaarable(itemname):
  return db[itemname]["bazaarable"]


def get_lowest_bin(itemname, count):
  if db[itemname]["auctionable"] and "lowest_bin" in db[itemname]:
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
  database = db
  with open("./constants/forgables.json") as forgables:
    forgables = json.load(forgables)
  #declares so many goddamn variables

  for item in forgables:
    current_item_data = database[item]
    final_flips["id"][i] = item
    final_flips["image"][i] = f"<img src={current_item_data['image']}>"
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
  with open("items.json", "r") as items2:
    items2 = json.load(items2)

  try:
    return list(items2.keys())[list(items2.values()).index(itemname)]
  except KeyError:
    return "AMMONITE;4"
  except ValueError:
    return itemname
  

def id_to_name(itemname):
  with open("items.json", "r") as items2:
    items2 = json.load(items2)

  try:
    return items2[itemname]
  except:
    return "Ammonite Pet"

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
    return await resp.json()

#---------------------------------------------------------------------------------------------------------
#SUBPROGRAMS
#---------------------------------------------------------------------------------------------------------

# database_updater
asyncio.run(dynamic_database_updater())
# deletion_time()