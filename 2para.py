import streamlit as st
import pandas as pd
from supabase import create_client
import httpx

st.set_page_config(page_title="Prosty Magazyn", page_icon="📦")
st.title("📦 Prosty Magazyn (Supabase)")

def init_connection():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception as e:
        st.error("BŁĄD: Sprawdź formatowanie w Secrets (musi być w jednej linii!)")
        st.stop()

supabase = init_connection()

@st.cache_data(ttl=10)
def pobierz_magazyn():
    try:
        # Próba pobrania danych z relacją Kategorie
        res = supabase.table("produkty").select("id, nazwa, liczba, cena, Kategorie(nazwa)").execute()
        
        flat_data = []
        for item in res.data:
            flat_data.append({
                "ID": item["id"],
                "Produkt": item["nazwa"],
                "Liczba": item["liczba"],
                "Cena": item["cena"],
                "Kategoria": item["Kategorie"]["nazwa"] if item.get("Kategorie") else "Brak"
            })
        return pd.DataFrame(flat_data)
    except Exception as e:
        st.error(f"Błąd bazy danych: {e}")
        st.info("💡 Wskazówka: Sprawdź czy w Supabase wyłączono RLS lub dodano uprawnienia (Policies).")
        return pd.DataFrame()

@st.cache_data(ttl=10)
def pobierz_kategorie():
    try:
        res = supabase.table("Kategorie").select("id, nazwa").execute()
        return pd.DataFrame(res.data)
    except Exception:
        return pd.DataFrame()

# --- Interfejs ---
tab1, tab2 = st.tabs(["📋 Widok", "➕ Dodaj"])

with tab1:
    df = pobierz_magazyn()
    if not df.empty:
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.warning("Brak danych do wyświetlenia.")

with tab2:
    kat_df = pobierz_kategorie()
    if kat_df.empty:
        st.error("Nie można pobrać kategorii. Sprawdź uprawnienia tabeli 'Kategorie' w Supabase.")
    else:
        with st.form("dodaj_form"):
            nazwa = st.text_input("Nazwa")
            liczba = st.number_input("Liczba", step=1)
            cena = st.number_input("Cena", step=0.01)
            kat_map = dict(zip(kat_df["nazwa"], kat_df["id"]))
            wybrana_kat = st.selectbox("Kategoria", options=kat_map.keys())
            
            if st.form_submit_button("Zapisz"):
                supabase.table("produkty").insert({
                    "nazwa": nazwa, "liczba": liczba, "cena": cena, "kategoria_id": kat_map[wybrana_kat]
                }).execute()
                st.cache_data.clear()
                st.rerun()
