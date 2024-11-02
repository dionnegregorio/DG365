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
        result = connection.execute(sqlalchemy.text("SELECT * FROM potion_ledger")).mappings()
    

    potions_for_sale = []

    for potion in result:
        if potion.quantity > 0:
            potions_for_sale.append({
                "sku": potion.sku,
                "name": potion.name,
                "quantity": potion.quantity,
                "price": potion.price,
                "potion_type": [potion.red, potion.green, potion.blue, potion.dark]
            })

    for entry in potions_for_sale:
        print(f"potions for sale: {entry}")

    return potions_for_sale

    #get number of potions in database

    #if each potion is less than or equal to 0 return []
    #if not return "sku": "GREEN_POTION_0",
    
