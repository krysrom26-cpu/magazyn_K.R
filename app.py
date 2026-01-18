import streamlit as st
import pandas as pd
from supabase import create_client

# ================== CONFIG ==================
st.set_page_config(
    page_title="📦 Magazyn",
    layout="wide"
)

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ================== DATA ==================
@st.cache_data
def load_categories():
    data = supabase.table("kategorie").select("*").execute().data
    return pd.DataFrame(data)

@st.cache_data
def load_products():
    products = supabase.table("produkty").select("*").execute().data
    categories = supabase.table("kategorie").select("*").execute().data

    if not products:
        return pd.DataFrame()

    df_p = pd.DataFrame(products)
    df_c = pd.DataFrame(categories)

    df = df_p.merge(
        df_c,
        left_on="kategoria_id",
        right_on="id",
        how="left",
        suffixes=("", "_kat")
    )

    df = df.rename(columns={"nazwa_kat": "kategoria"})
    return df

def clear_cache():
    st.cache_data.clear()

# ================== DB OPERATIONS ==================
def add_product(name, qty, price, category_id):
    supabase.table("produkty").insert({
        "nazwa": name,
        "liczba": qty,
        "cena": price,
        "kategoria_id": category_id
    }).execute()
    clear_cache()

def update_product(pid, name, qty, price):
    supabase.table("produkty").update({
        "nazwa": name,
        "liczba": qty,
        "cena": price
    }).eq("id", pid).execute()
    clear_cache()

def delete_product(pid):
    supabase.table("produkty").delete().eq("id", pid).execute()
    clear_cache()

# ================== UI ==================
st.title("📦 Aplikacja magazynowa")

tab1, tab2, tab3 = st.tabs(["📋 Produkty", "➕ Dodaj produkt", "📊 Statystyki"])

# ================== TAB 1 ==================
with tab1:
    products = load_products()

    if products.empty:
        st.info("📭 Brak produktów w magazynie")
        st.stop()

    search = st.text_input("🔍 Wyszukaj produkt")
    if search:
        products = products[products["nazwa"].str.contains(search, case=False)]

    st.dataframe(
        products[["id", "nazwa", "kategoria", "liczba", "cena"]],
        use_container_width=True
    )

    st.subheader("✏️ Edytuj / Usuń")

    selected_name = st.selectbox(
        "Wybierz produkt",
        products["nazwa"]
    )

    product = products[products["nazwa"] == selected_name].iloc[0]

    new_name = st.text_input("Nazwa", product["nazwa"])
    new_qty = st.number_input("Ilość", min_value=0, value=int(product["liczba"]))
    new_price = st.number_input("Cena", min_value=0.0, value=float(product["cena"]))

    col1, col2 = st.columns(2)

    if col1.button("💾 Zapisz zmiany"):
        update_product(product["id"], new_name, new_qty, new_price)
        st.success("Produkt zaktualizowany")

    if col2.button("🗑️ Usuń produkt"):
        delete_product(product["id"])
        st.warning("Produkt usunięty")

# ================== TAB 2 ==================
with tab2:
    categories = load_categories()

    if categories.empty:
        st.warning("Brak kategorii w bazie")
        st.stop()

    name = st.text_input("Nazwa produktu")
    qty = st.number_input("Ilość", min_value=0)
    price = st.number_input("Cena", min_value=0.0)

    category_name = st.selectbox("Kategoria", categories["nazwa"])
    category_id = categories[categories["nazwa"] == category_name]["id"].iloc[0]

    if st.button("➕ Dodaj produkt"):
        if name:
            add_product(name, qty, price, category_id)
            st.success("Produkt dodany")
        else:
            st.error("Podaj nazwę produktu")

# ================== TAB 3 ==================
with tab3:
    products = load_products()

    if products.empty:
        st.info("Brak danych do statystyk")
        st.stop()

    total_products = len(products)
    total_value = (products["liczba"] * products["cena"]).sum()

    col1, col2 = st.columns(2)
    col1.metric("📦 Liczba produktów", total_products)
    col2.metric("💰 Wartość magazynu", f"{total_value:.2f} zł")

    st.subheader("⚠️ Niski stan magazynowy (<5)")
    st.dataframe(products[products["liczba"] < 5])
