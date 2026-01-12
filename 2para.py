import streamlit as st
import pandas as pd
from datetime import date
from supabase import create_client

# =========================
# KONFIGURACJA SUPABASE
# =========================
SUPABASE_URL = "https://xhhkkygvbcyjafcfdsyo.supabase.co"
SUPABASE_KEY = "sb_publishable_VZK4gqxn6BVg-YIRUBX_Tw_1EsNzfci"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# =========================
# STREAMLIT
# =========================
st.set_page_config(page_title="Prosty Magazyn", layout="centered")
st.title("📦 Prosty Magazyn (Supabase)")

# =========================
# FUNKCJE POMOCNICZE
# =========================
def pobierz_magazyn():
    response = supabase.table("magazyn").select("*").order("towar").execute()
    return pd.DataFrame(response.data)

def zapisz_towar(towar, stan_aktualny, stan_docelowy, cena, data):
    braki = max(stan_docelowy - stan_aktualny, 0)

    supabase.table("magazyn").upsert(
        {
            "towar": towar,
            "stan_aktualny": stan_aktualny,
            "stan_docelowy": stan_docelowy,
            "braki": braki,
            "cena": cena,
            "data": str(data)
        },
        on_conflict="towar"
    ).execute()


def usun_towar(towar):
    supabase.table("magazyn").delete().eq("towar", towar).execute()

# =========================
# DODAWANIE / AKTUALIZACJA
# =========================
st.header("➕ Dodaj / zaktualizuj towar")

with st.form("formularz"):
    towar = st.text_input("Nazwa towaru")
    stan_aktualny = st.number_input("Stan aktualny", min_value=0, step=1)
    stan_docelowy = st.number_input("Stan docelowy", min_value=0, step=1)
    cena = st.number_input("Cena (zł)", min_value=0.0, step=0.01, format="%.2f")
    data = st.date_input("Data", value=date.today())

    submitted = st.form_submit_button("Zapisz")

    if submitted:
        if not towar:
            st.error("Podaj nazwę towaru")
        else:
            zapisz_towar(towar, stan_aktualny, stan_docelowy, cena, data)
            st.success("Towar zapisany")
            st.rerun()

# =========================
# WYŚWIETLANIE MAGAZYNU
# =========================
st.header("📋 Stan magazynu")

df = pobierz_magazyn()

if df.empty:
    st.info("Brak danych w magazynie")
else:
    st.dataframe(
        df[[
            "towar",
            "stan_aktualny",
            "stan_docelowy",
            "braki",
            "cena",
            "data"
        ]],
        use_container_width=True
    )

    # Towary z brakami
    st.subheader("❗ Towary z brakami")

    braki_df = df[df["braki"] > 0]

    if braki_df.empty:
        st.success("Brak braków magazynowych 🎉")
    else:
        st.dataframe(braki_df, use_container_width=True)

# =========================
# USUWANIE TOWARU
# =========================
st.header("🗑️ Usuń towar")

if df.empty:
    st.info("Brak towarów do usunięcia")
else:
    towar_do_usuniecia = st.selectbox(
        "Wybierz towar do usunięcia",
        df["towar"]
    )

    if st.button("Usuń towar"):
        usun_towar(towar_do_usuniecia)
        st.success(f"Usunięto towar: {towar_do_usuniecia}")
        st.rerun()
