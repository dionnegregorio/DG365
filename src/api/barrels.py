from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/barrels",
    tags=["barrels"],
    dependencies=[Depends(auth.get_api_key)],
)

class Barrel(BaseModel):
    sku: str

    ml_per_barrel: int
    potion_type: list[int]
    price: int

    quantity: int

@router.post("/deliver/{order_id}")
def post_deliver_barrels(barrels_delivered: list[Barrel], order_id: int):
    """ """
    print(f"barrels delievered: {barrels_delivered} order_id: {order_id}")

    #iterate through list of barrels delivered
    #if green barrel is delivered, deliv_ml = current ml + ml delivered 
        #payed = price * quantity

    delivered_green_ml = 0
    delivered_red_ml = 0
    delivered_blue_ml = 0
    delivered_dark_ml = 0
    gold = 0

    for barrel in barrels_delivered:
        if barrel.potion_type == [1,0,0,0]:
            delivered_red_ml += barrel.ml_per_barrel * barrel.quantity
            gold -= barrel.price * barrel.quantity
            print(f"Added {delivered_red_ml} ml to red inventory")
        elif barrel.potion_type == [0,1,0,0]:
            delivered_green_ml += barrel.ml_per_barrel * barrel.quantity
            gold -= barrel.price * barrel.quantity
            print(f"Added {delivered_green_ml} ml to green inventory")
        elif barrel.potion_type == [0,0,1,0]:
            delivered_blue_ml += barrel.ml_per_barrel * barrel.quantity
            gold -= barrel.price * barrel.quantity
            print(f"Added {delivered_blue_ml} ml to blue inventory")
        elif barrel.potion_type == [0,0,0,1]:
            delivered_dark_ml += barrel.ml_per_barrel * barrel.quantity
            gold -= barrel.price * barrel.quantity
            print(f"Added {delivered_dark_ml} ml to dark inventory")

    sql2 = """
            INSERT INTO barrel_ledger 
                (red_ml, green_ml, blue_ml, dark_ml, gold)
            VALUES 
                (:red_ml, :green_ml, :blue_ml, :dark_ml, :gold)
            """
    
    values = {'red_ml': delivered_red_ml, 'green_ml': delivered_green_ml, 'blue_ml': delivered_blue_ml, 'dark_ml': delivered_dark_ml, 'gold': gold}

    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text(sql2), values)

    print(f"Added barrels")
    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):

    """purchase barrels"""
    
    print(wholesale_catalog)

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("""
            SELECT 
                SUM(red_ml) as red_ml,
                SUM(green_ml) as green_ml,
                SUM(blue_ml) as blue_ml,
                SUM(dark_ml) as dark_ml,
                SUM(gold) as gold
            FROM barrel_ledger
            """)).first()
        
    to_buy_list = []
    ml_cap = 10000
    red_ml = result.red_ml
    green_ml = result.green_ml
    blue_ml = result.blue_ml
    dark_ml = result.dark_ml
    gold_total = result.gold
    budget = 0

    if gold_total <= 100:
        budget = gold_total
    else:
        budget = gold_total * 0.6

    print(f"total gold budget: {budget}")
    print(f"current capacity: {ml_cap}")

    if budget <= 0:
        print("NOT ENOUGH GOLD")
        return []
    
    elif budget >= 100 and ml_cap > 500:

        for barrel in wholesale_catalog:

            if barrel.sku == "SMALL_RED_BARREL" and red_ml < 500 and budget >= 100:
                capacity = ml_cap // 3 - red_ml 
                available_barrels = capacity // barrel.ml_per_barrel
                can_afford = budget // barrel.price
                barrels_can_buy = min(available_barrels, can_afford)
                budget -= barrel.price * barrels_can_buy

                if barrels_can_buy > 5:
                    barrels_can_buy = 5 #max buy 5 barrels
                budget -= (barrels_can_buy * barrel.price)
                to_buy_list.append({
                        "sku": "SMALL_RED_BARREL",
                        "quantity": barrels_can_buy,
                        })
                
            if barrel.sku == "SMALL_GREEN_BARREL" and green_ml < 500 and budget >= 100:
                capacity = ml_cap // 3 - green_ml
                available_barrels = capacity // barrel.ml_per_barrel
                can_afford = budget // barrel.price
                barrels_can_buy = min(available_barrels, can_afford)
                budget -= barrel.price * barrels_can_buy

                if barrels_can_buy > 5:
                    barrels_can_buy = 5
                budget -= (barrels_can_buy * barrel.price)
                to_buy_list.append({
                        "sku": "SMALL_GREEN_BARREL",
                        "quantity": barrels_can_buy,
                        })
                
            if barrel.sku == "SMALL_BLUE_BARREL" and  blue_ml < 500 and budget >= 120:
                capacity = ml_cap // 3 - blue_ml
                available_barrels = capacity // barrel.ml_per_barrel
                can_afford = budget // barrel.price
                barrels_can_buy = min(available_barrels, can_afford)
                budget -= barrel.price * barrels_can_buy

                if barrels_can_buy > 5:
                    barrels_can_buy = 5
                gold_total -= (barrels_can_buy * barrel.price)
                to_buy_list.append({
                        "sku": "SMALL_BLUE_BARREL",
                        "quantity": barrels_can_buy,
                        })

                      
    print(f"Barrels to buy: {to_buy_list}")

    return to_buy_list


"""
[Barrel(sku='SMALL_RED_BARREL', ml_per_barrel=500, potion_type=[1, 0, 0, 0], price=100, quantity=10), 
Barrel(sku='SMALL_GREEN_BARREL', ml_per_barrel=500, potion_type=[0, 1, 0, 0], price=100, quantity=10),
 Barrel(sku='SMALL_BLUE_BARREL', ml_per_barrel=500, potion_type=[0, 0, 1, 0], price=120, quantity=10), 

 Barrel(sku='LARGE_DARK_BARREL', ml_per_barrel=10000, potion_type=[0, 0, 0, 1], price=750, quantity=10), 
 Barrel(sku='LARGE_BLUE_BARREL', ml_per_barrel=10000, potion_type=[0, 0, 1, 0], price=600, quantity=30), 
 Barrel(sku='LARGE_GREEN_BARREL', ml_per_barrel=10000, potion_type=[0, 1, 0, 0], price=400, quantity=30),
Barrel(sku='LARGE_RED_BARREL', ml_per_barrel=10000, potion_type=[1, 0, 0, 0], price=500, quantity=30)]


 Barrel(sku='MINI_RED_BARREL', ml_per_barrel=200, potion_type=[1, 0, 0, 0], price=60, quantity=1), 
 Barrel(sku='MINI_GREEN_BARREL', ml_per_barrel=200, potion_type=[0, 1, 0, 0], price=60, quantity=1), 
 Barrel(sku='MINI_BLUE_BARREL', ml_per_barrel=200, potion_type=[0, 0, 1, 0], price=60, quantity=1), 
"""

#dont need to reference potion quantity 
"""
    for column in potion_quants:
         if column['sku'] == "RED":
              print(column['sku'])
              print(column["quantity"])
                red_ml
         = column['quantity']
         if column["sku"] == "GREEN":
              print(column['sku'])
              print(column["quantity"])
ml= column['quantity']
         if column["sku"] == "BLUE":
              print(column['sku'])
              print(column["quantity"])
                blue_ml = column['quantity']
    """
