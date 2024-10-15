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
                    """
    values = {
        #'id_count': id_count,
        'customer_name': new_cart.customer_name,
        'character_class': new_cart.character_class,
        'level': new_cart.level,
    }
    
    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text(sql_to_execute), values)
        cart_id = connection.execute(sqlalchemy.text(f"SELECT id FROM carts WHERE customer_name = {new_cart.customer_name}"))
                       
                       
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

    print(f"Added {cart_item.quantity} to cart")
    return {"success": added}
        
class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """ input is cart id which is an int 
        and cart checkout which is an object with str variable
    """
    
    #get cart id and its quantity, potion and 
    with db.engine.begin() as connection:
        cart = connection.execute(sqlalchemy.text("SELECT * FROM carts WHERE cart_id = :cart_id"), {'cart_id': cart_id})

    cart = cart.first()
    total_quantity = cart.quantity
    total_price = 0

    potion_type = ""

    match cart.item_sku: 
        case "GREEN":
            total_price = total_quantity * 50
            potion_type = "num_green_potions"
        case "RED":
            total_price = total_quantity * 55
            potion_type = "num_red_potions"
        case "BLUE": 
            total_price = total_quantity * 60
            potion_type = "num_blue_potions"

    #update gold and inventory
 
    sql_to_ecexute_update = f"""
                            UPDATE global_inventory
                            SET {potion_type} = {potion_type} - carts.quantity, gold = gold + :total_price
                            FROM carts
                            WHERE carts.cart_id = cart_id;

                            UPDATE carts 
                            SET payed = 'TRUE'
                            WHERE cart_id = :cart_id;
                            """

    with db.engine.begin() as connection:
            connection.execute(sqlalchemy.text(sql_to_ecexute_update), {'total_price': total_price, 'cart_id': cart_id})
        
    """UPDATE catalog
SET inventory = catalog.inventory - cart_items.quantity
FROM cart_items
WHERE catalog.id = cart_items.catalog_id and cart_items.cart_id = :cart_id;"""

    
    print(f"total_potions_bought: {total_quantity}, total_gold_paid: {total_price}")
    return {"total_potions_bought": total_quantity, "total_gold_paid": total_price}
