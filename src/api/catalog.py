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
        result = connection.execute(sqlalchemy.text("SELECT * FROM catalog")).mappings()
    

    potions_for_sale = []

    for row in result:
        if row["quantity"] > 0:
            potions_for_sale.append({
                "sku": row["sku"],
                "name": row["name"],
                "quantity": row["quantity"],
                "price": row["price"],
                "potion_type": row["potion_type"],
            })

    for entry in potions_for_sale:
        print(f"potions for sale: {entry}")

    return potions_for_sale

    #get number of potions in database

    #if each potion is less than or equal to 0 return []
    #if not return "sku": "GREEN_POTION_0",
    
