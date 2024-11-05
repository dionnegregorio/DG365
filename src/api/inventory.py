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
        barrel_total = connection.execute(sqlalchemy.text("""
                                SELECT 
                                    SUM(red_ml + green_ml + blue_ml + dark_ml) as total
                                FROM barrel_ledger
                            """)).scalar()
        potions = connection.execute(sqlalchemy.text("SELECT SUM(quantity) FROM potion_ledger")).scalar()
        gold_total = connection.execute(sqlalchemy.text("SELECT SUM(total_gold) FROM transaction_ledger")).scalar()
    
    print(f"Total potions: {potions}, total ml: {barrel_total}, total gold: {gold_total}")
    return {"number_of_potions": potions, "ml_in_barrels": barrel_total, "gold": gold_total}

# Gets called once a day
@router.post("/plan")
def get_capacity_plan():
    """ 
    Start with 1 capacity for 50 potions and 1 capacity for 10000 ml of potion. Each additional 
    capacity unit costs 1000 gold.
    """
    print("Starting capacity plan")

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT SUM(quantity) FROM potion_ledger")).scalar()
        gold = connection.execute(sqlalchemy.text("SELECT SUM(total_gold) FROM transaction_ledger")).scalar()

    print(result)
    print(gold)


    if result >= 25 and result <= 100 and gold >= 1000:
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

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text(
            """
            INSERT INTO capacity_ledger
                (potion_capacity, ml_capacity)
            VALUES 
                (:potion, :ml)
            """
        ),{'potion': capacity_purchase.potion_capacity, 'ml': capacity_purchase.ml_capacity})

    print(capacity_purchase.potion_capacity)
    print(capacity_purchase.ml_capacity)
    
    return "OK"
