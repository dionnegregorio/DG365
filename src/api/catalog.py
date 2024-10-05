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
        red = connection.execute(sqlalchemy.text("SELECT * FROM potion_catalog WHERE sku = 'RED_POTION'"))  
        green = connection.execute(sqlalchemy.text("SELECT * FROM potion_catalog WHERE sku = 'GREEN_POTION'")) 
        blue = connection.execute(sqlalchemy.text("SELECT * FROM potion_catalog WHERE sku = 'BLUE_POTION'"))      

        if green.quantity <= 0:
            return []
        else: 
            return [
            {
                "sku": "GREEN_POTION_0",
                "name": "green potion",
                "quantity": green.quantity,
                "price": green.price,
                "potion_type": [0, 100, 0, 0],
            }
        ]

    #get number of potions in database

    #if each potion is less than or equal to 0 return []
    #if not return "sku": "GREEN_POTION_0",
    
