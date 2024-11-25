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
    deliv_orange = 0
    deliv_dark = 0
    
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
            case [75,25,0,0]: 
                deliv_orange += potion.quantity
                ml_red -= red
                ml_green -= green
            case [0,0,0,100]:
                deliv_dark += potion.quantity
                ml_dark -= dark



    sql_to_execute = """
                    UPDATE potion_ledger
                    SET quantity = CASE sku
                        WHEN 'RED' THEN quantity + :deliv_red
                        WHEN 'GREEN' THEN quantity + :deliv_green
                        WHEN 'BLUE' THEN quantity + :deliv_blue
                        WHEN 'PURPLE' THEN quantity + :deliv_purp
                        WHEN 'ORANGE' THEN quantity + :deliv_orange
                        ELSE quantity
                    END
                    WHERE sku IN ('RED', 'GREEN', 'BLUE', 'PURPLE', 'ORANGE');

                    INSERT INTO barrel_ledger
                        (red_ml, green_ml, blue_ml, dark_ml)
                    VALUES
                        (:ml_red, :ml_green, :ml_blue, :ml_dark)
                    """
    

    values = {'deliv_red': deliv_red, 'deliv_green': deliv_green, 'deliv_blue': deliv_blue,
                'deliv_purp': deliv_purp, 'deliv_orange': deliv_orange,
                'ml_red': ml_red , 'ml_green': ml_green, 'ml_blue': ml_blue, 'ml_dark': ml_dark
              }
    
    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text(sql_to_execute), values)

    print(f"delivered: {deliv_red} red, {deliv_green} green, {deliv_blue} blue, {deliv_purp} purple, {deliv_orange} orange")

    return "successfully delivered"


def calculate_bottled_quantity(color_ml, color_needed, max_bottle = 10):
    if color_needed > 0:
        bottled_quantity = color_ml // color_needed
        return min(bottled_quantity, max_bottle)
    return 0


@router.post("/plan")
def get_bottle_plan():
    """
    Evenly distributes potion bottling among all available recipes,
    proportionally using resources and respecting bottling capacity.
    Stops if the total number of potions exceeds 50.
    """
    with db.engine.begin() as connection:
        barrels = connection.execute(sqlalchemy.text("""
            SELECT 
                SUM(red_ml) as red_ml,
                SUM(green_ml) as green_ml,
                SUM(blue_ml) as blue_ml,
                SUM(dark_ml) as dark_ml
            FROM barrel_ledger
        """)).first()
        
        potions = connection.execute(sqlalchemy.text("""
            SELECT sku, name, red, green, blue, dark, quantity 
            FROM potion_ledger
            ORDER BY sku
        """)).mappings()
        
        total_potions = connection.execute(sqlalchemy.text("SELECT SUM(quantity) FROM potion_ledger")).scalar()
        capacity = connection.execute(sqlalchemy.text("""
            SELECT SUM(amount) as capacity 
            FROM capacity_ledger 
            WHERE type = 'POTION'
        """)).scalar()

    to_mix = []
    red_ml = barrels.red_ml or 0
    green_ml = barrels.green_ml or 0
    blue_ml = barrels.blue_ml or 0
    dark_ml = barrels.dark_ml or 0
    can_bottle = capacity - total_potions

    print(f"Current total potions: {total_potions}")
    print(f"Bottling capacity available: {can_bottle}")
    print(f"Ingredient inventory - Red: {red_ml}ml, Green: {green_ml}ml, Blue: {blue_ml}ml, Dark: {dark_ml}ml")

    potion_plans = []
    for potion in potions:
        red_needed = potion.red
        green_needed = potion.green
        blue_needed = potion.blue
        dark_needed = potion.dark

        current_potion = [red_needed, green_needed, blue_needed, dark_needed]
        print(current_potion)

        total_needed = red_needed + green_needed + blue_needed + dark_needed
        if total_needed != 100:
            print(f"Skipping potion {potion.name} ({potion.sku}) - proportions do not sum to 100")
            continue

        # Calculate max possible bottles for this potion
        max_bottles = min(
            red_ml // red_needed if red_needed > 0 else float('inf'),
            green_ml // green_needed if green_needed > 0 else float('inf'),
            blue_ml // blue_needed if blue_needed > 0 else float('inf'),
            dark_ml // dark_needed if dark_needed > 0 else float('inf'),
            can_bottle
        )
        if max_bottles > 0:
            potion_plans.append({
                "potion": potion,
                "max_bottles": max_bottles
            })

    total_created_potions = 0

    # Distribute bottling evenly across all potion types
    while can_bottle > 0 and len(potion_plans) > 0:
        total_max_bottles = sum(plan['max_bottles'] for plan in potion_plans)
        if total_max_bottles == 0:
            break

        for plan in potion_plans[:]:
            potion = plan["potion"]
            red_needed = potion.red
            green_needed = potion.green
            blue_needed = potion.blue
            dark_needed = potion.dark

            # Proportionally allocate resources
            proportion = plan["max_bottles"] / total_max_bottles
            bottles_to_add = max(1, int(proportion * can_bottle))  # Ensure at least one bottle is made

            bottles_to_add = min(
                bottles_to_add,
                plan["max_bottles"]
            )

            if bottles_to_add > 0:
                print(f"Adding {bottles_to_add} bottles of {potion.name} ({potion.sku})")
                to_mix.append({
                    "potion_type": [red_needed, green_needed, blue_needed, dark_needed],
                    "quantity": bottles_to_add
                })

                red_ml -= bottles_to_add * red_needed
                green_ml -= bottles_to_add * green_needed
                blue_ml -= bottles_to_add * blue_needed
                dark_ml -= bottles_to_add * dark_needed
                can_bottle -= bottles_to_add
                total_created_potions += bottles_to_add

                plan["max_bottles"] -= bottles_to_add

            # Stop if the total number of potions exceeds 50
            if total_created_potions >= 50:
                print(f"Reached the maximum limit of 50 potions. Stopping.")
                can_bottle = 0
                break

            # Remove potion plan if no more bottles can be made
            if plan["max_bottles"] <= 0 or can_bottle <= 0:
                potion_plans.remove(plan)

    print(f"Bottling plan: {to_mix}")
    print(f"Remaining inventory - Red: {red_ml}ml, Green: {green_ml}ml, Blue: {blue_ml}ml, Dark: {dark_ml}ml")
    return to_mix


if __name__ == "__main__":
    print(get_bottle_plan())


"""
check how many potions i can make

for each potion in the db 
    get how many rgbd ingredients is needed
    calculate how many of those are available
    if available >= needed
    add to the mix

"""