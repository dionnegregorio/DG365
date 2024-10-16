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
    
    return [{
        "success": True,
    }]

    #return "OK"

@router.post("/")
def create_cart(new_cart: Customer):
    """ class Customer(BaseModel):
    customer_name: str
    character_class: str
    level: int"""

    sql_to_execute = """
                    INSERT INTO carts 
                        (customer_name, customer_class, level) 
                    VALUES
                        (:customer_name, :character_class, :level)
                    RETURNING id
                    """
    values = {
        #'id_count': id_count,
        'customer_name': new_cart.customer_name,
        'character_class': new_cart.character_class,
        'level': new_cart.level,
    }
    
    with db.engine.begin() as connection:
        cart_id = connection.execute(sqlalchemy.text(sql_to_execute), values).scalar()
                         
    print(f"Created a new cart for {new_cart.customer_name}, class: {new_cart.character_class}, level: {new_cart.level}, cart_id: {cart_id}")
    return {"cart_id": cart_id}

class CartItem(BaseModel):
    quantity: int

@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    """  Set the quantity for a specific item in the cart.
    If the item exists, it updates the quantity; otherwise, it adds the item.
    """
    #inputs are cart_id, item_sku, cart_item 

    sql_to_execute = """
                    INSERT INTO cart_items
                        (cart_id, item_sku, quantity)
                    VALUES
                        (:cart_id, :item_sku, :quantity)
                    """

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT num_green_potions, num_red_potions, num_blue_potions FROM global_inventory"))
                                    
        potion_inventory = result.first()
        values = []

        if item_sku == "GREEN_POTION" and cart_item.quantity <= potion_inventory.num_green_potions:
            values.append({'cart_id': cart_id, 'item_sku': item_sku, 'quantity': cart_item.quantity})
        elif item_sku == "RED_POTION" and cart_item.quantity <= potion_inventory.num_red_potions:
            values.append({'cart_id': cart_id, 'item_sku': item_sku, 'quantity': cart_item.quantity})
        elif item_sku == "BLUE_POTION" and cart_item.quantity <= potion_inventory.num_blue_potions:
            values.append({'cart_id': cart_id, 'item_sku': item_sku, 'quantity': cart_item.quantity})

    #with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text(sql_to_execute), values)

    print(f"Added {cart_item.quantity} to cart")
    return {"success": True}
        
class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """ input is cart id which is an int 
        and cart checkout which is an object with str variable
    """
    #get cart id and its quantity, potion and 
    with db.engine.begin() as connection:
        cart_items = connection.execute(sqlalchemy.text("SELECT cart_id, item_sku, quantity FROM cart_items WHERE cart_id = :cart_id"), {'cart_id': cart_id}).mappings()

    total_price = 0
    green_potions = 0
    red_potions = 0
    blue_potions = 0

    #for each item in a customers cart add the quantity of each potion type and total price and all potion quantity
    for item in cart_items:
        if item["item_sku"] == "GREEN":
            green_potions += item["quantity"]
            total_price += 50 * item["quantity"]
        if item["item_sku"] == "RED":
            red_potions += item["quantity"]
            total_price += 50 * item["quantity"]
        if item["item_sku"] == "BLUE":
            blue_potions += item["quantity"]
            total_price += 50 * item["quantity"]
    
    total_quantity = green_potions + red_potions + blue_potions

    sql_to_ecexute_update = """
                            UPDATE global_inventory
                            SET num_green_potions = num_green_potions - :green_potions, 
                                num_red_potions = num_red_potions - :red_potions,
                                num_blue_potions = num_blue_potions - :blue_potions,
                                gold = gold + :total_price;
                            DELETE FROM carts WHERE id = :id;
                            DELETE FROM cart_items WHERE cart_id = :id
                            """
    
    values = {'green_potions': green_potions, 'red_potions': red_potions, 'blue_potions': blue_potions, 'total_price': total_price, 'id': cart_id, 'id': cart_id}
                                                                        
    with db.engine.begin() as connection:
            connection.execute(sqlalchemy.text(sql_to_ecexute_update), values)

    print(f"total_potions_bought: {total_quantity}, total_gold_paid: {total_price}")
    return {"total_potions_bought": total_quantity, "total_gold_paid": total_price}

