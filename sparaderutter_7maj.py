import streamlit as st
import pandas as pd
import openrouteservice
from streamlit_folium import folium_static
import folium
import os
import streamlit.components.v1 as components

# Konfiguration
st.set_page_config(page_title="Tillgänglig Göteborg", page_icon="🗺️", layout="centered")

ORS_API_KEY = "5b3ce3597851110001cf62487ab1e05ef5b94e489695d7a4058f8bcd"
client = openrouteservice.Client(key=ORS_API_KEY)

# Init session state
if "page" not in st.session_state:
    st.session_state.page = "login"
if "saved_routes" not in st.session_state:
    st.session_state.saved_routes = []
if "forum_posts" not in st.session_state:
    st.session_state.forum_posts = []
if "reports" not in st.session_state:
    st.session_state.reports = []

# ----------------- MENY -----------------
def show_menu():
    with st.sidebar:
        st.header("📋 Meny")
        if st.button("🏠 Hem"):
            st.session_state.page = "home"
            st.rerun()
        if st.button("🗺️ Utforska rutter"):
            st.session_state.page = "rutter"
            st.rerun()
        if st.button("🧭 GPS-navigering"):
            st.session_state.page = "gps"
            st.rerun()
        if st.button("💬 Forum"):
            st.session_state.page = "forum"
            st.rerun()
        if st.button("🚧 Rapportera hinder"):
            st.session_state.page = "rapportering"
            st.rerun()
        if st.button("⭐ Sparade rutter"):
            st.session_state.page = "sparade"
            st.rerun()
        if st.button("🚪 Logga ut"):
            st.session_state.clear()
            st.session_state.page = "login"
            st.rerun()

# ----------------- FUNKTIONER -----------------
def geocode_address(address):
    try:
        result = client.pelias_search(text=address, sources=["osm"])
        coords = result['features'][0]['geometry']['coordinates']
        return tuple(coords)
    except Exception as e:
        st.error(f"Geokodning misslyckades: {e}")
        return None

def show_route_map(route_coords, start_coords, end_coords):
    mid_lat = (start_coords[1] + end_coords[1]) / 2
    mid_lon = (start_coords[0] + end_coords[0]) / 2
    m = folium.Map(location=[mid_lat, mid_lon], zoom_start=14)
    folium.PolyLine([(lat, lon) for lon, lat in route_coords], color="blue", weight=6, opacity=0.8).add_to(m)
    folium.Marker([start_coords[1], start_coords[0]], popup="Start").add_to(m)
    folium.Marker([end_coords[1], end_coords[0]], popup="Mål").add_to(m)
    folium_static(m)

