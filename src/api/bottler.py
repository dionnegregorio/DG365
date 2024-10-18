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
    ml_green = 0
    deliv_red = 0
    ml_red = 0
    deliv_blue = 0
    ml_blue = 0
    return_statement = []
    
    for potion in potions_delivered:
        if potion.potion_type == [0,100,0,0]:
            deliv_green += potion.quantity
            ml_green = potion.quantity * 100
            print(f"Delivered {deliv_green} green potions")
            return_statement.append(f"Delivered {deliv_green} green potions")
        if potion.potion_type == [100,0,0,0]:
            deliv_red += potion.quantity
            ml_red = potion.quantity * 100
            print(f"Delivered {deliv_red} red potions")
            return_statement.append(f"Delivered {deliv_red} red potions")
        if potion.potion_type == [0,0,100,0]:
            deliv_blue += potion.quantity 
            ml_blue = potion.quantity * 100
            print(f"Delivered {deliv_blue} blue potions")
            return_statement.append(f"Delivered {deliv_blue} blue potions")

    sql_to_execute = """
                    UPDATE global_inventory
                    SET num_green_potions = num_green_potions + :deliv_green,
                        num_green_ml = num_green_ml - :ml_green,
                        num_red_potions = num_red_potions + :deliv_red,
                        num_red_ml = num_red_ml - :ml_red,
                        num_blue_potions = num_blue_potions + :deliv_blue,
                        num_blue_ml = num_blue_ml - :ml_blue
                    """
    sql_to_exc = """
                UPDATE catalog 
                SET quantity
                """
    values = {'deliv_green': deliv_green, 'ml_green' : ml_green, 'deliv_red': deliv_red,
                'ml_red' : ml_red, 'deliv_blue': deliv_blue, 'ml_blue' : ml_blue
             }

    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text(sql_to_execute), values)

    return return_statement

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
        potions = connection.execute(sqlalchemy.text("SELECT sku, quantity, type FROM catalog")).fetchall()

    ml_inv = result.first()  
    red_ml = ml_inv.num_red_ml
    green_can_mix =  ml_inv.num_green_ml // 100
    red_can_mix = ml_inv.num_red_ml // 100
    blue_can_mix = ml_inv.num_blue_ml // 100

    to_mix = []
    """
    get ml inventory from global inventory
    get abount of red inventory from catalog


    """
    print()

    if red_ml >= 500:
        if potions["sku"] == "RED":
            to_mix.append(
                {
                    "potion_type": potions["type"],
                    "quantity": red_can_mix
                }
            )


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