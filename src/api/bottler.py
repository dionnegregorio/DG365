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

    ml_green = ml_red = ml_blue = ml_dark = 0
    deliv_red = 0
    deliv_green = 0
    deliv_blue = 0
    deliv_purp = 0
    deliv_yellow = 0
    deliv_orange = 0
    
    for potion in potions_delivered:
        print(f"potion: {potion.potion_type}, quantity: {potion.quantity}")

        red = potion.potion_type[0] * potion.quantity
        green = potion.potion_type[1] *  potion.quantity
        blue = potion.potion_type[2] * potion.quantity
        dark = potion.potion_type[3] * potion.quantity
        
        match potion.potion_type:
            case [100,0,0,0]:
                deliv_red += potion.quantity
                ml_red -= red
            case [0,100,0,0]:
                deliv_green += potion.quantity
                ml_green -= green
            case [0,0,100,0]:
                deliv_blue += potion.quantity
                ml_blue -= blue   
            case [50,50,0,0]:
                deliv_yellow += potion.quantity
                ml_red -= red
                ml_green -= green
            case [50,0,50,0]:
                deliv_purp += potion.quantity
                ml_red -= red
                ml_blue -= blue
            case [75,0,25,0]: 
                deliv_orange += potion.quantity
                ml_red -= red
                ml_green -= green


    sql_to_execute = """
                    UPDATE potion_ledger
                    SET quantity = CASE sku
                        WHEN 'RED' THEN quantity + :deliv_red
                        WHEN 'GREEN' THEN quantity + :deliv_green
                        WHEN 'BLUE' THEN quantity + :deliv_blue
                        WHEN 'YELLOW' THEN quantity + :deliv_yellow
                        WHEN 'PURPLE' THEN quantity + :deliv_purp
                        WHEN 'ORANGE' THEN quantity + :deliv_orange
                        ELSE quantity
                    END
                    WHERE sku IN ('RED', 'GREEN', 'BLUE', 'YELLOW', 'PURPLE', 'ORANGE', 'DARK');

                    INSERT INTO barrel_ledger
                        (red_ml, green_ml, blue_ml, dark_ml)
                    VALUES
                        (:ml_red, :ml_green, :ml_blue, :ml_dark)
                    """

    values = {'deliv_red': deliv_red, 'deliv_green': deliv_green, 'deliv_blue': deliv_blue,
                'deliv_yellow': deliv_yellow, 'deliv_purp': deliv_purp, 'deliv_orange': deliv_orange,
                'ml_red': ml_red , 'ml_green': ml_green, 'ml_blue': ml_blue, 'ml_dark': ml_dark
              }
    
    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text(sql_to_execute), values)

    print(f"delivered: {deliv_red} red, {deliv_green} green, {deliv_blue} blue, {deliv_yellow} yellow, {deliv_purp} purple")

    return "successfully delivered"


def calculate_bottled_quantity(color_ml, color_needed, max_bottle = 10):
    if color_needed > 0:
        bottled_quantity = color_ml // color_needed
        return min(bottled_quantity, max_bottle)
    return 0


