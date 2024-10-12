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
            print(f"Added {delivered_green_ml} ml to red inventory and payed {payed} gold")
        if barrel.sku == "SMALL_RED_BARREL":
            delivered_red_ml += barrel.ml_per_barrel * barrel.quantity
            payed += barrel.price * barrel.quantity
            print(f"Added {delivered_red_ml} ml to green inventory and payed {payed} gold")
        if barrel.sku == "SMALL_BLUE_BARREL":
            delivered_blue_ml += barrel.ml_per_barrel * barrel.quantity
            payed += barrel.price * barrel.quantity
            print(f"Added {delivered_blue_ml} ml to blue inventory and payed {payed} gold")

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

    inventory = result.first()
    to_buy_list = []
    gold_total = inventory.gold

    for barrel in wholesale_catalog:
        if barrel.sku == "SMALL_GREEN_BARREL":
            if inventory.num_green_potions < 10 and gold_total >= 100:
                gold_total -= 100
                to_buy_list.append({
                    "sku": "SMALL_GREEN_BARREL",
                    "quantity": 1,
                    })
        elif barrel.sku == "SMALL_RED_BARREL":
            if inventory.num_red_potions < 10 and gold_total >= 100:
                gold_total -= 100
                to_buy_list.append({
                    "sku": "SMALL_RED_BARREL",
                    "quantity": 1,
                    })
        elif barrel.sku == "SMALL_BLUE_BARREL":
            if inventory.num_blue_potions < 10 and gold_total >= 120:
                gold_total -= 120
                to_buy_list.append({
                    "sku": "SMALL_BLUE_BARREL",
                    "quantity": 1,
                    })
                
    print(f"catalog: {wholesale_catalog}")
    print(f"barrels to buy: {to_buy_list}")

    return to_buy_list
