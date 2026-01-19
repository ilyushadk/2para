import streamlit as st
import pandas as pd
from supabase import create_client
import httpx

# =========================
# 1. KONFIGURACJA STRONY
# =========================
st.set_page_config(
    page_title="Prosty Magazyn",
    page_icon="📦",
    layout="centered"
)

st.title("📦 Prosty Magazyn (Supabase)")

# =========================
# 2. POŁĄCZENIE Z BAZĄ (Z OBSŁUGĄ BŁĘDÓW)
# =========================
def init_connection():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except KeyError:
        st.error("❌ Brakuje kluczy w Secrets! Dodaj SUPABASE_URL i SUPABASE_KEY.")
        st.stop()
    except Exception as e:
        st.error(f"❌ Błąd inicjalizacji: {e}")
        st.stop()

supabase = init_connection()

# =========================
# 3. FUNKCJE BAZODANOWE
# =========================

@st.cache_data(ttl=10)
def pobierz_kategorie():
    """Pobiera listę kategorii ze schematu."""
    try:
        res = supabase.table("Kategorie").select("id, nazwa").execute()
        return pd.DataFrame(res.data)
    except Exception as e:
        st.error(f"Nie można pobrać kategorii: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=10)
def pobierz_magazyn():
    """Pobiera produkty łącząc je z tabelą Kategorie (JOIN)."""
    try:
        # Pobieramy dane zgodnie ze schematem: id, nazwa, liczba, cena, kategoria_id
        res = supabase.table("produkty").select(
            "id, nazwa, liczba, cena, kategoria_id, Kategorie(nazwa)"
        ).order("nazwa").execute()
        
        if not res.data:
            return pd.DataFrame()

        # Spłaszczanie struktury (wyciąganie nazwy kategorii z relacji)
        parsed_data = []
        for item in res.data:
            parsed_data.append({
                "ID": item["id"],
                "Produkt": item["nazwa"],
                "Liczba": item["liczba"],
                "Cena (zł)": item["cena"],
                "Kategoria": item["Kategorie"]["nazwa"] if item.get("Kategorie") else "Brak"
            })
        return pd.DataFrame(parsed_data)
    except httpx.ConnectError:
        st.error("❌ Brak połączenia z serwerem Supabase. Sprawdź swój URL w Secrets.")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Błąd pobierania danych: {e}")
        return pd.DataFrame()

def dodaj_produkt(nazwa, liczba, cena, kat_id):
    try:
        supabase.table("produkty").insert({
            "nazwa": nazwa,
            "liczba": liczba,
            "cena": cena,
            "kategoria_id": kat_id
        }).execute()
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Błąd zapisu: {e}")
        return False

def usun_produkt(prod_id):
    try:
        supabase.table("produkty").delete().eq("id", prod_id).execute()
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Błąd usuwania: {e}")
        return False

# =========================
# 4. INTERFEJS UŻYTKOWNIKA
# =========================

tab1, tab2 = st.tabs(["📋 Widok Magazynu", "➕ Nowy Produkt"])

# --- TABELA PRODUKTÓW ---
with tab1:
    st.header("Aktualne stany")
    df = pobierz_magazyn()
    
    if df.empty:
        st.info("Brak produktów w bazie lub błąd połączenia.")
    else:
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        st.divider()
        st.subheader("🗑️ Usuwanie")
        do_usuniecia = st.selectbox(
            "Wybierz produkt do usunięcia",
            options=df["ID"].tolist(),
            format_func=lambda x: df[df["ID"] == x]["Produkt"].iloc[0]
        )
        
        if st.button("Usuń wybrany produkt", type="primary"):
            if usun_produkt(do_usuniecia):
                st.success("Usunięto pomyślnie!")
                st.rerun()

# --- FORMULARZ DODAWANIA ---
with tab2:
    st.header("Dodaj nowy towar")
    kat_df = pobierz_kategorie()
    
    if kat_df.empty:
        st.warning("⚠️ Baza kategorii jest pusta. Dodaj kategorie w Supabase.")
    else:
        with st.form("form_dodaj", clear_on_submit=True):
            nazwa_in = st.text_input("Nazwa produktu")
            liczba_in = st.number_input("Liczba (szt.)", min_value=0, step=1)
            cena_in = st.number_input("Cena (zł)", min_value=0.0, format="%.2f")
            
            # Tworzymy słownik do mapowania Nazwa -> ID kategorii
            opcje_kat = dict(zip(kat_df["nazwa"], kat_df["id"]))
            wybrana_kat_nazwa = st.selectbox("Wybierz kategorię", options=opcje_kat.keys())
            
            if st.form_submit_button("Zapisz w magazynie"):
                if not nazwa_in:
                    st.error("Podaj nazwę produktu!")
                else:
                    id_kat = opcje_kat[wybrana_kat_nazwa]
                    if dodaj_produkt(nazwa_in, liczba_in, cena_in, id_kat):
                        st.success(f"Dodano produkt: {nazwa_in}")
                        st.rerun()