@router.post("/plan")
def get_bottle_plan():
    """
    Go from barrel to bottle.
    """
    # Each bottle has a quantity of what proportion of red, blue, and
    # green potion to add.
    # Expressed in integers from 1 to 100 that must sum up to 100.

    with db.engine.begin() as connection:
        
        result = connection.execute(sqlalchemy.text("""
            SELECT 
                SUM(red_ml) as red_ml,
                SUM(green_ml) as green_ml,
                SUM(blue_ml) as blue_ml,
                SUM(dark_ml) as dark_ml
                FROM barrel_ledger
            """)).first()        
        
        #potions = connection.execute(sqlalchemy.text("SELECT sku, quantity, potion_type FROM catalog ORDER BY id")).mappings()
        potions = connection.execute(sqlalchemy.text("""
                SELECT sku, name, red, green, blue, dark, quantity 
                FROM potion_ledger
                """)).mappings()
        total_potions = connection.execute(sqlalchemy.text("SELECT SUM(quantity) FROM potion_ledger")).scalar()
        
        capacity = connection.execute(sqlalchemy.text("SELECT SUM(amount) as capacity FROM capacity_ledger WHERE type = 'POTION'")).scalar()

    to_mix = []

    red_ml = result.red_ml
    green_ml = result.green_ml
    blue_ml = result.blue_ml
    dark_ml = result.dark_ml
    can_bottle = capacity - total_potions
    
    print(f"current total potions: {total_potions}")
    print(f"can bottle: {can_bottle}")

    print(f"red ml total: {red_ml}")
    print(f"green ml total: {green_ml}")
    print(f"blue ml total: {blue_ml}")


    for potion in potions:

        red_needed = potion.red
        green_needed = potion.green
        blue_needed = potion.blue
        dark_needed = potion.dark
    
        potion_type = [red_needed, green_needed, blue_needed, dark_needed]
        print(potion_type)

        to_bottle_pure_red = calculate_bottled_quantity(red_ml, red_needed)
        to_bottle_pure_green = calculate_bottled_quantity(green_ml, green_needed)
        to_bottle_pure_blue = calculate_bottled_quantity(blue_ml, blue_needed)
        to_bottle_pure_dark = calculate_bottled_quantity(dark_ml, dark_needed)

        print(to_bottle_pure_red)
        print(to_bottle_pure_green)
        print(to_bottle_pure_blue)

        if can_bottle > 0:
            if to_bottle_pure_red > 0 and red_needed == 100: #red
                print(f"added {potion_type}, quantity: {to_bottle_pure_red}")
                to_mix.append({
                    "potion_type": potion_type,
                    "quantity": to_bottle_pure_red
                })
                red_ml -= to_bottle_pure_red * 100
                print(f"{red_ml}ml of red remaining")
                can_bottle -= to_bottle_pure_red
                to_bottle_pure_red = red_ml // 50 
                print(to_bottle_pure_red)
                continue

            if to_bottle_pure_green > 0 and green_needed == 100: #green
                print(f"added {potion_type}, quantity: {to_bottle_pure_green}")
                to_mix.append({
                    "potion_type": potion_type,
                    "quantity": to_bottle_pure_green
                })
                green_ml -= to_bottle_pure_green * 100
                print(f"{green_ml}ml of red remaining")
                can_bottle -= to_bottle_pure_green
                to_bottle_pure_green = green_ml // 50
                print(to_bottle_pure_green)
                continue


            if to_bottle_pure_red > 0 and to_bottle_pure_green > 0 and blue_needed == 0:  #yellow
                to_bottle_yellow = min(to_bottle_pure_red, to_bottle_pure_green)
                print(f"added {potion_type}, quantity: {to_bottle_yellow}")
                to_mix.append({
                    "potion_type": potion_type,
                    "quantity": to_bottle_yellow
                    })
                red_ml -= to_bottle_yellow * 50
                green_ml -= to_bottle_yellow * 50
                can_bottle -= to_bottle_yellow
                continue
                            

            if to_bottle_pure_blue > 0 and blue_needed == 100: #blue
                print(f"added {potion_type}, quantity: {to_bottle_pure_blue}")
                to_mix.append({
                    "potion_type": potion_type,
                    "quantity": to_bottle_pure_blue
                })
                blue_ml -= to_bottle_pure_blue * 100
                print(f"{blue_ml}ml of blue ramaining")
                can_bottle -= to_bottle_pure_blue

                to_bottle_pure_blue = blue_ml // 50
                print(f"{to_bottle_pure_blue} blue potions")
                continue

            if to_bottle_pure_red > 0 and to_bottle_pure_blue > 0 and green_needed == 0: #purple
                to_bottle_purple = min(to_bottle_pure_blue, to_bottle_pure_blue)
                print(f"added {potion_type}, quantity: {to_bottle_purple}")
                to_mix.append({
                "potion_type": potion_type,
                "quantity": to_bottle_purple
                })
                red_ml -= to_bottle_purple * 50
                blue_ml -= to_bottle_purple * 50
                can_bottle -= to_bottle_purple
                continue

            if to_bottle_pure_red > 0 and to_bottle_pure_green == 25 and blue_needed == 0:
                to_bottle_orange = min(to_bottle_pure_green, to_bottle_pure_red)
                print(f"added {potion_type}, quantity: {to_bottle_orange}")
                to_mix.append({
                    "potion_type": potion_type,
                    "quantity": to_bottle_orange
                    })
                red_ml -= to_bottle_orange * 75
                green_ml -= to_bottle_orange * 25
                can_bottle -= to_bottle_orange
                continue
                

    print(f"bottle plan to mix: {to_mix}")
    return to_mix

if __name__ == "__main__":
    print(get_bottle_plan())
