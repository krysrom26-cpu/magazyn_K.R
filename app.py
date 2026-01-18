import streamlit as st
import pandas as pd
from supabase import create_client

# ---------------- CONFIG ----------------
st.set_page_config(page_title="Magazyn", layout="wide")

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ---------------- FUNCTIONS ----------------
@st.cache_data
def load_products():
    data = supabase.table("produkty").select(
        "id, nazwa, liczba, cena, kategorie(nazwa)"
    ).execute()
    return pd.DataFrame(data.data)

@st.cache_data
def load_categories():
    data = supabase.table("kategorie").select("*").execute()
    return pd.DataFrame(data.data)

def add_product(name, qty, price, category_id):
    supabase.table("produkty").insert({
        "nazwa": name,
        "liczba": qty,
        "cena": price,
        "kategoria_id": category_id
    }).execute()
    st.cache_data.clear()

def delete_product(product_id):
    supabase.table("produkty").delete().eq("id", product_id).execute()
    st.cache_data.clear()

def update_product(pid, name, qty, price):
    supabase.table("produkty").update({
        "nazwa": name,
        "liczba": qty,
        "cena": price
    }).eq("id", pid).execute()
    st.cache_data.clear()

# ---------------- UI ----------------
st.title("📦 Aplikacja magazynowa")

tab1, tab2, tab3 = st.tabs(["📋 Produkty", "➕ Dodaj", "📊 Statystyki"])

# -------- TAB 1: PRODUCTS --------
with tab1:
    products = load_products()

    search = st.text_input("🔍 Szukaj produktu")
    if search:
        products = products[products["nazwa"].str.contains(search, case=False)]

    st.dataframe(products, use_container_width=True)

    st.subheader("✏️ Edycja / Usuwanie")
    selected = st.selectbox("Wybierz produkt", products["id"])

    product = products[products["id"] == selected].iloc[0]

    new_name = st.text_input("Nazwa", product["nazwa"])
    new_qty = st.number_input("Ilość", value=int(product["liczba"]))
    new_price = st.number_input("Cena", value=float(product["cena"]))

    col1, col2 = st.columns(2)
    if col1.button("💾 Zapisz zmiany"):
        update_product(selected, new_name, new_qty, new_price)
        st.success("Zaktualizowano")

    if col2.button("🗑️ Usuń produkt"):
        delete_product(selected)
        st.warning("Usunięto produkt")

# -------- TAB 2: ADD PRODUCT --------
with tab2:
    categories = load_categories()

    name = st.text_input("Nazwa produktu")
    qty = st.number_input("Ilość", min_value=0)
    price = st.number_input("Cena", min_value=0.0)

    category = st.selectbox(
        "Kategoria",
        categories["nazwa"]
    )
    category_id = categories[categories["nazwa"] == category]["id"].iloc[0]

    if st.button("➕ Dodaj produkt"):
        add_product(name, qty, price, category_id)
        st.success("Produkt dodany")

# -------- TAB 3: STATS --------
with tab3:
    products = load_products()

    total_products = len(products)
    total_value = (products["liczba"] * products["cena"]).sum()

    col1, col2 = st.columns(2)
    col1.metric("📦 Liczba produktów", total_products)
    col2.metric("💰 Wartość magazynu", f"{total_value:.2f} zł")

    low_stock = products[products["liczba"] < 5]
    st.subheader("⚠️ Niski stan magazynowy")
    st.dataframe(low_stock)
