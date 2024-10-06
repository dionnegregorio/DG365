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

    with db.engine.begin() as connection:
        for barrel in barrels_delivered:
            if barrel.potion_type == [0,1,0,0]:
                connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_green_ml = num_green_ml + {barrel.ml_per_barrel * barrel.quantity}"))
                connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET gold = gold - ({barrel.price * barrel.quantity})"))
            elif barrel.potion_type == [1,0,0,0]:
                connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_red_ml = num_red_ml + {barrel.ml_per_barrel * barrel.quantity}"))
                connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET gold = gold - ({barrel.price * barrel.quantity})"))
            elif barrel.potion_type == [0,0,1,0]:
                connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_blue_ml = num_red_ml + {barrel.ml_per_barrel * barrel.quantity}"))
                connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET gold = gold - ({barrel.price * barrel.quantity})"))

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
       
        current_green_potions = connection.execute(sqlalchemy.text("SELECT quantity FROM potion_catalog WHERE name = 'Green Potion'")).scalar()
        current_red_potions = connection.execute(sqlalchemy.text("SELECT quantity FROM potion_catalog WHERE name = 'Red Potion'")).scalar()
        current_blue_potions = connection.execute(sqlalchemy.text("SELECT quantity FROM potion_catalog WHERE name = 'Blue Potion'")).scalar()
        gold_total = connection.execute(sqlalchemy.text("SELECT gold FROM global_inventory")).scalar()

    to_buy_list = []
    num_green_can_buy = 0
    num_red_can_buy = 0
    num_blue_can_buy = 0

    for barrel in wholesale_catalog:
        if barrel.sku == "SMALL_GREEN_BARREL":
            num_green_can_buy = (gold_total // barrel.price)
            if num_green_can_buy >= barrel.quantity:
                num_green_can_buy = barrel.quantity
        if barrel.sku == "SMALL_RED_BARREL":
            num_red_can_buy = (gold_total // barrel.price)
            if num_red_can_buy >= barrel.quantity:
                num_red_can_buy = barrel.quantity
        if barrel.sku == "SMALL_BLUE_BARREL":
            num_blue_can_buy = (gold_total // barrel.price)
            if num_blue_can_buy >= barrel.quantity:
                num_blue_can_buy = barrel.quantity
                
    if current_green_potions < 10 and num_green_can_buy > 0:
        to_buy_list.append({
            "sku": "SMALL_GREEN_BARREL",
            "quantity": num_green_can_buy
            })
            
    if current_red_potions < 10 and num_red_can_buy > 0:
        to_buy_list.append({
            "sku": "SMALL_RED_BARREL",
            "quantity": num_red_can_buy,
            })
        
    if current_blue_potions < 10 and num_blue_can_buy > 0:
        to_buy_list.append({
            "sku": "SMALL_BLUE_BARREL",
            "quantity": num_blue_can_buy,
            })
    
    print(wholesale_catalog)

    return to_buy_list

   