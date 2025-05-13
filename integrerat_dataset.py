import streamlit as st
import pandas as pd
import openrouteservice
from streamlit_folium import folium_static
import folium
import os
import json
import streamlit.components.v1 as components

# ✅ SIDKONFIG
st.set_page_config( 
    page_title="Tillgänglig Göteborg",
    page_icon="🗺️",
    layout="centered"
)

# 📊 Dataset-analys för Majorna-Linné
with st.sidebar.expander("📊 Dataset-analys: Majorna-Linné"):
    data_path = "data/gangvagar_majorna.geojson"
    if os.path.exists(data_path):
        with open(data_path, encoding='utf-8') as f:
            data = json.load(f)
        features = data.get("features", [])
        st.write(f"Antal gångvägar: {len(features)}")

        material_count = {}
        inclines = []

        for feat in features:
            props = feat.get("properties", {})
            surface = props.get("surface", "Okänt")
            material_count[surface] = material_count.get(surface, 0) + 1

            incline = props.get("incline")
            if incline:
                try:
                    if incline.endswith("%"):
                        inclines.append(float(incline.strip('%')))
                except:
                    pass

        st.write("### Ytmaterial:")
        total = sum(material_count.values())
        for mat, count in material_count.items():
            st.write(f"- {mat}: {count} gångvägar ({(count/total)*100:.1f}%)")

        if inclines:
            inclines_sorted = sorted(inclines, reverse=True)[:5]
            st.write("### Top 5 brantaste gångvägar (procent):")
            for i, inc in enumerate(inclines_sorted, 1):
                st.write(f"{i}. {inc}%")
        else:
            st.write("Ingen lutningsdata tillgänglig i datasetet.")
    else:
        st.warning("Datasetet saknas. Lägg filen i data/gangvagar_majorna.geojson.")

# API och session state
ORS_API_KEY = "5b3ce3597851110001cf62487ab1e05ef5b94e489695d7a4058f8bcd"
client = openrouteservice.Client(key=ORS_API_KEY)

if "page" not in st.session_state:
    st.session_state.page = "login"
if "saved_routes" not in st.session_state:
    st.session_state.saved_routes = []
if "forum_posts" not in st.session_state:
    st.session_state.forum_posts = []
if "reports" not in st.session_state:
    st.session_state.reports = []

# Meny
def show_menu():
    with st.sidebar:
        st.header("📋 Meny")
        buttons = [
            ("🏠 Hem", "home"),
            ("🗺️ Utforska rutter", "rutter"),
            ("🧭 GPS-navigering", "gps"),
            ("💬 Forum", "forum"),
            ("🚧 Rapportera hinder", "rapportering"),
            ("⭐ Sparade rutter", "sparade"),
            ("🚪 Logga ut", "login")
        ]
        for label, page in buttons:
            if st.button(label):
                if page == "login":
                    st.session_state.clear()
                st.session_state.page = page
                st.rerun()

# Funktioner
def geocode_address(address):
    try:
        result = client.pelias_search(text=address, sources=["osm"])
        coords = result['features'][0]['geometry']['coordinates']
        return tuple(coords)
    except Exception as e:
        st.error(f"Geokodning misslyckades: {e}")
        return None

