import streamlit as st
import pandas as pd
from supabase import create_client

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
# 2. POŁĄCZENIE Z SUPABASE
# =========================
# Upewnij się, że w Secrets masz: SUPABASE_URL i SUPABASE_KEY
try:
    supabase = create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_KEY"]
    )
except Exception as e:
    st.error("Błąd połączenia z bazą danych. Sprawdź Secrets w ustawieniach aplikacji.")
    st.stop()

# =========================
# 3. FUNKCJE OPERACJI NA BAZIE
# =========================

@st.cache_data(ttl=5)
def pobierz_kategorie():
    """Pobiera listę dostępnych kategorii ze schematu."""
    try:
        res = supabase.table("Kategorie").select("id, nazwa").execute()
        return pd.DataFrame(res.data)
    except Exception as e:
        st.error(f"Błąd kategorii: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=5)
def pobierz_magazyn():
    """Pobiera produkty łącząc je z tabelą Kategorie (JOIN)."""
    try:
        # Pobieramy produkty i dołączamy nazwę kategorii przez klucz obcy kategoria_id
        res = supabase.table("produkty").select(
            "id, nazwa, liczba, cena, kategoria_id, Kategorie(nazwa)"
        ).order("nazwa").execute()
        
        if not res.data:
            return pd.DataFrame()

        # Przetwarzanie zagnieżdżonych danych z relacji
        dane = []
        for item in res.data:
            dane.append({
                "ID": item["id"],
                "Produkt": item["nazwa"],
                "Liczba": item["liczba"],
                "Cena (zł)": item["cena"],
                "Kategoria": item["Kategorie"]["nazwa"] if item["Kategorie"] else "Brak"
            })
        return pd.DataFrame(dane)
    except Exception as e:
        st.error(f"Błąd pobierania: {e}")
        return pd.DataFrame()

def dodaj_produkt(nazwa, liczba, cena, kategoria_id):
    """Wstawia nowy wiersz do tabeli produkty."""
    try:
        supabase.table("produkty").insert({
            "nazwa": nazwa,
            "liczba": liczba,
            "cena": cena,
            "kategoria_id": kategoria_id
        }).execute()
        st.success(f"✅ Dodano: {nazwa}")
        st.cache_data.clear()
    except Exception as e:
        st.error(f"Błąd zapisu: {e}")

def usun_produkt(id_produktu):
    """Usuwa produkt na podstawie klucza głównego ID."""
    try:
        supabase.table("produkty").delete().eq("id", id_produktu).execute()
        st.success("🗑️ Produkt usunięty")
        st.cache_data.clear()
    except Exception as e:
        st.error(f"Błąd usuwania: {e}")

# =========================
# 4. INTERFEJS UŻYTKOWNIKA
# =========================

tab1, tab2 = st.tabs(["📋 Widok Magazynu", "➕ Dodaj Produkt"])

# --- TABELA PRODUKTÓW ---
with tab1:
    st.header("Aktualny stan magazynu")
    df = pobierz_magazyn()
    
    if df.empty:
        st.info("Magazyn jest pusty.")
    else:
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        st.divider()
        st.subheader("Usuwanie produktu")
        # Wybór produktu do usunięcia na podstawie ID
        do_usuniecia = st.selectbox(
            "Wybierz towar do usunięcia",
            options=df["ID"].tolist(),
            format_func=lambda x: df[df["ID"] == x]["Produkt"].iloc[0]
        )
        if st.button("Usuń wybrany produkt", type="primary"):
            usun_produkt(do_usuniecia)
            st.rerun()

# --- FORMULARZ DODAWANIA ---
with tab2:
    st.header("Nowy towar")
    kat_df = pobierz_kategorie()
    
    if kat_df.empty:
        st.warning("⚠️ Brak kategorii w bazie. Dodaj je najpierw w Supabase.")
    else:
        with st.form("form_dodawania", clear_on_submit=True):
            nazwa_p = st.text_input("Nazwa produktu")
            liczba_p = st.number_input("Ilość", min_value=0, step=1)
            cena_p = st.number_input("Cena za sztukę", min_value=0.0, format="%.2f")
            
            # Mapowanie nazw kategorii na ich ID z bazy
            opcje_kat = dict(zip(kat_df["nazwa"], kat_df["id"]))
            wybrana_kat = st.selectbox("Kategoria", options=opcje_kat.keys())
            
            if st.form_submit_button("Zapisz w bazie"):
                if nazwa_p:
                    dodaj_produkt(nazwa_p, liczba_p, cena_p, opcje_kat[wybrana_kat])
                    st.rerun()
                else:
                    st.error("Nazwa nie może być pusta!")
