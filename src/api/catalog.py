from fastapi import APIRouter
import sqlalchemy
from src import database as db


router = APIRouter()

@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    """
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory"))
    

    inventory = result.first()
    potions_for_sale = []

    green = inventory.num_green_potions
    red = inventory.num_red_potions
    blue = inventory.num_blue_potions

    if green > 0:
        potions_for_sale.append({
                "sku": "GREEN_POTION",
                "name": "Green Potion",
                "quantity": green,
                "price": 50,
                "potion_type": [0,100,0,0],
            })
    if red > 0:
        potions_for_sale.append({
                "sku": "RED_POTION",
                "name": "Red Potion",
                "quantity": red,
                "price": 50,
                "potion_type": [100,0,0,0],
            })
    if blue > 0:
        potions_for_sale.append({
                "sku": "BLUE_POTION",
                "name": "Blue Potion",
                "quantity": blue,
                "price": 50,
                "potion_type": [0,0,100,0],
            })
        
    for entry in potions_for_sale:
        print(f"potions for sale: {entry}")
    return potions_for_sale

    #get number of potions in database

    #if each potion is less than or equal to 0 return []
    #if not return "sku": "GREEN_POTION_0",
    