def show_route_map(route_coords, start_coords, end_coords):
    m = folium.Map(location=[(start_coords[1] + end_coords[1]) / 2, (start_coords[0] + end_coords[0]) / 2], zoom_start=14)
    folium.PolyLine(
        [(lat, lon) for lon, lat in route_coords],
        color="blue", weight=6, opacity=0.8
    ).add_to(m)
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
        <style>#map { height: 600px; }</style>
    </head>
    <body>
    <div id="map"></div>
    <script>
        var map = L.map('map').setView([57.7089, 11.9746], 14);

        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            maxZoom: 19
        }).addTo(map);

        function onLocationFound(e) {
            L.marker(e.latlng).addTo(map).bindPopup("Du är här").openPopup();
            map.setView(e.latlng, 17);
        }

        function onLocationError(e) {
            var popup = L.popup()
                .setLatLng(map.getCenter())
                .setContent("❗ Geolocation misslyckades: " + e.message + "<br>Om du inte har gett platsåtkomst, testa att aktivera det i webbläsaren.");
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

# SID: LOGIN
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

# SID: SKAPA KONTO
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

# SID: HOME
elif st.session_state.page == "home":
    show_menu()
    user_info = st.session_state.user_info
    st.title(f"👋 Välkommen, {user_info['namn']}!")
    
    # Välkomstmeddelande och bild
    col1, col2 = st.columns([1, 2])
    with col1:
        st.image("https://i.imgur.com/pJxcfyY.jpeg", width=250)
    with col2:
        st.markdown("""
        <h2 style='color: #2a7de1; font-size: 32px; margin-top: 20px;'>
        Smarta vägar<br>Färre hinder<br>Mer frihet
        </h2>""", unsafe_allow_html=True)
    
    # Beskrivande text
    st.markdown("""
    <div style='text-align: center; font-size: 18px; color: #444; margin-top: 20px;'>
    Gör Göteborg tillgängligt för alla - Vår hemsida hjälper dig att hitta framkomliga och rullstolsanpassade vägar i Göteborg.<br>
    Vi vill minska osäkerheten och göra staden mer tillgänglig, en gata i taget. För dig som vill röra dig fritt, utan att behöva oroa dig för snö, trappor eller kullersten.
    </div>
    """, unsafe_allow_html=True)

# SID: RUTTER
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

    if st.button("Beräkna rutt"):
        start_coords = geocode_address(start_address)
        end_coords = geocode_address(end_address)

        st.write(f"Startkoord: {start_coords}")
        st.write(f"Slutkoord: {end_coords}")

        if start_coords is None or end_coords is None:
            st.error("❌ Adresser kunde inte hittas. Kontrollera stavning och försök igen.")
            st.stop()

        try:
            route = client.directions(
                coordinates=[start_coords, end_coords],
                profile=ors_profile,
                format='geojson',
                instructions=True,
                language='en'
            )
            route_coords = route['features'][0]['geometry']['coordinates']
            show_route_map(route_coords, start_coords, end_coords)

            st.subheader("📝 Steg-för-steg-instruktioner")
            for step in route['features'][0]['properties']['segments'][0]['steps']:
                st.write(f"➡ {step['instruction']} – {step['distance']:.0f} m ({step['duration']/60:.1f} min)")

            # 🔎 Gångvägsanalys
            import geopandas as gpd
            from shapely.geometry import LineString

            route_line = LineString([(lon, lat) for lon, lat in route_coords])
            dataset_path = "data/gangvagar_majorna.geojson"

            if not os.path.exists(dataset_path):
                st.warning("Dataset saknas i 'data/gangvagar_majorna.geojson'")
                st.stop()

            gangvagar = gpd.read_file(dataset_path)
            route_buffer = route_line.buffer(0.0001)
            match = gangvagar[gangvagar.geometry.intersects(route_buffer)]

            if match.empty:
                st.info("Inga gångvägar från datasetet matchar denna rutt.")
                st.stop()

            total_length = sum(geom.length * 111320 for geom in match.geometry if geom)
            risk_length = sum(
                row.geometry.length * 111320
                for idx, row in match.iterrows()
                if isinstance(row.get('surface'), str) and row.get('surface').lower() in ['sett', 'paving_stones', 'cobblestone', 'gravel'] and row.geometry
            )
            risk_percent = (risk_length / total_length) * 100 if total_length else 0

            st.subheader("🔎 Analys av gångvägar")
            ytmaterial = match['surface'].value_counts()
            for mat, count in ytmaterial.items():
                st.write(f"- {mat}: {count} segment ({(count / len(match)) * 100:.1f}%)")

            st.write(f"**Riskavsnitt:** {risk_length:.0f} m ({risk_percent:.1f}%) av rutten.")

            inclines = [float(row.get('incline').strip('%')) for idx, row in match.iterrows() if row.get('incline') and row.get('incline').endswith('%')]
            max_incline = max(inclines) if inclines else 0

            st.write(f"**Max lutning:** {max_incline}%")
            if max_incline >= 6:
                st.warning("⚠️ Brant lutning >6% kan vara svårt för rullstol.")

            # 🤖 ML-analys
            import joblib
            model_data = joblib.load("ml_modell.pkl")
            model = model_data['model']
            label_map = model_data['label_map']
            
            # Prepare input data
            input_data = [[max_incline, risk_percent, total_length]]
            prediction_numeric = model.predict(input_data)[0]
            
            # Convert numeric prediction back to label
            reverse_label_map = {v: k for k, v in label_map.items()}
            prediction = reverse_label_map[prediction_numeric]
            
            st.subheader("🤖 Maskininlärningsanalys:")
            
            # Get feature importances
            feature_importances = model.feature_importances_
            features = ["Max lutning", "Riskprocent", "Total längd"]
            
            # Create a DataFrame for feature importances
            importance_df = pd.DataFrame({
                'Feature': features,
                'Importance': feature_importances
            }).sort_values('Importance', ascending=False)
            
            # Display feature importances
            st.write("**Viktigaste faktorer för bedömningen:**")
            for _, row in importance_df.iterrows():
                st.write(f"- {row['Feature']}: {row['Importance']:.1%}")
            
            # Display prediction with appropriate styling
            if prediction == "svår":
                st.error("❗ Rutten bedöms som SVÅR – välj annan väg om möjligt.")
                st.write("""
                **Anledningar:**
                - Hög lutning eller riskprocent
                - Lång sträcka med svårframkomligt underlag
                - Kombination av utmanande faktorer
                """)
            elif prediction == "medel":
                st.warning("🔶 Rutten bedöms som MEDEL – viss försiktighet behövs.")
                st.write("""
                **Tips:**
                - Kontrollera väderförhållanden
                - Planera för eventuella pauser
                - Var extra uppmärksam på svåra sektioner
                """)
            else:
                st.success("✅ Rutten bedöms som LÄTT – god tillgänglighet.")
                st.write("""
                **Fördelar:**
                - Låg lutning
                - Bra underlag
                - Hanterbar längd
                """)

        except Exception as e:
            st.exception(e)

    
# SID: GPS
elif st.session_state.page == "gps":
    show_menu()
    st.title("🧭 GPS-navigering i Göteborg")
    show_gps_map()

# SID: SPARADE RUTTER
elif st.session_state.page == "sparade":
    show_menu()
    st.title("⭐ Sparade rutter")
    if st.session_state.saved_routes:
        for i, r in enumerate(st.session_state.saved_routes):
            st.write(f"Rutt {i + 1}: Från {r['start']} → Till {r['end']}")
    else:
        st.write("Inga sparade rutter än.")

# SID: FORUM
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
                st.success("✅ Inlägg skickat!")
            else:
                st.warning("⚠️ Skriv något innan du skickar.")

# SID: RAPPORTERING
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
