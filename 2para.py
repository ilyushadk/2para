import streamlit as st
import pandas as pd
from supabase import create_client
import httpx

# ==========================================
# 1. KONFIGURACJA STRONY
# ==========================================
st.set_page_config(
    page_title="Prosty Magazyn",
    page_icon="📦",
    layout="centered"
)

st.title("📦 Prosty Magazyn (Supabase)")

# ==========================================
# 2. POŁĄCZENIE Z BAZĄ DANYCH
# ==========================================
def init_connection():
    try:
        # Pobieranie danych z sekcji Secrets
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except KeyError:
        # Obsługa błędu widocznego na zrzucie ekranu
        st.error("❌ BŁĄD: Brak kluczy w Secrets! Dodaj SUPABASE_URL i SUPABASE_KEY w ustawieniach aplikacji.")
        st.stop()
    except Exception as e:
        st.error(f"❌ BŁĄD INICJALIZACJI: {e}")
        st.stop()

supabase = init_connection()

# ==========================================
# 3. FUNKCJE BAZODANOWE (Zgodne ze schematem)
# ==========================================

@st.cache_data(ttl=10)
def pobierz_kategorie():
    """Pobiera ID i nazwy z tabeli Kategorie."""
    try:
        res = supabase.table("Kategorie").select("id, nazwa").execute()
        return pd.DataFrame(res.data)
    except Exception as e:
        st.error(f"⚠️ Nie udało się pobrać kategorii: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=10)
def pobierz_magazyn():
    """Pobiera produkty wraz z nazwami ich kategorii (JOIN)."""
    try:
        # Zapytanie zgodne ze strukturą: id, nazwa, liczba, cena, kategoria_id
        res = supabase.table("produkty").select(
            "id, nazwa, liczba, cena, Kategorie(nazwa)"
        ).order("nazwa").execute()
        
        if not res.data:
            return pd.DataFrame()

        # Przetwarzanie danych do płaskiej tabeli
        flat_data = []
        for item in res.data:
            flat_data.append({
                "ID": item["id"],
                "Produkt": item["nazwa"],
                "Ilość": item["liczba"],
                "Cena (zł)": item["cena"],
                "Kategoria": item["Kategorie"]["nazwa"] if item.get("Kategorie") else "Brak"
            })
        return pd.DataFrame(flat_data)
    except httpx.ConnectError:
        # Rozwiązanie błędu widocznego na zrzutach
        st.error("❌ BRAK POŁĄCZENIA: Sprawdź, czy SUPABASE_URL w Secrets jest poprawny i czy projekt nie jest uśpiony.")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"⚠️ Błąd pobierania danych: {e}")
        return pd.DataFrame()

def dodaj_produkt(nazwa, liczba, cena, kategoria_id):
    """Zapisuje nowy produkt do tabeli produkty."""
    try:
        supabase.table("produkty").insert({
            "nazwa": nazwa,
            "liczba": int(liczba),
            "cena": float(cena),
            "kategoria_id": int(kategoria_id)
        }).execute()
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"❌ Błąd zapisu: {e}")
        return False

# ==========================================
# 4. INTERFEJS UŻYTKOWNIKA (Zakładki)
# ==========================================
tab1, tab2 = st.tabs(["📋 Widok Magazynu", "➕ Nowy Produkt"])

with tab1:
    st.header("Aktualne stany")
    df = pobierz_magazyn()
    
    if df.empty:
        st.info("Magazyn jest obecnie pusty lub wystąpił błąd połączenia.")
    else:
        st.dataframe(df, use_container_width=True, hide_index=True)

with tab2:
    st.header("Dodaj nowy towar")
    kat_df = pobierz_kategorie()
    
    if kat_df.empty:
        st.warning("⚠️ Baza kategorii jest pusta. Dodaj rekordy do tabeli 'Kategorie' w Supabase.")
    else:
        with st.form("form_dodaj", clear_on_submit=True):
            p_nazwa = st.text_input("Nazwa produktu")
            p_liczba = st.number_input("Ilość (szt.)", min_value=0, step=1)
            p_cena = st.number_input("Cena (zł)", min_value=0.0, format="%.2f")
            
            # Mapowanie nazw na ID kategorii
            kat_map = dict(zip(kat_df["nazwa"], kat_df["id"]))
            p_kat = st.selectbox("Wybierz kategorię", options=kat_map.keys())
            
            if st.form_submit_button("Zapisz produkt"):
                if not p_nazwa:
                    st.error("Podaj nazwę produktu!")
                else:
                    if dodaj_produkt(p_nazwa, p_liczba, p_cena, kat_map[p_kat]):
                        st.success(f"✅ Produkt '{p_nazwa}' został dodany!")
                        st.rerun()
