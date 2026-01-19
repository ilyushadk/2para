import streamlit as st
import pandas as pd
from datetime import date
from supabase import create_client

# =========================
# STREAMLIT CONFIG
# =========================
st.set_page_config(
    page_title="Prosty Magazyn",
    page_icon="📦",
    layout="centered"
)

st.title("📦 Prosty Magazyn (Supabase)")

# =========================
# SUPABASE CONFIG
# =========================
supabase = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_KEY"]
)

# =========================
# FUNKCJE
# =========================
@st.cache_data(ttl=10)
def pobierz_magazyn():
    try:
        response = (
            supabase
            .table("magazyn")
            .select("*")
            .order("towar", desc=False)
            .execute()
        )

        if response.data is None:
            return pd.DataFrame()

        return pd.DataFrame(response.data)

    except Exception as e:
        st.error(f"Błąd pobierania danych: {e}")
        return pd.DataFrame()


def zapisz_towar(towar, stan_aktualny, stan_docelowy, cena, data):
    braki = max(int(stan_docelowy) - int(stan_aktualny), 0)

    try:
        supabase.table("magazyn").upsert(
            {
                "towar": towar,
                "stan_aktualny": int(stan_aktualny),
                "stan_docelowy": int(stan_docelowy),
                "braki": braki,
                "cena": float(cena),
                "data": data.isoformat()
            },
            on_conflict="towar"
        ).execute()

    except Exception as e:
        st.error(f"Błąd zapisu: {e}")


def usun_towar(towar):
    try:
        supabase.table("magazyn").delete().eq("towar", towar).execute()
    except Exception as e:
        st.error(f"Błąd usuwania: {e}")

# =========================
# FORMULARZ
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
        if not towar.strip():
            st.error("❌ Podaj nazwę towaru")
        else:
            zapisz_towar(towar, stan_aktualny, stan_docelowy, cena, data)
            st.success("✅ Towar zapisany")
            st.cache_data.clear()
            st.rerun()

# =========================
# MAGAZYN
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
        use_container_width=True,
        hide_index=True
    )

    # -------------------------
    # BRAKI
    # -------------------------
    st.subheader("❗ Towary z brakami")

    braki_df = df[df["braki"] > 0]

    if braki_df.empty:
        st.success("Brak braków magazynowych 🎉")
    else:
        st.dataframe(braki_df, use_container_width=True, hide_index=True)

# =========================
# USUWANIE
# =========================
st.header("🗑️ Usuń towar")

if df.empty:
    st.info("Brak towarów do usunięcia")
else:
    towar_do_usuniecia = st.selectbox(
        "Wybierz towar do usunięcia",
        df["towar"].unique()
    )

    if st.button("Usuń towar", type="primary"):
        usun_towar(towar_do_usuniecia)
        st.success(f"🗑️ Usunięto: {towar_do_usuniecia}")
        st.cache_data.clear()
        st.rerun()
