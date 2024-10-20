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
        potions = connection.execute(sqlalchemy.text("SELECT sku, quantity, type FROM catalog ORDER BY id")).mappings()

    ml_inv = result.first()  
    red_ml = ml_inv.num_red_ml
    green_ml = ml_inv.num_green_ml
    blue_ml = ml_inv.num_blue_ml
    total_ml = red_ml + green_ml + blue_ml

    to_mix = []

    """
    get ml inventory from global inventory
    get abount of red inventory from catalo
    """
    print(to_mix)
    print(f"red ml total: {red_ml}")
    print(f"green ml total: {green_ml}")
    print(f"blue ml total: {blue_ml}")

    """
    get ml inventory for each barrel 
    for each potion in the catalog 
        if enough ingredients are available
        calculate how much you can make with that amount
        add plan
    """

    if total_ml > 0: 
        for potion in potions:
            if potion["sku"] == "RED":
                if red_ml > 0 and red_ml <= 500:
                    to_bottle = red_ml // 100
                    to_mix.append({
                                        "potion_type": potion["type"],
                                        "quantity": to_bottle
                                        })
                    print(f"added {potion['type']}, quantity: {to_bottle}")
                    red_ml -= 100 * to_bottle
                    continue
                elif red_ml > 500:
                    to_bottle = red_ml // 100
                    remaining_red = to_bottle - 5
                    to_bottle -= remaining_red
                    to_mix.append({
                                    "potion_type": potion["type"],
                                    "quantity": to_bottle
                                    })
                    print(f"added {potion['type']}, quantity: {to_bottle}")
                    red_ml = remaining_red * 100

            if potion["sku"] == "GREEN":
                if green_ml > 0 and green_ml <= 500:
                    to_bottle = green_ml // 100
                    to_mix.append({
                                        "potion_type": potion["type"],
                                        "quantity": to_bottle
                                        })
                    print(f"added {potion['type']}, quantity: {to_bottle}")
                    green_ml -= 100 * to_bottle
                    continue
                elif green_ml > 500:
                    to_bottle = green_ml // 100
                    remaining_green = to_bottle - 5
                    to_bottle -= remaining_green
                    to_mix.append({
                                    "potion_type": potion["type"],
                                    "quantity": to_bottle
                                    })
                    print(f"added {potion['type']}, quantity: {to_bottle}")

                    green_ml = remaining_green * 100

            if potion["sku"] == "BLUE":
                if blue_ml > 0 and blue_ml <= 500:
                    to_bottle = blue_ml // 100
                    to_mix.append({
                                        "potion_type": potion["type"],
                                        "quantity": to_bottle
                                        })
                    print(f"added {potion['type']}, quantity: {to_bottle}")
                    blue_ml -= 100 * to_bottle
                    continue
                elif blue_ml > 500:
                    to_bottle = blue_ml // 100
                    remaining_blue = to_bottle - 5
                    to_bottle -= remaining_blue
                    to_mix.append({
                                    "potion_type": potion["type"],
                                    "quantity": to_bottle
                                    })
                    print(f"added {potion['type']}, quantity: {to_bottle}")

                    blue_ml = remaining_blue * 100

            if potion["sku"] == "PURPLE":
                    #check if we have red and blue available.
                    #if red > = 50 and blue >= 50: 
                if red_ml >= 50 and blue_ml >= 50:
                    red_mix = red_ml // 50 #ex: 300ml / 50 = 6
                    blue_mix = blue_ml // 50 #ex: 100ml / 50 = 2 
                    if red_mix > blue_mix: 
                        remaining_red = red_mix - blue_mix
                        red_mix = blue_mix
                        to_mix.append({
                                "potion_type": potion["type"],
                                "quantity": red_mix
                                })
                        print(f"added {potion['type']}, quantity: {to_bottle}")

                        blue_ml -= blue_ml
                        print(blue_ml)
                        red_ml = remaining_red * 50
                    elif blue_mix > red_mix:
                        remaining_blue = blue_mix - red_mix
                        blue_mix = red_mix
                        to_mix.append({
                                "potion_type": potion["type"],
                                "quantity": blue_mix
                                })
                        red_ml -= red_ml
                        blue_ml = remaining_blue * 50
                        print(red_ml)

            if potion["sku"] == "YELLOW":
                if red_ml >= 50 and green_ml >= 50:
                    red_mix = red_ml // 50 #ex: 300ml / 50 = 6
                    green_mix = green_ml // 50 #ex: 100ml / 50 = 2 
                    if red_mix > green_mix: 
                        remaining_red = red_mix - green_mix
                        red_mix = green_mix
                        to_mix.append({
                                "potion_type": potion["type"],
                                "quantity": red_mix
                                })
                        print(f"added {potion['type']}, quantity: {to_bottle}")
                        green_ml -= green_ml
                        red_ml = remaining_red * 50
                    elif green_mix > red_mix:
                        remaining_green = blue_mix - red_mix
                        green_mix = red_mix
                        to_mix.append({
                                "potion_type": potion["type"],
                                "quantity": green_mix
                                })
                        print(f"added {potion['type']}, quantity: {to_bottle}")

                        red_ml -= red_ml
                        green_ml = remaining_green * 50
                    
            if potion["sku"] == "TEAL":
                if blue_ml >= 50 and green_ml >= 50:
                    blue_mix = blue_ml // 50 #ex: 300ml / 50 = 6
                    green_mix = green_ml // 50 #ex: 100ml / 50 = 2 
                    if blue_mix > green_mix: 
                        remaining_blue = blue_mix - green_mix
                        blue_mix = green_mix
                        to_mix.append({
                                "potion_type": potion["type"],
                                "quantity": blue_mix
                                })
                        print(f"added {potion['type']}, quantity: {to_bottle}")
                        green_ml -= green_ml
                        blue_ml = remaining_blue * 50
                    elif green_mix > blue_mix:
                        remaining_green = blue_mix - blue_mix
                        green_mix = blue_mix
                        to_mix.append({
                                "potion_type": potion["type"],
                                "quantity": green_mix
                                })
                        print(f"added {potion['type']}, quantity: {to_bottle}")
                        blue_ml -= blue_ml
                        green_ml = remaining_green * 50                                
        
    print(f"bottle plan to mix: {to_mix}")
    return to_mix

if __name__ == "__main__":
    print(get_bottle_plan())