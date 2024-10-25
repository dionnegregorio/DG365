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
    print(f"potions to deliver: {potions_delivered} order_id: {order_id}")

    #for each potion, if green, update inventory set num_green_potions = num_green_potion + potion.quantity
    
    ml_green = ml_red = ml_blue = ml_dark = 0
    deliv_red = 0
    deliv_green = 0
    deliv_blue = 0
    deliv_purp = 0
    deliv_yellow = 0
    deliv_teal = 0
    
    for potion in potions_delivered:
        print(f"potion: {potion.potion_type}, quantity: {potion.quantity}")
        print(potion.quantity)

        red = potion.potion_type[0] * potion.quantity
        green = potion.potion_type[1] *  potion.quantity
        blue = potion.potion_type[2] * potion.quantity
        #dark = potion.potion_type[3] * potion.quantity
        
        match potion.potion_type:
            case [100,0,0,0]:
                deliv_red += potion.quantity
                ml_red += red
            case [0,100,0,0]:
                deliv_green += potion.quantity
                ml_green += green
            case [0,0,100,0]:
                deliv_blue += potion.quantity
                ml_blue += blue   
            case [50,50,0,0]:
                deliv_yellow += potion.quantity
                ml_red += red
                ml_green += green
            case [50,0,50,0]:
                deliv_purp += potion.quantity
                ml_red += red
                ml_blue += blue
            case [0,50,50,0]:
                deliv_teal += potion.quantity
                ml_green += green
                ml_blue += blue


    sql_to_execute = """
                    UPDATE catalog
                    SET quantity = CASE sku
                        WHEN 'RED' THEN quantity + :deliv_red
                        WHEN 'GREEN' THEN quantity + :deliv_green
                        WHEN 'BLUE' THEN quantity + :deliv_blue
                        WHEN 'YELLOW' THEN quantity + :deliv_yellow
                        WHEN 'PURPLE' THEN quantity + :deliv_purp
                        WHEN 'TEAL' THEN quantity + :deliv_teal
                        ELSE quantity
                    END
                    WHERE sku IN ('RED', 'GREEN', 'BLUE', 'YELLOW', 'PURPLE', 'TEAL');

                    UPDATE global_inventory
                    SET num_red_ml = num_red_ml - :ml_red,
                        num_green_ml = num_green_ml - :ml_green,
                        num_blue_ml = num_blue_ml - :ml_blue
                    """

    values = {'deliv_red': deliv_red, 'deliv_green': deliv_green, 'deliv_blue': deliv_blue,
                'deliv_yellow': deliv_yellow, 'deliv_purp': deliv_purp, 'deliv_teal': deliv_teal,
                'ml_red': ml_red , 'ml_green': ml_green, 'ml_blue': ml_blue
              }
    
    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text(sql_to_execute), values)

    print(f"delivered: {deliv_red} red, {deliv_green} green, {deliv_blue} blue, {deliv_yellow} yellow, {deliv_purp} purple, {deliv_teal} teal")

    return "successfully delivered"


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
        
        result = connection.execute(sqlalchemy.text("SELECT num_green_ml, num_red_ml, num_blue_ml, potion_capacity, ml_capacity FROM global_inventory"))
        potions = connection.execute(sqlalchemy.text("SELECT sku, quantity, potion_type FROM catalog ORDER BY id")).mappings()

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
    print(f"red ml total: {red_ml}")
    print(f"green ml total: {green_ml}")
    print(f"blue ml total: {blue_ml}")

    for row in potions: 

        potion_type = row["potion_type"] 
        print(potion_type)
        to_bottle_pure_blue = 0
        to_bottle_pure_green = 0
        to_bottle_pure_red = 0
        remaining_red = remaining_green = remaining_blue = 0

        if potion_type[0] > 0: #if red 
            to_bottle_pure_red = red_ml // potion_type[0]  #divide by req amount
            if to_bottle_pure_red > 10:
                remaining_red = to_bottle_pure_red - 10
                to_bottle_pure_red -= remaining_red
        if potion_type[1] > 0:
            to_bottle_pure_green = green_ml // potion_type[1] #divide by req amount
            if to_bottle_pure_green > 10:
                remaining_green = to_bottle_pure_green - 10
                to_bottle_pure_green -= remaining_green
        if potion_type[2] > 0:
            to_bottle_pure_blue = blue_ml // potion_type[2]
            if to_bottle_pure_blue > 10:
                remaining_blue = to_bottle_pure_blue - 10
                to_bottle_pure_blue -= remaining_blue
            

        if to_bottle_pure_red > 0 and potion_type[0] == 100: #red
            print(f"added {potion_type}, quantity: {to_bottle_pure_red}")
            to_mix.append({
                "potion_type": potion_type,
                "quantity": to_bottle_pure_red
            })
            red_ml -= to_bottle_pure_red * 100
            print(f"{red_ml}ml of red remaining")
            to_bottle_pure_red = red_ml // 50 
            print(to_bottle_pure_red)
            continue


        if to_bottle_pure_green > 0 and potion_type[1] == 100: #green
            print(f"added {potion_type}, quantity: {to_bottle_pure_green}")
            to_mix.append({
                "potion_type": potion_type,
                "quantity": to_bottle_pure_green
            })
            green_ml -= to_bottle_pure_green * 100
            print(f"{green_ml}ml of red remaining")
            to_bottle_pure_green = green_ml // 50
            print(to_bottle_pure_green)
            continue


        if to_bottle_pure_red > 0 and to_bottle_pure_green > 0 and potion_type[2] == 0:  #yellow
            if to_bottle_pure_red > to_bottle_pure_green:
                to_bottle_pure_red = to_bottle_pure_green
                print(f"added {potion_type}, quantity: {to_bottle_pure_red}")
                to_mix.append({
                "potion_type": potion_type,
                "quantity": to_bottle_pure_red
                })
                red_ml -= to_bottle_pure_red * 50
                green_ml -= to_bottle_pure_red * 50
                continue
            else: 
                to_bottle_pure_green = to_bottle_pure_red
                print(f"added {potion_type}, quantity: {to_bottle_pure_green}")
                to_mix.append({
                "potion_type": potion_type,
                "quantity": to_bottle_pure_green
                })
                red_ml -= to_bottle_pure_green * 50
                green_ml -= to_bottle_pure_green * 50
                continue


        if to_bottle_pure_blue > 0 and potion_type[2] == 100:
            print(f"added {potion_type}, quantity: {to_bottle_pure_blue}")
            to_mix.append({
                "potion_type": potion_type,
                "quantity": to_bottle_pure_blue
            })
            blue_ml -= to_bottle_pure_blue * 100
            print(f"{blue_ml}ml of blue ramaining")
            to_bottle_pure_blue = blue_ml // 50
            print(to_bottle_pure_blue)
            continue


        if to_bottle_pure_red > 0 and to_bottle_pure_blue > 0 and potion_type[1] == 0: #purple
            if to_bottle_pure_red > to_bottle_pure_blue:
                to_bottle_pure_red = to_bottle_pure_blue
                print(f"added {potion_type}, quantity: {to_bottle_pure_red}")
                to_mix.append({
                "potion_type": potion_type,
                "quantity": to_bottle_pure_red
                })
                red_ml -= to_bottle_pure_red * 50
                blue_ml -= to_bottle_pure_red * 50
                continue
            else: 
                to_bottle_pure_green = to_bottle_pure_red
                print(f"added {potion_type}, quantity: {to_bottle_pure_blue}")
                to_mix.append({
                "potion_type": potion_type,
                "quantity": to_bottle_pure_blue
                })
                red_ml -= to_bottle_pure_blue * 50
                blue_ml -= to_bottle_pure_blue * 50
                continue


        if to_bottle_pure_green > 0 and to_bottle_pure_blue > 0 and potion_type[0] == 0: #teal 
            if to_bottle_pure_green > to_bottle_pure_blue:
                to_bottle_pure_green = to_bottle_pure_blue
                print(f"added {potion_type}, quantity: {to_bottle_pure_green}")
                to_mix.append({
                "potion_type": potion_type,
                "quantity": to_bottle_pure_green
                })
                green_ml -= to_bottle_pure_green * 50
                blue_ml -= to_bottle_pure_green * 50
                continue
            else: 
                to_bottle_pure_blue = to_bottle_pure_green
                print(f"added {potion_type}, quantity: {to_bottle_pure_blue}")
                to_mix.append({
                "potion_type": potion_type,
                "quantity": to_bottle_pure_blue
                })
                green_ml -= to_bottle_pure_blue * 50
                blue_ml -= to_bottle_pure_blue * 50
                continue
        

    print(f"bottle plan to mix: {to_mix}")
    return to_mix

if __name__ == "__main__":
    print(get_bottle_plan())

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
                        green_ml = remaining_green * 50 """                           
        
    