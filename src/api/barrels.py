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

    with db.engine.begin() as connection:
        gold = connection.execute(sqlalchemy.text("SELECT gold FROM global_inventory")).scalar()

    
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
        potion_quants = connection.execute(sqlalchemy.text("SELECT sku, quantity FROM catalog WHERE id = '1' OR id = '2' OR id = '3' ORDER BY id")).mappings()
    
    inventory = result.first()
    to_buy_list = []
    red_potion = 0
    green_potion = 0
    blue_potion = 0
    gold_total = inventory.gold

    current_ml = inventory.num_green_ml + inventory.num_red_ml + inventory.num_blue_ml
    current_cap = inventory.ml_capacity - current_ml

    print(gold_total)
    print(current_cap)

    #get current amount of red, green and blue potions
    for column in potion_quants:
         if column['sku'] == "RED":
              print(column['sku'])
              print(column["quantity"])
              red_potion = column['quantity']
         if column["sku"] == "GREEN":
              print(column['sku'])
              print(column["quantity"])
              green_potion = column['quantity']
         if column["sku"] == "BLUE":
              print(column['sku'])
              print(column["quantity"])
              blue_potion = column['quantity']

    print(f"red: {red_potion}, green: {green_potion} , blue: {blue_potion} ")

    #get amount of ml and potion storage i have left
    #if num of red potions is less than 5, then buy a small red barrel cost 100gold 5000ml = 5 potions
    #after selling potions,

    if gold_total <= 0:
        print("NOT ENOUGH GOLD")
        return ["NOT ENOUGH GOLD, BUYING NONE"]
    
    elif gold_total >= 100 and current_cap > 100:
        for barrel in wholesale_catalog:
            if barrel.sku == "SMALL_RED_BARREL" and red_potion < 5:
                    gold_total -= 100 
                    to_buy_list.append({
                        "sku": "SMALL_RED_BARREL",
                        "quantity": 1,
                        })
            elif barrel.sku == "SMALL_GREEN_BARREL" and green_potion < 5:
                    gold_total -= 100
                    to_buy_list.append({
                        "sku": "SMALL_GREEN_BARREL",
                        "quantity": 1,
                        })
            elif barrel.sku == "SMALL_BLUE_BARREL" and blue_potion < 5 and gold_total >= 120:
                    gold_total -= 120
                    to_buy_list.append({
                        "sku": "SMALL_BLUE_BARREL",
                        "quantity": 1,
                        })
                      
    print(f"Barrels to buy: {to_buy_list}")

    return to_buy_list
