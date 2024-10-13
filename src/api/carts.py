from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
from enum import Enum
import sqlalchemy
from src import database as db


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

    sql_to_execute = """
                    INSERT INTO carts 
                        (cart_id, customer_name, customer_class, level) 
                     VALUES
                        (:id_count, :customer_name, :character_class, :level)
                    """
    values = {
        'id_count': id_count,
        'customer_name': new_cart.customer_name,
        'character_class': new_cart.character_class,
        'level': new_cart.level,
    }
    
    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text(sql_to_execute), values)
                       
    return {"cart_id": id_count}


class CartItem(BaseModel):
    quantity: int

@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    """  Set the quantity for a specific item in the cart.
    If the item exists, it updates the quantity; otherwise, it adds the item.
    """
    #inputs are cart_id, item_sku, cart_item 

#class CartItem(BaseModel):
    #quantity: int

    added = False

    sql_to_execute = """
                    UPDATE carts 
                    SET item_sku = :item_sku, quantity = :quantity
                    WHERE cart_id = :cart_id
                    """

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT num_green_potions, num_red_potions, num_blue_potions FROM global_inventory"))
                                    
    potion_inventory = result.first()
    values = []

    if item_sku == "GREEN" and cart_item.quantity <= potion_inventory.num_green_potions:
        values.append({'item_sku': item_sku, 'quantity': cart_item.quantity, 'cart_id': cart_id})
        added = True
    elif item_sku == "RED" and cart_item.quantity <= potion_inventory.num_red_potions:
        values.append({'item_sku': item_sku, 'quantity': cart_item.quantity, 'cart_id': cart_id})
        added = True
    elif item_sku == "BLUE" and cart_item.quantity <= potion_inventory.num_blue_potions:
        values.append({'item_sku': item_sku, 'quantity': cart_item.quantity, 'cart_id': cart_id})
        added = True

    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text(sql_to_execute), values)


    print(f"Added {cart_item.quantity} to cart")
    return {"success": added}
        
class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """ input is cart id which is an int 
        and cart chackout which is an object with str vatiable
    """
    #get cart id and its quantity, potion and 
    with db.engine.begin() as connection:
        cart = connection.execute(sqlalchemy.text(f"SELECT * FROM carts WHERE cart_id = {cart_id}")).fetchall()

    total_price = 0
    total_quantity = 0

    for cart_column in cart:
        item_sku = cart_column.item_sku 
        quantity = cart_column.quantity
        total_price = connection.execute(sqlalchemy.text(f"SELECT price FROM potion_catalog WHERE sku = '{item_sku}'")).scalar() * quantity
        total_quantity += quantity

    #update gold, adding total price
    connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET gold = gold + {total_price}"))
    

    return {"total_potions_bought": total_quantity, "total_gold_paid": total_price}
