import streamlit as st
import pandas as pd
import os

# Sidinställning
st.set_page_config(page_title="Forum", page_icon="💬")

st.title("Forum")
st.markdown("Skriv en kommentar nedan och se tidigare inlägg.")

# Fil där inlägg sparas
forum_file = "forum.csv"

# Läs gamla inlägg eller skapa tom DataFrame
if os.path.exists(forum_file):
    forum_df = pd.read_csv(forum_file)
else:
    forum_df = pd.DataFrame(columns=["Namn", "Kommentar"])

# Visa tidigare inlägg
st.subheader("Tidigare inlägg")
if forum_df.empty:
    st.info("Inga inlägg ännu.")
else:
    for i, row in forum_df.iterrows():
        st.markdown(f"""
        <div style='border: 1px solid #ddd; border-radius: 8px; padding: 10px; margin-bottom: 10px; background-color: #f9f9f9;'>
            <strong>{row['Namn']}</strong><br>
            {row['Kommentar']}
        </div>
        """, unsafe_allow_html=True)

# Formulär
st.subheader("Lägg till inlägg")
with st.form("forum_form"):
    namn = st.text_input("Ditt namn")
    kommentar = st.text_area("Din kommentar")
    skicka = st.form_submit_button("Skicka")

    if skicka:
        if namn and kommentar:
            ny_rad = pd.DataFrame([{"Namn": namn, "Kommentar": kommentar.strip()}])
            ny_rad.to_csv(forum_file, mode="a", header=not os.path.exists(forum_file), index=False)
            st.success("✅ Inlägget har sparats! Ladda om sidan för att se det.")
        else:
            st.warning("⚠️ Fyll i både namn och kommentar.")
