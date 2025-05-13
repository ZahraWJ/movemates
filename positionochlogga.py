import streamlit as st
import pandas as pd
import openrouteservice
from streamlit_folium import folium_static
import folium
import os
import json
import streamlit.components.v1 as components

# ✅ SIDKONFIG (måste ligga allra först)
st.set_page_config(
    page_title="Tillgänglig Göteborg",
    page_icon="🗺️",
    layout="centered"
)

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

def show_map(route_coords, start_coords, end_coords):
    geojson_data = {
        "type": "FeatureCollection",
        "features": [{
            "type": "Feature",
            "geometry": {
                "type": "LineString",
                "coordinates": route_coords
            },
            "properties": {}
        }]
    }
    geojson_str = json.dumps(geojson_data)

    html_code = f'''
    <html>
    <head>
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.3/dist/leaflet.css" />
        <script src="https://unpkg.com/leaflet@1.9.3/dist/leaflet.js"></script>
        <style>#map {{ height: 600px; }}</style>
    </head>
    <body>
    <div id="map"></div>
    <script>
        var map = L.map('map').setView([{start_coords[1]}, {start_coords[0]}], 14);
        L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{ maxZoom: 19 }}).addTo(map);

        var route = {geojson_str};
        L.geoJSON(route, {{
            style: function (feature) {{ return {{color: "blue", weight: 6, opacity: 0.8}}; }}
        }}).addTo(map);

        L.marker([{start_coords[1]}, {start_coords[0]}]).addTo(map).bindPopup("Startpunkt");
        L.marker([{end_coords[1]}, {end_coords[0]}]).addTo(map).bindPopup("Målpunkt");

        function onLocationFound(e) {{
            var radius = e.accuracy;
            L.marker(e.latlng).addTo(map).bindPopup("Du är här").openPopup();
            map.setView(e.latlng, 17);
        }}

        function onLocationError(e) {{
            var popup = L.popup().setLatLng(map.getCenter()).setContent("❗ Geolocation misslyckades: " + e.message);
            popup.openOn(map);
        }}

        map.on('locationfound', onLocationFound);
        map.on('locationerror', onLocationError);
        map.locate({{setView: true, maxZoom: 17, watch: true}});
    </script>
    </body>
    </html>
    '''
    components.html(html_code, height=650)

# ----------------- SID: LOGIN -----------------
if st.session_state.page == "login":
    st.title("🔑 Logga in")
    email = st.text_input("E-post")
    password = st.text_input("Lösenord", type="password")

    if st.button("Logga in"):
        if os.path.exists("användarprofiler.csv"):
            df = pd.read_csv("användarprofiler.csv")
            match = df[(df["E-post"] == email) & (df["Lösenord"] == password)]
            if not match.empty:
                user = match.iloc[0]
                st.session_state.user_info = {
                    "namn": user["Namn"],
                    "email": user["E-post"],
                    "funktionsvariation": user["Funktionsvariation"]
                }
                st.session_state.page = "home"
                st.rerun()
            else:
                st.error("❌ Fel e-post eller lösenord.")
        else:
            st.warning("⚠️ Inga konton finns ännu. Skapa ett först.")

    if st.button("Skapa nytt konto"):
        st.session_state.page = "signup"
        st.rerun()

# ----------------- SID: SKAPA KONTO -----------------
elif st.session_state.page == "signup":
    st.title("📝 Skapa konto")
    funktionsval = ["Rullstol", "Elrullstol", "Rullator", "Kryckor", "Ingen"]
    namn = st.text_input("Namn")
    email = st.text_input("E-post")
    password = st.text_input("Lösenord", type="password")
    funktionsvariation = st.selectbox("Typ av funktionsvariation", funktionsval)
    if st.button("Registrera"):
        if namn and email and password:
            profil_data = {
                "Namn": namn,
                "E-post": email,
                "Funktionsvariation": funktionsvariation,
                "Lösenord": password
            }
            if not os.path.exists("användarprofiler.csv"):
                pd.DataFrame([profil_data]).to_csv("användarprofiler.csv", index=False)
            else:
                pd.DataFrame([profil_data]).to_csv("användarprofiler.csv", mode='a', header=False, index=False)
            st.success("✅ Konto skapat! Logga nu in.")
            st.session_state.page = "login"
            st.rerun()
        else:
            st.warning("⚠️ Fyll i namn, e-post och lösenord.")

