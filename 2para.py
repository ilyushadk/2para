import streamlit as st
import pandas as pd
from datetime import date

st.set_page_config(page_title="Prosty Magazyn", layout="centered")

st.title("📦 Prosty Magazyn")

# Inicjalizacja danych w sesji
if "magazyn" not in st.session_state:
    st.session_state.magazyn = pd.DataFrame(
        columns=[
            "Towar",
            "Stan aktualny",
            "Stan docelowy",
            "Braki",
            "Cena (zł)",
            "Data"
        ]
    )

# =========================
# Dodawanie / aktualizacja
# =========================
st.header("➕ Dodaj / zaktualizuj towar")

with st.form("formularz"):
    towar = st.text_input("Nazwa towaru")
    stan_aktualny = st.number_input("Stan aktualny", min_value=0, step=1)
    stan_docelowy = st.number_input("Stan docelowy", min_value=0, step=1)
    cena = st.number_input("Cena (zł)", min_value=0.0, step=0.01, format="%.2f")
    data = st.date_input("Data", value=date.today())
    submitted = st.form_submit_button("Zapisz")

    if submitted and towar:
        braki = max(stan_docelowy - stan_aktualny, 0)

        # Usuwamy istniejący towar (jeśli był)
        st.session_state.magazyn = st.session_state.magazyn[
            st.session_state.magazyn["Towar"] != towar
        ]

        # Dodajemy nowy wiersz
        nowy = pd.DataFrame(
            [[
                towar,
                stan_aktualny,
                stan_docelowy,
                braki,
                cena,
                data
            ]],
            columns=st.session_state.magazyn.columns
        )

        st.session_state.magazyn = pd.concat(
            [st.session_state.magazyn, nowy],
            ignore_index=True
        )

        st.success("Towar zapisany")

# =========================
# Wyświetlanie magazynu
# =========================
st.header("📋 Stan magazynu")

if st.session_state.magazyn.empty:
    st.info("Brak danych w magazynie")
else:
    st.dataframe(st.session_state.magazyn, use_container_width=True)

    # Towary z brakami
    st.subheader("❗ Towary z brakami")
    braki_df = st.session_state.magazyn[
        st.session_state.magazyn["Braki"] > 0
    ]

    if braki_df.empty:
        st.success("Brak braków magazynowych 🎉")
    else:
        st.dataframe(braki_df, use_container_width=True)

# =========================
# Usuwanie towaru
# =========================
st.header("🗑️ Usuń towar")

if st.session_state.magazyn.empty:
    st.info("Brak towarów do usunięcia")
else:
    towar_do_usuniecia = st.selectbox(
        "Wybierz towar do usunięcia",
        st.session_state.magazyn["Towar"]
    )

    if st.button("Usuń towar"):
        st.session_state.magazyn = st.session_state.magazyn[
            st.session_state.magazyn["Towar"] != towar_do_usuniecia
        ]
        st.success(f"Usunięto towar: {towar_do_usuniecia}")
