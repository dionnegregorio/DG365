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
        result = connection.execute(sqlalchemy.text("""
                                SELECT 
                                    num_green_ml + num_red_ml + num_blue_ml AS ml_total,
                                    gold
                                FROM global_inventory                 
                            """))
        potions = connection.execute(sqlalchemy.text("SELECT SUM(quantity) FROM catalog")).scalar()
    

    inventory = result.first()

    print(f"Total potions: {potions}, total ml: {inventory.ml_total}, total gold: {inventory.gold}")
    return {"number_of_potions": potions, "ml_in_barrels": inventory.ml_total, "gold": inventory.gold}

# Gets called once a day
@router.post("/plan")
def get_capacity_plan():
    """ 
    Start with 1 capacity for 50 potions and 1 capacity for 10000 ml of potion. Each additional 
    capacity unit costs 1000 gold.
    """

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT SUM(quantity) FROM catalog")).scalar()
        gold = connection.execute(sqlalchemy.text("SELECT gold FROM global_inventory")).scalar()

    if result == 50 and gold >= 2000:
        return {
            "potion_capacity": 1,
            "ml_capacity": 1
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
