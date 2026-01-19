import streamlit as st
import pandas as pd
from supabase import create_client

# ==========================================
# 1. KONFIGURACJA STRONY I POŁĄCZENIA
# ==========================================
st.set_page_config(page_title="Prosty Magazyn", page_icon="📦")

st.title("📦 Prosty Magazyn (Supabase)")

# Próba połączenia z bazą danych przy użyciu st.secrets
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase = create_client(url, key)
except Exception as e:
    st.error("❌ Błąd konfiguracji! Dodaj SUPABASE_URL i SUPABASE_KEY w Secrets.")
    st.stop()

# ==========================================
# 2. FUNKCJE OBSŁUGI BAZY DANYCH
# ==========================================

@st.cache_data(ttl=5)
def pobierz_kategorie():
    """Pobiera ID i nazwy z tabeli Kategorie."""
    res = supabase.table("Kategorie").select("id, nazwa").execute()
    return pd.DataFrame(res.data)

@st.cache_data(ttl=5)
def pobierz_magazyn():
    """Pobiera produkty wraz z nazwami kategorii (Join)."""
    # Pobieramy kolumny: id, nazwa, liczba, cena oraz nazwa z relacji Kategorie
    res = supabase.table("produkty").select(
        "id, nazwa, liczba, cena, kategoria_id, Kategorie(nazwa)"
    ).order("nazwa").execute()
    
    if not res.data:
        return pd.DataFrame()

    # Spłaszczanie danych, aby nazwa kategorii była w jednej linii
    rows = []
    for item in res.data:
        rows.append({
            "ID": item["id"],
            "Produkt": item["nazwa"],
            "Liczba": item["liczba"],
            "Cena": item["cena"],
            "Kategoria": item["Kategorie"]["nazwa"] if item["Kategorie"] else "Brak"
        })
    return pd.DataFrame(rows)

def dodaj_produkt(nazwa, liczba, cena, kat_id):
    """Wstawia nowy rekord do tabeli produkty."""
    supabase.table("produkty").insert({
        "nazwa": nazwa,
        "liczba": liczba,
        "cena": cena,
        "kategoria_id": kat_id
    }).execute()
    st.cache_data.clear()

def usun_produkt(prod_id):
    """Usuwa rekord na podstawie ID."""
    supabase.table("produkty").delete().eq("id", prod_id).execute()
    st.cache_data.clear()

# ==========================================
# 3. INTERFEJS UŻYTKOWNIKA (UI)
# ==========================================

tab1, tab2 = st.tabs(["📋 Lista Produktów", "➕ Dodaj Nowy"])

with tab1:
    st.header("Stan Magazynu")
    df = pobierz_magazyn()
    
    if df.empty:
        st.info("Magazyn jest obecnie pusty.")
    else:
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        st.divider()
        st.subheader("🗑️ Usuń produkt")
        # Wybór produktu do usunięcia
        opcje_usun = df.set_index("ID")["Produkt"].to_dict()
        wybrany_id = st.selectbox("Wybierz towar", options=opcje_usun.keys(), format_func=lambda x: opcje_usun[x])
        
        if st.button("Usuń trwale", type="primary"):
            usun_produkt(wybrany_id)
            st.rerun()

with tab2:
    st.header("Dodawanie towaru")
    kat_df = pobierz_kategorie()
    
    if kat_df.empty:
        st.warning("Najpierw dodaj kategorie w panelu Supabase!")
    else:
        with st.form("form_dodaj", clear_on_submit=True):
            f_nazwa = st.text_input("Nazwa produktu")
            f_liczba = st.number_input("Ilość (liczba)", min_value=0, step=1)
            f_cena = st.number_input("Cena (numeric)", min_value=0.0, format="%.2f")
            
            # Mapowanie kategorii do selectboxa
            dict_kat = dict(zip(kat_df["nazwa"], kat_df["id"]))
            f_kat = st.selectbox("Kategoria", options=dict_kat.keys())
            
            if st.form_submit_button("Zapisz w bazie"):
                if f_nazwa:
                    dodaj_produkt(f_nazwa, f_liczba, f_cena, dict_kat[f_kat])
                    st.success(f"Dodano: {f_nazwa}")
                    st.rerun()
                else:
                    st.error("Podaj nazwę produktu!")
