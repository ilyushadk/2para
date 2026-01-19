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
# 2. INICJALIZACJA POŁĄCZENIA
# ==========================================
def init_connection():
    try:
        # Pobieranie danych z Secrets (Ustawienia w Streamlit Cloud)
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except KeyError:
        st.error("❌ Błąd: Brak kluczy SUPABASE_URL lub SUPABASE_KEY w Secrets!")
        st.stop()
    except Exception as e:
        st.error(f"❌ Błąd połączenia: {e}")
        st.stop()

supabase = init_connection()

# ==========================================
# 3. FUNKCJE BAZODANOWE (Zgodne ze schematem)
# ==========================================

@st.cache_data(ttl=10)
def pobierz_kategorie():
    """Pobiera dane z tabeli Kategorie [id, nazwa, opis]"""
    try:
        res = supabase.table("Kategorie").select("id, nazwa").execute()
        return pd.DataFrame(res.data)
    except Exception as e:
        st.error(f"Błąd pobierania kategorii: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=10)
def pobierz_magazyn():
    """Pobiera produkty łącząc je z kategoriami (JOIN)"""
    try:
        # Zapytanie pobierające pola ze schematu: id, nazwa, liczba, cena, kategoria_id
        res = supabase.table("produkty").select(
            "id, nazwa, liczba, cena, Kategorie(nazwa)"
        ).order("nazwa").execute()
        
        if not res.data:
            return pd.DataFrame()

        # Przetworzenie danych dla czytelnego wyświetlania
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
        st.error("❌ Brak połączenia z serwerem. Sprawdź czy SUPABASE_URL jest poprawny.")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Wystąpił błąd: {e}")
        return pd.DataFrame()

def dodaj_produkt(nazwa, liczba, cena, kategoria_id):
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
        st.error(f"Błąd podczas zapisu: {e}")
        return False

def usun_produkt(produkt_id):
    try:
        supabase.table("produkty").delete().eq("id", produkt_id).execute()
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Błąd podczas usuwania: {e}")
        return False

# ==========================================
# 4. INTERFEJS UŻYTKOWNIKA (Tabs)
# ==========================================
tab1, tab2 = st.tabs(["📋 Widok Magazynu", "➕ Nowy Produkt"])

with tab1:
    st.header("Aktualne stany")
    df = pobierz_magazyn()
    
    if df.empty:
        st.info("Brak produktów w bazie lub błąd połączenia.")
    else:
        # Wyświetlanie tabeli produktów
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        st.divider()
        st.subheader("🗑️ Usuń produkt")
        
        # Wybór produktu do usunięcia na podstawie listy
        id_list = df["ID"].tolist()
        prod_names = df["Produkt"].tolist()
        options = dict(zip(id_list, prod_names))
        
        selected_id = st.selectbox(
            "Wybierz towar do usunięcia", 
            options=options.keys(),
            format_func=lambda x: options[x]
        )
        
        if st.button("Usuń trwale", type="primary"):
            if usun_produkt(selected_id):
                st.success("Produkt został usunięty.")
                st.rerun()

with tab2:
    st.header("Dodaj nowy towar")
    kat_df = pobierz_kategorie()
    
    if kat_df.empty:
        st.warning("⚠️ Baza kategorii jest pusta. Dodaj kategorie w panelu Supabase.")
    else:
        with st.form("dodawanie_produktu", clear_on_submit=True):
            nowa_nazwa = st.text_input("Nazwa produktu")
            nowa_liczba = st.number_input("Ilość (szt.)", min_value=0, step=1)
            nowa_cena = st.number_input("Cena (zł)", min_value=0.0, format="%.2f")
            
            # Mapowanie kategorii dla selectboxa
            kat_options = dict(zip(kat_df["nazwa"], kat_df["id"]))
            wybrana_kat = st.selectbox("Kategoria", options=kat_options.keys())
            
            submit = st.form_submit_button("Zapisz w bazie")
            
            if submit:
                if not nowa_nazwa:
                    st.error("Podaj nazwę produktu!")
                else:
                    success = dodaj_produkt(
                        nowa_nazwa, 
                        nowa_liczba, 
                        nowa_cena, 
                        kat_options[wybrana_kat]
                    )
                    if success:
                        st.success(f"Dodano produkt: {nowa_nazwa}")
                        st.rerun()
