    create table
  public.barrel_ledger (
    id bigint generated by default as identity not null,
    created_at timestamp with time zone not null default now(),
    red_ml integer not null default 0,
    green_ml integer not null default 0,
    blue_ml integer not null default 0,
    dark_ml integer not null default 0,
    order_id integer not null default 1,
    constraint gold_ledger_pkey primary key (id)
  ) tablespace pg_default;

  create table
  public.capacity_ledger (
    id bigint generated by default as identity not null,
    created_at timestamp with time zone not null default now(),
    type text null,
    amount integer null,
    constraint capacity_pkey primary key (id)
  ) tablespace pg_default;

  create table
  public.cart_items (
    created_at timestamp with time zone not null default now(),
    item_sku text null,
    quantity integer null,
    id integer generated by default as identity not null,
    cart_id integer not null,
    paid boolean null default false,
    constraint cart_items_pkey primary key (id),
    constraint cart_items_cart_id_fkey foreign key (cart_id) references carts (id)
  ) tablespace pg_default;

  create table
  public.carts (
    id integer generated by default as identity not null,
    customer_name text null,
    customer_class text null,
    level integer null,
    created_at timestamp with time zone null default now(),
    constraint carts_pkey primary key (id)
  ) tablespace pg_default;

  create table
  public.potion_ledger (
    created_at timestamp with time zone not null default now(),
    sku text not null,
    quantity integer null,
    price integer null,
    name text not null,
    red integer not null,
    green integer not null,
    blue integer not null,
    dark integer not null,
    constraint potion_ledger_pkey primary key (sku)
  ) tablespace pg_default;

  create table
  public.transaction_ledger (
    id bigint generated by default as identity not null,
    created_at timestamp with time zone not null default now(),
    tran_type text null,
    amount integer null,
    total_gold integer null,
    constraint transaction_id_pkey primary key (id)
  ) tablespace pg_default;