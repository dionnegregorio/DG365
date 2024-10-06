from fastapi import APIRouter, Depends
from enum import Enum
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/bottler",
    tags=["bottler"],
    dependencies=[Depends(auth.get_api_key)],
)

class PotionInventory(BaseModel):
    potion_type: list[int]
    quantity: int

@router.post("/deliver/{order_id}")
def post_deliver_bottles(potions_delivered: list[PotionInventory], order_id: int):
    """ """
    print(f"potions delievered: {potions_delivered} order_id: {order_id}")

    with db.engine.begin() as connection:
        green_ml= connection.execute(sqlalchemy.text("SELECT num_green_ml FROM global_inventory")).scalar()
        red_ml = connection.execute(sqlalchemy.text("SELECT num_red_ml FROM global_inventory")).scalar()
        blue_ml = connection.execute(sqlalchemy.text("SELECT num_blue_ml FROM global_inventory")).scalar()

    for potion in PotionInventory:
        delivered_in_ml = potion.quantity * 100
        if potion.type == [0,1,0,0]:
            if green_ml >= delivered_in_ml:
                connection.execute(sqlalchemy.text(f"UPDATE potion_catalog SET quantity = quantity + {potion.quantity} WHERE name = 'Green Potion'"))
                connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_green_ml = num_green_ml - {delivered_in_ml}"))
        if potion.type == [1,0,0,0]:
            if red_ml >= delivered_in_ml:
                connection.execute(sqlalchemy.text(f"UPDATE potion_catalog SET quantity = quantity + {potion.quantity} WHERE name = 'Red Potion'"))
                connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_red_ml = num_green_ml - {delivered_in_ml}"))
        if potion.type == [0,0,1,0]:
            if blue_ml >= delivered_in_ml:
                connection.execute(sqlalchemy.text(f"UPDATE potion_catalog SET quantity = quantity + {potion.quantity} WHERE name = 'Blue Potion'"))
                connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_blue_ml = num_green_ml - {delivered_in_ml}"))

    return "OK"

@router.post("/plan")
def get_bottle_plan():
    """
    Go from barrel to bottle.
    """
    # Each bottle has a quantity of what proportion of red, blue, and
    # green potion to add.
    # Expressed in integers from 1 to 100 that must sum up to 100.

    # Initial logic: bottle all barrels into green  potions.
    with db.engine.begin() as connection:
        green_ml= connection.execute(sqlalchemy.text("SELECT num_green_ml FROM global_inventory")).scalar()
        red_ml = connection.execute(sqlalchemy.text("SELECT num_red_ml FROM global_inventory")).scalar()
        blue_ml = connection.execute(sqlalchemy.text("SELECT num_blue_ml FROM global_inventory")).scalar()
        
    green_can_mix = green_ml // 100
    red_can_mix = red_ml // 100
    blue_can_mix = blue_ml // 100

    to_mix = []

    if green_can_mix > 0:                           
        to_mix.append(
            {
                "potion_type": [0, 100, 0, 0],
                "quantity": green_can_mix
            }
        )
    if red_can_mix > 0:                           
        to_mix.append(
            {
                "potion_type": [100, 0, 0, 0],
                "quantity": red_can_mix
            }
        )
    if blue_can_mix > 0:                           
        to_mix.append(
        {
            "potion_type": [0, 0, 100, 0],
            "quantity": blue_can_mix
        }
    )
    
    return to_mix

if __name__ == "__main__":
    print(get_bottle_plan())