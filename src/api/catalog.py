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
        potions = connection.execute(sqlalchemy.text(
            "SELECT sku FROM potion_catalog"))

    #potions_for_sale = ["Green Potion", "Red Potion", "Blue Potion"] 

    for potion_amount in potions:
        if potion_amount <= 0:
            return []
        else: 
            return [
            {
                "sku": potions_for_sale[potion_amount.index],
                "name": "green potion",
                "quantity": green.quantity,
                "price": green.price,
                "potion_type": [0, 100, 0, 0],
            }
        ]

        

    #get number of potions in database

    #if each potion is less than or equal to 0 return []
    #if not return "sku": "GREEN_POTION_0",
    