# ----------------- SID: HOME -----------------
elif st.session_state.page == "home":
    show_menu()
    user_info = st.session_state.user_info
    st.title(f"👋 Välkommen, {user_info['namn']}!")
    col1, col2 = st.columns([1, 2])
    with col1:
        st.image("https://i.imgur.com/pJxcfyY.jpeg", width=250)
    with col2:
        st.markdown("""
        <h2 style='color: #2a7de1; font-size: 32px; margin-top: 20px;'>
        Smarta vägar<br>Färre hinder<br>Mer frihet
        </h2>""", unsafe_allow_html=True)


# ----------------- SID: RUTTER -----------------
elif st.session_state.page == "rutter":
    show_menu()
    user_info = st.session_state.user_info
    profile_map = {"Rullstol": "wheelchair", "Elrullstol": "wheelchair", "Rullator": "foot-walking", "Kryckor": "foot-walking", "Ingen": "driving-car"}
    ors_profile = profile_map.get(user_info["funktionsvariation"], "driving-car")

    st.title(f"🗺️ Anpassad rutt för {user_info['funktionsvariation']}")
    start_address = st.text_input("Startadress")
    end_address = st.text_input("Slutadress")
    if st.button("Beräkna rutt"):
        start_coords = geocode_address(start_address)
        end_coords = geocode_address(end_address)
        if start_coords and end_coords:
            try:
                route = client.directions(
                    coordinates=[start_coords, end_coords],
                    profile=ors_profile,
                    format='geojson',
                    instructions=True,
                    language='en'
                )
                route_coords = route['features'][0]['geometry']['coordinates']
                segments = route['features'][0]['properties']['segments']
                show_map(route_coords, start_coords, end_coords)
                st.subheader("📝 Steg-för-steg-instruktioner")
                for i, segment in enumerate(segments):
                    st.markdown(f"### Delsträcka {i + 1}")
                    for step in segment['steps']:
                        st.write(f"➡ {step['instruction']}")
                        st.write(f"   • Avstånd: {step['distance']:.0f} meter")
                        st.write(f"   • Tid: {step['duration']/60:.1f} minuter")
                        st.markdown("---")
                if st.button("Spara rutt"):
                    st.session_state.saved_routes.append({"start": start_address, "end": end_address})
                    st.success("💾 Rutt sparad!")
            except Exception as e:
                st.error(f"Kunde inte hämta rutt: {e}")

# ----------------- SID: SPARADE RUTTER -----------------
elif st.session_state.page == "sparade":
    show_menu()
    st.title("⭐ Sparade rutter")
    if st.session_state.saved_routes:
        for i, r in enumerate(st.session_state.saved_routes):
            st.write(f"Rutt {i + 1}: Från {r['start']} → Till {r['end']}")
    else:
        st.write("Inga sparade rutter än.")

# ----------------- SID: FORUM -----------------
elif st.session_state.page == "forum":
    show_menu()
    st.title("💬 Forum")
    st.subheader("Tidigare inlägg")
    if st.session_state.forum_posts:
        for post in reversed(st.session_state.forum_posts):
            with st.container():
                st.markdown(f"""
                <div style='border:2px solid #6c757d; padding:10px; border-radius:8px; margin-bottom:10px; background-color:#f8f9fa;'>
                    <strong>{post['name']}</strong><br>
                    {post['message']}
                </div>
                """, unsafe_allow_html=True)
    else:
        st.write("Inga inlägg än.")

    user_name = st.session_state.user_info['namn']

    with st.form(key="forum_form", clear_on_submit=True):
        message = st.text_area("Din kommentar")
        submitted = st.form_submit_button("Skicka inlägg")

        if submitted:
            if message.strip():
                st.session_state.forum_posts.append({"name": user_name, "message": message.strip()})
                st.success("Inlägg skickat!")
            else:
                st.warning("Skriv något innan du skickar.")

# ----------------- SID: RAPPORTERING -----------------
elif st.session_state.page == "rapportering":
    show_menu()
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
                    "address": address,
                    "type": obstacle_type,
                    "description": description,
                    "image": image_file.name if image_file else None,
                    "lat": coords[1],
                    "lon": coords[0],
                    "status": "aktiv"
                }
                st.session_state.reports.append(report)
                st.success("✅ Tack! Din rapport har skickats in.")
            else:
                st.error("❌ Kunde inte geokoda adressen.")
        else:
            st.warning("⚠️ Fyll i alla fält innan du skickar rapporten.")

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