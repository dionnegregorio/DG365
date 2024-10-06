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
