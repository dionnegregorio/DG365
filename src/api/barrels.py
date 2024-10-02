from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

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

    barrels_amount = 0

    #save first index of the barrel list for now
    barrels_amount = barrels_delivered[0].ml_per_barrel * barrels_delivered[0].quantity
    gold_spent = barrels_delivered[0].price * barrels_delivered[0].quantity
  

    with db.engine.begin() as connection:
        for barrel in barrels_delivered:
            connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_green_ml = num_green_ml + {barrels_amount}"))
            connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET gold = gold - {gold_spent}"))

    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):

    """purchase a new small green potion barrel only if the potions 
    in inventory is less than 10.Always mix all available green ml 
     if any exists. Offer up for sale in the catalog only the amount 
     of green potions that actually exist currently in inventory."""
    

    with db.engine.begin() as connection:
        green_potion = connection.execute(sqlalchemy.text("SELECT num_green_potions FROM global_inventory")).scalar
    
        gold_total = connection.execute(sqlalchemy.text("SELECT gold FROM global_inventory")).scalar()

    plan = []
    for barrel in wholesale_catalog:

        if barrel.sku == "SMALL_GREEN_BARREL" and green_potion < 10:
            can_buy = gold_total // barrel.price
            if can_buy <= 0:
                continue
            if can_buy > barrel.quantity:
                can_buy = barrel.quantity
            plan.append({"sku": barrel.sku, "quantity": can_buy})
    return plan
                 

    #print(wholesale_catalog)
    
    

