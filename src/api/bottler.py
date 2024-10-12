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

    #for each potion, if green, update inventory set num_green_potions = num_green_potion + potion.quantity
    
    deliv_green = 0
    deliv_red = 0
    deliv_blue = 0
    
    for potion in potions_delivered:
        if potion.potion_type == [0,100,0,0]:
            deliv_green += potion.quantity
        if potion.potion_type == [100,0,0,0]:
            deliv_red += potion.quantity
        if potion.potion_type == [0,0,100,0]:
            deliv_blue += potion.quantity 

    sql_to_execute = """
                    UPDATE global_inventory
                    SET num_green_potions = num_green_potions + :deliv_green,
                        num_red_potions = num_red_potions + :deliv_red,
                        num_blue_potions = num_blue_potions + :deliv_blue
                    """
    values = {'deliv_green': deliv_green, 'deliv_red': deliv_red, 'deliv_blue': deliv_blue}

    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text(sql_to_execute), values)

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
        
        result = connection.execute(sqlalchemy.text("SELECT num_green_ml, num_red_ml, num_blue_ml FROM global_inventory"))

    ml_inv = result.first()  
    green_can_mix =  ml_inv.num_green_ml // 100
    red_can_mix = ml_inv.num_red_ml // 100
    blue_can_mix = ml_inv.num_blue_ml // 100

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
    print(f"bottle plan to mix: {to_mix}")
    return to_mix

if __name__ == "__main__":
    print(get_bottle_plan())