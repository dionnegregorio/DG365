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
    payed = 0

    for barrel in barrels_delivered:
        if barrel.sku == "SMALL_GREEN_BARREL":
            delivered_green_ml += barrel.ml_per_barrel * barrel.quantity
            payed += barrel.price * barrel.quantity
            print(f"Added {delivered_green_ml} ml to green inventory")
        if barrel.sku == "SMALL_RED_BARREL":
            delivered_red_ml += barrel.ml_per_barrel * barrel.quantity
            payed += barrel.price * barrel.quantity
            print(f"Added {delivered_red_ml} ml to red inventory")
        if barrel.sku == "SMALL_BLUE_BARREL":
            delivered_blue_ml += barrel.ml_per_barrel * barrel.quantity
            payed += barrel.price * barrel.quantity
            print(f"Added {delivered_blue_ml} ml to blue inventory")

    sql_to_execute = """ 
                    UPDATE global_inventory 
                    SET num_green_ml = num_green_ml + :green_ml,
                        num_red_ml = num_red_ml + :red_ml,
                        num_blue_ml = num_blue_ml + :blue_ml,
                        gold = gold - :payed
                    """
    values = {'green_ml': delivered_green_ml, 'red_ml': delivered_red_ml, 'blue_ml': delivered_blue_ml, 'payed': payed}

    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text(sql_to_execute), values)

    print(f"Added barrels")
    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):

    """purchase a new small green potion barrel only if the potions 
    in inventory is less than 10. Always mix all available green ml 
     if any exists. Offer up for sale in the catalog only the amount 
     of green potions that actually exist currently in inventory."""
    
    print(wholesale_catalog)

    #get number of current green potions
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory"))
        #potion_quants = connection.execute(sqlalchemy.text("SELECT sku, quantity FROM catalog WHERE id = '1' OR id = '2' OR id = '3' ORDER BY id")).mappings()
    
    inventory = result.first()
    to_buy_list = []
    red_ml = inventory.num_red_ml
    green_ml = inventory.num_green_ml
    blue_ml = inventory.num_blue_ml
    gold_total = inventory.gold

    current_ml = red_ml + green_ml + blue_ml
    current_cap = inventory.ml_capacity - current_ml

    print(gold_total)
    print(current_cap)

    #get current amount of red, green and blue potions
    #buy if ml is less than 500ml

    if gold_total <= 0:
        print("NOT ENOUGH GOLD")
        return []
    
    elif gold_total >= 100 and current_cap > 100:
        for barrel in wholesale_catalog:
            if barrel.sku == "SMALL_RED_BARREL" and red_ml < 1000 and gold_total >= 100:
                barrels_can_buy = gold_total // barrel.price 
                if barrels_can_buy > 10:
                    barrels_can_buy = 10
                    gold_total -= (barrels_can_buy * barrel.price)
                    to_buy_list.append({
                        "sku": "SMALL_RED_BARREL",
                        "quantity": barrels_can_buy,
                        })
            elif barrel.sku == "SMALL_GREEN_BARREL" and green_ml < 1000 and gold_total >= 100:
                barrels_can_buy = gold_total // barrel.price 
                if barrels_can_buy > 10:
                    barrels_can_buy = 10
                    gold_total -= (barrels_can_buy * barrel.price)
                    to_buy_list.append({
                            "sku": "SMALL_GREEN_BARREL",
                            "quantity": barrels_can_buy,
                            })
            elif barrel.sku == "SMALL_BLUE_BARREL" and  blue_ml < 1000 and gold_total >= 120:
                barrels_can_buy = gold_total // barrel.price 
                if barrels_can_buy > 10:
                    barrels_can_buy = 10
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

 Barrel(sku='MINI_RED_BARREL', ml_per_barrel=200, potion_type=[1, 0, 0, 0], price=60, quantity=1), 
 Barrel(sku='MINI_GREEN_BARREL', ml_per_barrel=200, potion_type=[0, 1, 0, 0], price=60, quantity=1), 
 Barrel(sku='MINI_BLUE_BARREL', ml_per_barrel=200, potion_type=[0, 0, 1, 0], price=60, quantity=1), 

 
 Barrel(sku='LARGE_DARK_BARREL', ml_per_barrel=10000, potion_type=[0, 0, 0, 1], price=750, quantity=10), 
 Barrel(sku='LARGE_BLUE_BARREL', ml_per_barrel=10000, potion_type=[0, 0, 1, 0], price=600, quantity=30), 
 Barrel(sku='LARGE_GREEN_BARREL', ml_per_barrel=10000, potion_type=[0, 1, 0, 0], price=400, quantity=30),
Barrel(sku='LARGE_RED_BARREL', ml_per_barrel=10000, potion_type=[1, 0, 0, 0], price=500, quantity=30)]
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
