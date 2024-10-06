from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import math
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/inventory",
    tags=["inventory"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.get("/audit")
def get_inventory():
    """ """
    with db.engine.begin() as connection:
        #need to query more efficiently 
        gold_total = connection.execute(sqlalchemy.text("SELECT gold FROM global_inventory")).scalar()
        green_ml= connection.execute(sqlalchemy.text("SELECT num_green_ml FROM global_inventory")).scalar()
        red_ml = connection.execute(sqlalchemy.text("SELECT num_red_ml FROM global_inventory")).scalar()
        blue_ml = connection.execute(sqlalchemy.text("SELECT num_blue_ml FROM global_inventory")).scalar()
        green_potion = connection.execute(sqlalchemy.text("SELECT quantity FROM potion_catalog WHERE sku = 'GREEN'")).scalar()
        red_potion = connection.execute(sqlalchemy.text("SELECT quantity FROM potion_catalog WHERE sku = 'RED'")).scalar()
        blue_potion = connection.execute(sqlalchemy.text("SELECT quantity FROM potion_catalog WHERE sku = 'BLUE'")).scalar()

    ml_total = green_ml + red_ml + blue_ml
    potion_total = green_potion + red_potion + blue_potion 

    return {"number_of_potions": ml_total, "ml_in_barrels": potion_total, "gold": gold_total}

# Gets called once a day
@router.post("/plan")
def get_capacity_plan():
    """ 
    Start with 1 capacity for 50 potions and 1 capacity for 10000 ml of potion. Each additional 
    capacity unit costs 1000 gold.
    """

    return {
        "potion_capacity": 50,
        "ml_capacity": 10000
        }

class CapacityPurchase(BaseModel):
    potion_capacity: int
    ml_capacity: int

# Gets called once a day
@router.post("/deliver/{order_id}")
def deliver_capacity_plan(capacity_purchase : CapacityPurchase, order_id: int):
    """ 
    Start with 1 capacity for 50 potions and 1 capacity for 10000 ml of potion. Each additional 
    capacity unit costs 1000 gold.
    """

    return "OK"
