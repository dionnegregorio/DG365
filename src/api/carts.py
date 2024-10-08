from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
from enum import Enum
import sqlalchemy
from src import database as db
from src.api.catalog import CatalogItem


router = APIRouter(
    prefix="/carts",
    tags=["cart"],
    dependencies=[Depends(auth.get_api_key)],
)


id_count = 0

class search_sort_options(str, Enum):
    customer_name = "customer_name"
    item_sku = "item_sku"
    line_item_total = "line_item_total"
    timestamp = "timestamp"

class search_sort_order(str, Enum):
    asc = "asc"
    desc = "desc"   

@router.get("/search/", tags=["search"])
def search_orders(
    customer_name: str = "",
    potion_sku: str = "",
    search_page: str = "",
    sort_col: search_sort_options = search_sort_options.timestamp,
    sort_order: search_sort_order = search_sort_order.desc,
):
    """
    Search for cart line items by customer name and/or potion sku.

    Customer name and potion sku filter to orders that contain the 
    string (case insensitive). If the filters aren't provided, no
    filtering occurs on the respective search term.

    Search page is a cursor for pagination. The response to this
    search endpoint will return previous or next if there is a
    previous or next page of results available. The token passed
    in that search response can be passed in the next search request
    as search page to get that page of results.

    Sort col is which column to sort by and sort order is the direction
    of the search. They default to searching by timestamp of the order
    in descending order.

    The response itself contains a previous and next page token (if
    such pages exist) and the results as an array of line items. Each
    line item contains the line item id (must be unique), item sku, 
    customer name, line item total (in gold), and timestamp of the order.
    Your results must be paginated, the max results you can return at any
    time is 5 total line items.
    """

    return {
        "previous": "",
        "next": "",
        "results": [
            {
                "line_item_id": 1,
                "item_sku": "1 oblivion potion",
                "customer_name": "Scaramouche",
                "line_item_total": 50,
                "timestamp": "2021-01-01T00:00:00Z",
            }
        ],
    }

class Customer(BaseModel):
    customer_name: str
    character_class: str
    level: int

class cart_class:
    customer_name = Customer
    item_sku: str
    

@router.post("/visits/{visit_id}")
def post_visits(visit_id: int, customers: list[Customer]):
    """
    Which customers visited the shop today?
    """
    print(customers)

    visited = False
    for customer in customers:
        visited = True
    
    return [{
        "success": visited,
    }]

    #return "OK"

@router.post("/")
def create_cart(new_cart: Customer):
    """ class Customer(BaseModel):
    customer_name: str
    character_class: str
    level: int"""

    global id_count
    id_count += 1
    
    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text(f"""
                                    INSERT INTO carts 
                                        (id, customer_name, customer_class, level) 
                                    VALUES ('{id_count}', '{new_cart.customer_name}', '{new_cart.character_class}', '{new_cart.level}')
                                    """ ))
    return {"cart_id": id_count}


class CartItem(BaseModel):
    quantity: int



carts = {}

@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    """  Set the quantity for a specific item in the cart.
    If the item exists, it updates the quantity; otherwise, it adds the item.
    """

    green_count = 0
    red_count = 0
    blue_count = 0

    with db.engine.begin() as connection:

        match item_sku:
            case "GREEN_POTION":
                green_count += cart_item.quantity
                inventory_quant = connection.execute(sqlalchemy.text(f"SELECT num_green_potions FROM global_inventory")).scalar()
                if inventory_quant > green_count:
                    #update global_inventory
                    connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_green_potions = '{inventory_quant - green_count}'"))
                    #insert a new cart
                    connection.execute(sqlalchemy.text(f"INSERT INTO carts (cart_id, item_sku, quantity ) VALUES ('{cart_id}', '{item_sku}', '{green_count}'"))
                    return "OK"
                else: 
                    return "Not enough potions"
            case "RED_POTION":
                red_count += cart_item.quantity
                inventory_quant = connection.execute(sqlalchemy.text(f"SELECT num_red_potions FROM global_inventory")).scalar()
                if inventory_quant > green_count:
                    #update global_inventory
                    connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_red_potions = '{inventory_quant - red_count}'"))
                    #insert a new cart
                    connection.execute(sqlalchemy.text(f"INSERT INTO carts (cart_id, item_sku, quantity ) VALUES ('{cart_id}', '{item_sku}', '{red_count}'"))
                    return "OK"
                else: 
                    return "Not enough potions"
            case "BLUE_POTION":
                blue_count += cart_item.quantity
                inventory_quant = connection.execute(sqlalchemy.text(f"SELECT num_blue_potions FROM global_inventory")).scalar()
                if inventory_quant > green_count:
                    #update global_inventory
                    connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_blue_potions = '{inventory_quant - blue_count}'"))
                    #insert a new cart
                    connection.execute(sqlalchemy.text(f"INSERT INTO carts (cart_id, item_sku, quantity ) VALUES ('{cart_id}', '{item_sku}', '{blue_count}'"))
                    return "OK"
                else: 
                    return "Not enough potions"


class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """ """
    total_green = 0
    total_red = 0
    total_blue = 0

    green_price = 50
    red_price = 55
    blue_price = 60
    
    if cart_id not in carts:
        return {"error": "Cart not found"}
    
    cart = carts[cart_id]

    return {"total_potions_bought": 1, "total_gold_paid": 50}
