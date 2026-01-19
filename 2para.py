import streamlit as st
import pandas as pd
from supabase import create_client
import httpx

# Konfiguracja strony
st.set_page_config(page_title="Prosty Magazyn", page_icon="📦")
st.title("📦 Prosty Magazyn (Supabase)")

# Połączenie z bazą
def init_connection():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception as e:
        st.error(f"❌ Błąd kluczy w Secrets! Sprawdź czy są poprawnie wpisane.")
        st.stop()

supabase = init_connection()

# Funkcje pobierania danych
@st.cache_data(ttl=10)
def pobierz_magazyn():
    try:
        # Pobieranie produktów i nazwy kategorii przez relację
        res = supabase.table("produkty").select(
            "id, nazwa, liczba, cena, Kategorie(nazwa)"
        ).order("nazwa").execute()
        
        if not res.data:
            return pd.DataFrame()

        # Spłaszczanie danych dla tabeli
        rows = []
        for item in res.data:
            rows.append({
                "ID": item["id"],
                "Produkt": item["nazwa"],
                "Liczba": item["liczba"],
                "Cena (zł)": item["cena"],
                "Kategoria": item["Kategorie"]["nazwa"] if item.get("Kategorie") else "Brak"
            })
        return pd.DataFrame(rows)
    except Exception as e:
        st.error(f"❌ Brak połączenia z serwerem Supabase.")
        return pd.DataFrame()

@st.cache_data(ttl=10)
def pobierz_kategorie():
    res = supabase.table("Kategorie").select("id, nazwa").execute()
    return pd.DataFrame(res.data)

# Interfejs
tab1, tab2 = st.tabs(["📋 Widok Magazynu", "➕ Dodaj Nowy"])

with tab1:
    st.header("Aktualne stany")
    df = pobierz_magazyn()
    if df.empty:
        st.info("Magazyn jest pusty lub błąd połączenia.")
    else:
        st.dataframe(df, use_container_width=True, hide_index=True)

with tab2:
    st.header("Dodaj produkt")
    kat_df = pobierz_kategorie()
    if kat_df.empty:
        st.warning("⚠️ Dodaj najpierw kategorie w Supabase!")
    else:
        with st.form("dodaj"):
            nazwa = st.text_input("Nazwa produktu")
            liczba = st.number_input("Ilość", min_value=0, step=1)
            cena = st.number_input("Cena", min_value=0.0, format="%.2f")
            kat_map = dict(zip(kat_df["nazwa"], kat_df["id"]))
            kat_wybrana = st.selectbox("Kategoria", options=kat_map.keys())
            
            if st.form_submit_button("Zapisz"):
                if nazwa:
                    supabase.table("produkty").insert({
                        "nazwa": nazwa, "liczba": liczba, 
                        "cena": cena, "kategoria_id": kat_map[kat_wybrana]
                    }).execute()
                    st.cache_data.clear()
                    st.rerun()
