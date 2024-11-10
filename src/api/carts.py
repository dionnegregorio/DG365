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

    sql = """
            SELECT potion_ledger.name as potion, cart_items.quantity * potion_ledger.price as gold, 
                carts.customer_name, carts.created_at as time
            FROM cart_items
            JOIN potion_ledger ON cart_items.item_sku = potion_ledger.sku
            JOIN carts ON carts.id = cart_items.cart_id 
            """
    
    #search by name and/or potion
    if customer_name != "" and potion_sku != "":
        sql += f" WHERE carts.customer_name ILIKE %{customer_name} AND WHERE potion_ledger.sku ILIKE %{potion_sku}%"
    elif customer_name != "":
        sql += f" WHERE carts.customer_name ILIKE %{customer_name}% "
    elif potion_sku != "":
        sql += f" WHERE potion_ledger.sku ILIKE %{potion_sku}% "

    print(customer_name, potion_sku)

    if sort_col is search_sort_options.customer_name:
        sort = "customer_name"
    elif sort_col is search_sort_options.item_sku:
        sort = "item_sku"
    elif sort_col is search_sort_options.line_item_total:
        sort = "gold"
    elif sort_col is search_sort_options.timestamp:
        sort = "time"

    print(sort)

    if sort_order.value == "asc":
        order = "asc"
    else:
        order = "desc"


    print(order)
    print(sql)

    sql += f" ORDER BY {sort} {order} "
    sql += f" LIMIT 5 {('OFFSET ' + search_page) if search_page != '' else ''}"

    print(sql)

    with db.engine.begin() as connection:
        results = connection.execute(sqlalchemy.text(sql))
        items = []
        for i, row in enumerate(results):
            items.append({
                "line_item_id": i,
                "item_sku": row.potion,
                "customer_name": row.customer_name,
                "line_item_total": row.gold,
                "line_item_total": row.time,
            })

    search_page = int(search_page) if search_page else 0
    previous = str(int(search_page) - 5) if search_page != '' and int(search_page) >= 5 else 0
    next = str(search_page + 5) if search_page != '' else 5
        
    print(items)

    return {
        "previous": previous,
        "next": next,
        "results": items
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
                    UPDATE potion_ledger
                    SET quantity = quantity - :quantity_catalog
                    WHERE sku = :sku;

                    INSERT INTO cart_items
                        (cart_id, item_sku, quantity)
                    VALUES
                        (:cart_id, :item_sku, :quantity)
                    """

    values = {'quantity_catalog': cart_item.quantity, 'sku': item_sku,'cart_id': cart_id, 'item_sku': item_sku, 'quantity': cart_item.quantity}


    with db.engine.begin() as connection:
    
    #with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text(sql_to_execute), values)

    print(f"Added {cart_item.quantity} {item_sku} to cart_id {cart_id}")
    return {"success": True}
        
class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """ input is cart id which is an int 
        and cart checkout which is an object with str variable
    """
    #get cart id and its quantity, potion and 

    sql_to_execute = """
                    UPDATE cart_items
                    SET paid = TRUE
                    WHERE cart_items.cart_id = :cart_id;

                    SELECT item_sku, cart_items.quantity
                    FROM cart_items
                    WHERE cart_items.cart_id = :cart_id;
                    """
    values = {'cart_id': cart_id}
    
    with db.engine.begin() as connection:
        item = connection.execute(sqlalchemy.text(sql_to_execute), values).mappings().fetchone()
        price = connection.execute(sqlalchemy.text("SELECT price FROM potion_ledger WHERE sku = :sku"), {'sku': item['item_sku']}).scalar()
    
    sku = item['item_sku']
    quant = item['quantity']

    print(sku)
    print(price)

    cost = price * quant
    print(f"total cost: {cost}")
    print(f"total quantity: {quant}")

    sql2 = """
            INSERT INTO transaction_ledger
                (tran_type, amount, total_gold)
            VALUES
                (:tran_type, :amount, :total_gold)
            """

    sell = "SELL"

    val = {'tran_type': sell, 'amount': quant, 'total_gold': cost}

    with db.engine.begin() as connection:
        item = connection.execute(sqlalchemy.text(sql2), val)

    print(f"total_potions_bought: {quant} {sku} potions, total_gold_paid: {cost}")
    return {
        "total_potions_bought": quant, 
        "total_gold_paid": cost
    }


"""
    price = connection.execute(sqlalchemy.text("SELECT price FROM catalog")).mappings()

    total_price = 0
    green_potions = 0
    red_potions = 0
    blue_potions = 0

    #for each item in a customers cart add the quantity of each potion type and total price and all potion quantity
    for item in cart_items:
        if item["item_sku"] == "GREEN_POTION":
            green_potions += item["quantity"]
            total_price += 40 * item["quantity"]
        elif item["item_sku"] == "RED_POTION":
            red_potions += item["quantity"]
            total_price += 40 * item["quantity"]
        elif item["item_sku"] == "BLUE_POTION":
            blue_potions += item["quantity"]
            total_price += 40 * item["quantity"]
    
    total_quantity = green_potions + red_potions + blue_potions

    sql_to_ecexute_update = 
    
    values = {'green_potions': green_potions, 'red_potions': red_potions, 'blue_potions': blue_potions, 'total_price': total_price, 'id': cart_id, }
                                                                        
    with db.engine.begin() as connection:
            connection.execute(sqlalchemy.text(sql_to_ecexute_update), values)
"""
"""
UPDATE global_inventory
                            SET num_green_potions = num_green_potions - :green_potions, 
                                num_red_potions = num_red_potions - :red_potions,
                                num_blue_potions = num_blue_potions - :blue_potions,
                                gold = gold + :total_price;
                            INSERT INTO sell_history 
                                (customer_id, potion_type, name, quantity, amount_payed)
                            VALUES (:customer_id, :potion_type, :name, :quantity, :amount_payed)

                            DELETE FROM carts WHERE id = :id;
                            DELETE FROM cart_items WHERE cart_id = :id"""