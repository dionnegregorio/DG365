"""with db.engine.begin() as connection:
        num_green_potion = connection.execute(sqlalchemy.text("SELECT num_green_potions FROM global_inventory")).scalar()
        gold = connection.execute(sqlalchemy.text("SELECT gold FROM global_inventory"))  
        num_green_potion = num_green_potion.first()
        gold = gold.first()

    inventory = {  
        "Green_ml" : num_green_potion
        #"Red_ml" : num_red_potion
       #"Blue_ml" : num_blue_potion
    }

    barrel_plan = []

    for barrel in wholesale_catalog:
        if barrel.sku.upper() != "SMALL_GREEN_BARREL": #and num_green_potion < 10:
            return [
                {"sku": "SMALL_GREEN_BARREL", "quantity": 5}
                ]
        else: 
            return [
                {"sku": "SMALL_GREEN_BARREL", "quantity": 5}
                ]
            
            amount_can_buy = gold // barrel.price
            if amount_can_buy <= 0:
                continue
            if amount_can_buy >= barrel.quantity:
                amount_can_buy = barrel.quantity
                barrel_plan.append({"sku": barrel.sku, "quantity": amount_can_buy})
            else: 
                barrel_plan.append({"sku": barrel.sku, "quantity": amount_can_buy})
    #return barrel_plan
    """
        

    #for barrel plan old inventory
"""current_green_potions = connection.execute(sqlalchemy.text("SELECT num_green_potions FROM global_inventory")).scalar()
        current_red_potions = connection.execute(sqlalchemy.text("SELECT num_red_potions FROM global_inventory")).scalar()
        current_blue_potions = connection.execute(sqlalchemy.text("SELECT num_blue_potions FROM global_inventory")).scalar()
        gold_total = connection.execute(sqlalchemy.text("SELECT gold FROM global_inventory")).scalar()
"""
#barrel plan
"""num_green_can_buy = 0
    num_red_can_buy = 0
    num_blue_can_buy = 0"""

""" num_green_can_buy = (gold_total // barrel.price)
            if num_green_can_buy > barrel.quantity:
                num_green_can_buy = barrel.quantity
            else: 
                num_green_can_buy = 1"""
""" #loop to see the num of barrels i can buy
for barrel in wholesale_catalog:
    if barrel.sku == "SMALL_GREEN_BARREL":
        #green_price = barrel.price
        if inventory.num_green_potions < 10 and gold_total >= barrel.price:
            gold_total -= barrel.price
            to_buy_list.append({
                "sku": "SMALL_GREEN_BARREL",
                "quantity": 1,
                })
    if barrel.sku == "SMALL_RED_BARREL":
        #red_price = barrel.price
        if inventory.num_red_potions < 10 and gold_total >= barrel.price:
            gold_total -= barrel.price
            to_buy_list.append({
                "sku": "SMALL_RED_BARREL",
                "quantity": 1,
                })
    if barrel.sku == "SMALL_BLUE_BARREL":
        #blue_price = barrel.price
        if inventory.num_blue_potions < 10 and gold_total >= barrel.price:
            gold_total -= barrel.price
            to_buy_list.append({
                "sku": "SMALL_BLUE_BARREL",
                "quantity": 1,
                })
            """

""" for potion in potions_delivered:
        delivered_in_ml = potion.quantity * 100
        if potion.potion_type == [0,1,0,0]:
            if inventory.num_green_ml >= delivered_in_ml:
                connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_green_potions = num_green_potions + {potion.quantity}, num_green_ml = num_green_ml - {delivered_in_ml}"))
                #connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_green_ml = num_green_ml - {delivered_in_ml}"))
        if potion.potion_type == [1,0,0,0]:
            if inventory.num_red_ml  >= delivered_in_ml:
                connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_red_potions = num_red_potions + {potion.quantity}, num_red_ml = num_red_ml - {delivered_in_ml}"))
        if potion.potion_type == [0,0,1,0]:
            if inventory.num_green_ml >= delivered_in_ml:
                connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_blue_potions = num_blue_potions + {potion.quantity}, num_blue_ml = num_blue_ml - {delivered_in_ml}"))
"""