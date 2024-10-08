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
                connection.execute(sqlalchemy.text(f"""
                                            UPDATE 
                                                global_inventory SET num_green_ml = num_green_ml + {barrel.ml_per_barrel * barrel.quantity},
                                                gold = gold - ({barrel.price * barrel.quantity})
                                            """))
            elif barrel.potion_type == [1,0,0,0]:
                connection.execute(sqlalchemy.text(f"""
                                            UPDATE 
                                                global_inventory SET num_red_ml = num_red_ml + {barrel.ml_per_barrel * barrel.quantity},
                                                gold = gold - ({barrel.price * barrel.quantity})
                                            """))
            elif barrel.potion_type == [0,0,1,0]:
                connection.execute(sqlalchemy.text(f"""
                                            UPDATE 
                                                global_inventory SET num_blue_ml = num_blue_ml + {barrel.ml_per_barrel * barrel.quantity},
                                                gold = gold - ({barrel.price * barrel.quantity})
                                            """))
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
        if barrel.sku == "SMALL_GREEN_POTION":
            if inventory.num_green_potions < 10 and gold_total >= 100:
                gold_total -= 100
                to_buy_list.append({
                    "sku": "SMALL_GREEN_BARREL",
                    "quantity": 1,
                    })
            else: 
                return "NOT ENOUGH GOLD"
        elif barrel.sku == "SMALL_RED_POTION":
            if inventory.num_red_potions < 10 and gold_total >= 100:
                gold_total -= 100
                to_buy_list.append({
                    "sku": "SMALL_RED_BARREL",
                    "quantity": 1,
                    })
            else: 
                return "NOT ENOUGH GOLD"
        elif barrel.sku == "SMALL_BLUE_POTION":
            if inventory.num_blue_potions < 10 and gold_total >= 120:
                gold_total -= 120
                to_buy_list.append({
                    "sku": "SMALL_BLUE_BARREL",
                    "quantity": 1,
                    })
            else: 
                return "NOT ENOUGH GOLD"

    print(wholesale_catalog)

    return to_buy_list