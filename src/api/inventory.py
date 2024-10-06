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
                gold_total = connection.execute(sqlalchemy.text("SELECT gold FROM global_inventory")).scalar()
                ml = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory")).scalar()
                #change query
                potions = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory")).scalar()

                ml_total = 0
                potion_total = 0

                for amount in ml:
                      ml_total += amount
                for amount in potions:
                      potion_total += amount

    
    return {"number_of_potions": potion_total, "ml_in_barrels": ml_total, "gold": gold_total}

# Gets called once a day
@router.post("/plan")
def get_capacity_plan():
    """ 
    Start with 1 capacity for 50 potions and 1 capacity for 10000 ml of potion. Each additional 
    capacity unit costs 1000 gold.
    """

    return {
        "potion_capacity": 0,
        "ml_capacity": 0
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
