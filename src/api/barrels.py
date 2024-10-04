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

    gold_spent = 0

    #set current quantity of each ml and gold
    with db.engine.begin() as connection:
        green_ml = connection.execute(sqlalchemy.text("SELECT num_green_ml, FROM global_inventory")).scalar()
        gold_amount = connection.execute(sqlalchemy.text("SELECT gold FROM gold_bank")).scalar()

        
        for barrel in barrels_delivered:
            if barrel.sku == "SMALL_GREEN_BARREL":
                green_ml += barrel.ml_per_barrel * barrel.quantity
                gold_amount -= barrel.price * barrel.quantity

        connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_green_ml =: green_ml"),
            {'num_green_ml' : green_ml})
        connection.execute(sqlalchemy.text("UPDATE gold_bank SET gold =: gold_amount"), {'gold_amount': gold_amount})

    return "OK"


# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):

    """purchase a new small green potion barrel only if the potions 
    in inventory is less than 10. Always mix all available green ml 
     if any exists. Offer up for sale in the catalog only the amount 
     of green potions that actually exist currently in inventory."""
    
    print(wholesale_catalog)
    with db.engine.begin() as connection:
        current_green_potions = connection.execute(sqlalchemy.text("SELECT num_green_potions FROM global_inventory")).scalar()
        gold_total = connection.execute(sqlalchemy.text("SELECT num_green_potions FROM global_inventory")).scalar()

    if current_green_potions < 10:
            return [
                {
                "sku": "SMALL_GREEN_BARREL",
                "quantity": 5,
                }
            ]
    
    print(wholesale_catalog)

    return []

    """with db.engine.begin() as connection:
        num_green_potion = connection.execute(sqlalchemy.text("SELECT num_green_potions FROM global_inventory")).scalar()
        gold = connection.execute(sqlalchemy.text("SELECT gold FROM global_inventory"))  
        num_green_potion = num_green_potion.first()
        gold = gold.first()

    inventory = {  
        "Green_ml" : num_green_potion
        #"Red_ml" : num_red_potion
       #"Blue_ml" : num_blue_potion
    }

    barrel_plan = []

    for barrel in wholesale_catalog:
        if barrel.sku.upper() != "SMALL_GREEN_BARREL": #and num_green_potion < 10:
            return [
                {"sku": "SMALL_GREEN_BARREL", "quantity": 5}
                ]
        else: 
            return [
                {"sku": "SMALL_GREEN_BARREL", "quantity": 5}
                ]
            
            amount_can_buy = gold // barrel.price
            if amount_can_buy <= 0:
                continue
            if amount_can_buy >= barrel.quantity:
                amount_can_buy = barrel.quantity
                barrel_plan.append({"sku": barrel.sku, "quantity": amount_can_buy})
            else: 
                barrel_plan.append({"sku": barrel.sku, "quantity": amount_can_buy})
    #return barrel_plan
    """
        