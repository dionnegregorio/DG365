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
        potions = connection.execute(sqlalchemy.text("SELECT sku, name, quantity, price, type FROM potion_catalog"))

    potions_for_sale = []

    for potion in potions:
        if potion.quantity > 0: 
            potions_for_sale.append({
                "sku": potion.sku,
                "name": potion.name,
                "quantity": potion.quantity,
                "price": potion.price,
                "potion_type": potion.type,
            })
    return potions_for_sale

    #get number of potions in database

    #if each potion is less than or equal to 0 return []
    #if not return "sku": "GREEN_POTION_0",
    
