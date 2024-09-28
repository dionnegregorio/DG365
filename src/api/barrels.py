from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text(sql_to_execute))

router = APIRouter(
    prefix="/barrels",
    tags=["barrels"],
    dependencies=[Depends(auth.get_api_key)],
)

class Barrel(BaseModel):
    sku: str

    ml_per_barrel: int
    potion_type: list[int]
    price: int

    quantity: int

@router.post("/deliver/{order_id}")
def post_deliver_barrels(barrels_delivered: list[Barrel], order_id: int):
    """ """
    print(f"barrels delievered: {barrels_delivered} order_id: {order_id}")

    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):

    #purchase a new small green potion barrel only if the potions 
    #in inventory is less than 10.Always mix all available green ml 
    # if any exists. Offer up for sale in the catalog only the amount 
    # of green potions that actually exist currently in inventory.

    greenpotion = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory WHERE num_green_potion"))
    
    if greenpotion < 10:
         return [
        {
            "sku": "SMALL_GREEN_BARREL",
            "quantity": 1,
        }
    #print(wholesale_catalog)
    
    ]