def show_gps_map():
    gps_html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <script src="https://cdn.jsdelivr.net/npm/leaflet@1.7.1/dist/leaflet.js"></script>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/leaflet@1.7.1/dist/leaflet.css"/>
        <style>
            #map { height: 600px; }
        </style>
    </head>
    <body>
    <div id="map"></div>
    <script>
        var map = L.map('map').setView([57.7089, 11.9746], 14);

        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19 }).addTo(map);

        function onLocationFound(e) {
            L.marker(e.latlng).addTo(map).bindPopup("Du är här").openPopup();
            map.setView(e.latlng, 17);
        }

        function onLocationError(e) {
            var popup = L.popup().setLatLng(map.getCenter())
                .setContent("❗ Geolocation misslyckades: " + e.message + "<br>Aktivera platsåtkomst i webbläsaren.");
            popup.openOn(map);
        }

        map.on('locationfound', onLocationFound);
        map.on('locationerror', onLocationError);

        map.locate({setView: true, maxZoom: 17, watch: true});
    </script>
    </body>
    </html>
    '''
    components.html(gps_html, height=700, scrolling=False)

# ----------------- LOGIN -----------------
if st.session_state.page == "login":
    st.title("🔑 Logga in")
    email = st.text_input("E-post")
    if st.button("Logga in"):
        if os.path.exists("användarprofiler.csv"):
            df = pd.read_csv("användarprofiler.csv", on_bad_lines='skip')
            match = df[df["E-post"] == email]
            if not match.empty:
                user = match.iloc[0]
                st.session_state.user_info = {
                    "namn": user["Namn"],
                    "email": user["E-post"],
                    "funktionsvariation": user["Funktionsvariation"]
                }
                # Ladda sparade rutter
                if os.path.exists("sparade_rutter.csv"):
                    df_routes = pd.read_csv("sparade_rutter.csv", on_bad_lines='skip')
                    user_routes = df_routes[df_routes["email"] == email].to_dict(orient="records")
                    st.session_state.saved_routes = user_routes
                else:
                    st.session_state.saved_routes = []
                # Ladda forum-inlägg
                if os.path.exists("forum.csv"):
                    df_forum = pd.read_csv("forum.csv", on_bad_lines='skip')
                    user_posts = df_forum[df_forum["email"] == email].to_dict(orient="records")
                    st.session_state.forum_posts = user_posts
                else:
                    st.session_state.forum_posts = []
                # Ladda rapporter
                if os.path.exists("rapporter.csv"):
                    df_reports = pd.read_csv("rapporter.csv", on_bad_lines='skip')
                    user_reports = df_reports[df_reports["email"] == email].to_dict(orient="records")
                    st.session_state.reports = user_reports
                else:
                    st.session_state.reports = []
                st.session_state.page = "home"
                st.rerun()
            else:
                st.error("Fel e-post eller konto finns inte.")
        else:
            st.warning("Inga konton finns ännu. Skapa ett först.")
    if st.button("Skapa nytt konto"):
        st.session_state.page = "signup"
        st.rerun()

# ----------------- SIGN UP -----------------
elif st.session_state.page == "signup":
    st.title("📝 Skapa konto")
    funktionsval = ["Rullstol", "Elrullstol", "Rullator", "Kryckor", "Ingen"]
    namn = st.text_input("Namn")
    email = st.text_input("E-post")
    funktionsvariation = st.selectbox("Typ av funktionsvariation", funktionsval)
    if st.button("Registrera"):
        if namn and email:
            profil_data = {"Namn": namn, "E-post": email, "Funktionsvariation": funktionsvariation}
            if not os.path.exists("användarprofiler.csv"):
                pd.DataFrame([profil_data]).to_csv("användarprofiler.csv", index=False)
            else:
                pd.DataFrame([profil_data]).to_csv("användarprofiler.csv", mode='a', header=False, index=False)
            st.success("Konto skapat! Logga nu in.")
            st.session_state.page = "login"
            st.rerun()
        else:
            st.warning("Fyll i både namn och e-post.")
# ----------------- HOME -----------------
elif st.session_state.page == "home":
    show_menu()
    user_info = st.session_state.user_info
    st.title(f"👋 Välkommen, {user_info['namn']}!")
    st.markdown("Smarta vägar. Färre hinder. Mer frihet.")

# ----------------- GPS -----------------
elif st.session_state.page == "gps":
    show_menu()
    st.title("🧭 GPS-navigering i Göteborg")
    show_gps_map()

# ----------------- RUTTER -----------------
elif st.session_state.page == "rutter":
    show_menu()
    user_info = st.session_state.user_info
    profile_map = {
        "Rullstol": "wheelchair",
        "Elrullstol": "wheelchair",
        "Rullator": "foot-walking",
        "Kryckor": "foot-walking",
        "Ingen": "driving-car"
    }
    ors_profile = profile_map.get(user_info["funktionsvariation"], "driving-car")

    st.title(f"🗺️ Anpassad rutt för {user_info['funktionsvariation']}")
    start_address = st.text_input("Startadress")
    end_address = st.text_input("Slutadress")

    # 💾 Spara-knappen högt upp
    if start_address and end_address:
        if st.button("💾 Spara rutt"):
            route_data = {
                "email": user_info["email"],
                "start": start_address,
                "end": end_address
            }
            st.session_state.saved_routes.append(route_data)
            df_route = pd.DataFrame([route_data])
            if not os.path.exists("sparade_rutter.csv"):
                df_route.to_csv("sparade_rutter.csv", index=False)
            else:
                df_route.to_csv("sparade_rutter.csv", mode="a", header=False, index=False)
            st.success("💾 Rutt sparad!")

    if st.button("Beräkna rutt"):
        start_coords = geocode_address(start_address)
        end_coords = geocode_address(end_address)
        if start_coords and end_coords:
            try:
                route = client.directions(
                    coordinates=[start_coords, end_coords],
                    profile=ors_profile,
                    format='geojson',
                    instructions=True
                )
                route_coords = route['features'][0]['geometry']['coordinates']
                segments = route['features'][0]['properties']['segments']
                show_route_map(route_coords, start_coords, end_coords)
                st.subheader("📝 Steg-för-steg-instruktioner")
                for i, segment in enumerate(segments):
                    st.markdown(f"### Delsträcka {i + 1}")
                    for step in segment['steps']:
                        st.write(f"➡ {step['instruction']}")
                        st.write(f"   • Avstånd: {step['distance']:.0f} meter")
                        st.write(f"   • Tid: {step['duration']/60:.1f} minuter")
                        st.markdown("---")
            except Exception as e:
                st.error(f"Kunde inte hämta rutt: {e}")

# ----------------- SPARADE RUTTER -----------------
elif st.session_state.page == "sparade":
    show_menu()
    st.title("⭐ Sparade rutter")
    if st.session_state.saved_routes:
        for i, r in enumerate(st.session_state.saved_routes):
            col1, col2 = st.columns([4, 1])
            with col1:
                st.write(f"Rutt {i + 1}: Från {r['start']} → Till {r['end']}")
            with col2:
                if st.button(f"🗑️ Ta bort", key=f"delete_{i}"):
                    # Ta bort från session_state
                    st.session_state.saved_routes.pop(i)
                    # Läs in befintlig CSV
                    if os.path.exists("sparade_rutter.csv"):
                        df = pd.read_csv("sparade_rutter.csv", on_bad_lines='skip')
                        # Filtrera bort den rutten som ska tas bort (baserat på e-post, start och end)
                        df = df[~(
                            (df['email'] == r['email']) &
                            (df['start'] == r['start']) &
                            (df['end'] == r['end'])
                        )]
                        # Spara tillbaka till filen
                        df.to_csv("sparade_rutter.csv", index=False)
                    st.success("✅ Rutt borttagen!")
                    st.rerun()
    else:
        st.write("Inga sparade rutter än.")


# ----------------- FORUM -----------------
elif st.session_state.page == "forum":
    show_menu()
    user_info = st.session_state.user_info
    st.title("💬 Forum")
    st.subheader("Tidigare inlägg")
    if st.session_state.forum_posts:
        for post in reversed(st.session_state.forum_posts):
            with st.container():
                st.markdown(f"""
                <div style='border:1px solid #ccc; padding:10px; border-radius:8px; margin-bottom:10px; background-color:#f9f9f9;'>
                    <strong>{post['name']}</strong><br>
                    {post['message']}
                </div>
                """, unsafe_allow_html=True)
    else:
        st.write("Inga inlägg än.")
    name = user_info["namn"]
    message = st.text_area("Din kommentar")
    if st.button("Skicka inlägg"):
        if message.strip():
            post = {
                "email": user_info["email"],
                "name": name,
                "message": message.strip()
            }
            st.session_state.forum_posts.append(post)
            df_post = pd.DataFrame([post])
            if not os.path.exists("forum.csv"):
                df_post.to_csv("forum.csv", index=False)
            else:
                df_post.to_csv("forum.csv", mode="a", header=False, index=False)
            st.success("✅ Inlägg skickat!")
            st.rerun()
        else:
            st.warning("⚠️ Skriv något innan du skickar.")

# ----------------- RAPPORTERING -----------------
elif st.session_state.page == "rapportering":
    show_menu()
    user_info = st.session_state.user_info
    st.title("🚧 Rapportera hinder")
    address = st.text_input("Adress")
    obstacle_type = st.selectbox("Typ av hinder", ["Trasig trottoar", "Snö/is", "Smal passage", "Annat"])
    description = st.text_area("Beskrivning", max_chars=1000)
    image_file = st.file_uploader("Ladda upp en bild", type=["jpg", "jpeg", "png"])
    if st.button("Skicka rapport"):
        if address and obstacle_type and description:
            coords = geocode_address(address)
            if coords:
                report = {
                    "email": user_info["email"],
                    "address": address,
                    "type": obstacle_type,
                    "description": description,
                    "image": image_file.name if image_file else None,
                    "lat": coords[1],
                    "lon": coords[0],
                    "status": "aktiv"
                }
                st.session_state.reports.append(report)
                df_report = pd.DataFrame([report])
                if not os.path.exists("rapporter.csv"):
                    df_report.to_csv("rapporter.csv", index=False)
                else:
                    df_report.to_csv("rapporter.csv", mode="a", header=False, index=False)
                st.success("✅ Rapport inskickad!")
            else:
                st.error("❌ Kunde inte geokoda adressen.")
        else:
            st.warning("⚠️ Fyll i alla fält innan du skickar.")
    st.subheader("📍 Karta över rapporterade hinder")
    map_center = [57.7089, 11.9746]
    m = folium.Map(location=map_center, zoom_start=13)
    for report in st.session_state.reports:
        if report['status'] == "aktiv":
            folium.Marker(
                [report['lat'], report['lon']],
                popup=f"{report['type']}<br>{report['description']}<br>{report['address']}",
                icon=folium.Icon(color="red", icon="exclamation-sign")
            ).add_to(m)
    folium_static(m)
    st.subheader("📄 Tidigare rapporter")
    if st.session_state.reports:
        for i, r in enumerate(reversed(st.session_state.reports)):
            st.write(f"{i+1}. {r['address']} – {r['type']}")
            st.write(f"{r['description']}")
            if r['image']:
                st.write(f"Bild: {r['image']}")
            st.markdown("---")
    else:
        st.write("Inga rapporter ännu.")
