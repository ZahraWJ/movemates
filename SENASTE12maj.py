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

st.markdown("""
    <style>
    html, body, .stApp {
        background-color: #f9fbfd !important;
    }
    h1, h2, h3, p, span, label, div {
        color: #004c99 !important;
    }
    button, button * {
        background-color: #004c99 !important;
        color: white !important;
        border-radius: 5px !important;
        font-size: 16px !important;
        border: none !important;
    }
    button:hover, button:hover * {
        background-color: #0066cc !important;
        color: white !important;
    }
    [data-testid="stSidebar"], .sidebar, .stSidebarContent {
        background-color: #ffffff !important;
        color: #004c99 !important;
    }
    .stTextInput > div > div > input {
        color: #004c99 !important;
        border: 1px solid #004c99 !important;
        background-color: #ffffff !important;
    }
    .stTextArea textarea {
        color: #004c99 !important;
        border: 1px solid #004c99 !important;
        background-color: #ffffff !important;
    }
    [data-testid="stFileUploader"] {
        background-color: #ffffff !important;
        border: 1px solid #004c99 !important;
        border-radius: 5px !important;
        padding: 10px !important;
        color: #004c99 !important;
    }
    [data-testid="stFileUploader"] * {
        background-color: #ffffff !important;
        color: #004c99 !important;
    }
    .info-card {
        border: 1px solid #cce0ff;
        border-radius: 10px;
        padding: 15px;
        background-color: #ffffff !important;
        margin-bottom: 15px;
    }
    .forum-post, .report-card {
        border: 1px solid #d9eaff;
        border-radius: 8px;
        padding: 10px;
        margin-bottom: 10px;
        background-color: #ffffff !important;
    }
    .stSelectbox div[data-baseweb="select"] {
        background-color: #ffffff !important;
        border: 1px solid #004c99 !important;
        border-radius: 5px !important;
    }
    .stSelectbox div[data-baseweb="select"] * {
        color: #004c99 !important;
        background-color: #ffffff !important;
    }
    .stSelectbox .css-1wa3eu0-placeholder,
    .stSelectbox .css-1jqq78o-singleValue,
    .stSelectbox .css-14el2xx-placeholder,
    .stSelectbox .css-1dimb5e-singleValue {
        color: #004c99 !important;
    }
    [data-baseweb="menu"] {
        background-color: #ffffff !important;
        border: 1px solid #004c99 !important;
    }
    li.st-emotion-cache-1v77ucq,
    li.st-emotion-cache-17l5uvc {
        background-color: #ffffff !important;
    }
    li.st-emotion-cache-1v77ucq:hover,
    li.st-emotion-cache-17l5uvc:hover {
        background-color: #e6f0ff !important;
    }
    .st-emotion-cache-qiev7j {
        color: #004c99 !important;
    }
    </style>
""", unsafe_allow_html=True)

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
from geopy.distance import geodesic

GOTEBORG_CENTER = (57.7089, 11.9746)  # Göteborgs centrum
MAX_DISTANCE_FROM_GBG_KM = 50         # Godtagbar radie

def geocode_address(address):
    try:
        result = client.pelias_search(text=address, sources=["osm"])
        if not result['features']:
            return None
        coords = result['features'][0]['geometry']['coordinates']
        latlon = (coords[1], coords[0])
        distance = geodesic(latlon, GOTEBORG_CENTER).km
        if distance > MAX_DISTANCE_FROM_GBG_KM:
            return None  # Utanför Göteborgs närhet
        return tuple(coords)
    except Exception:
        return None

def show_map_with_position(route_coords, start_coords, end_coords):
    if not route_coords or not start_coords or not end_coords:
        return
    import json
    from streamlit.components.v1 import html
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
    html(html_code, height=650)

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
    col1, col2 = st.columns([1, 2])
    with col1:
        st.image("https://i.imgur.com/pJxcfyY.jpeg", width=250)
    with col2:
        st.markdown("""
        <h2 style='color: #2a7de1; font-size: 32px; margin-top: 20px;'>
        Smarta vägar<br>Färre hinder<br>Mer frihet
        </h2>""", unsafe_allow_html=True)
    st.markdown("""
    <div style='text-align: center; font-size: 18px; color: #444; margin-top: 20px;'>
    Gör Göteborg tillgängligt för alla - Vår lösning hjälper dig att hitta framkomliga och funktionsanpassade vägar i Göteborg.<br>
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

    # --- Spara rutt-knapp överst ---
    save_disabled = "last_route" not in st.session_state
    save_clicked = st.button("⭐ Spara senaste rutt", disabled=save_disabled)
    if save_clicked and not save_disabled:
        route_data = st.session_state["last_route"]
        route_file = "sparade_rutter.csv"
        if os.path.exists(route_file):
            df_routes = pd.read_csv(route_file)
            exists = (
                (df_routes["email"] == user_info["email"]) &
                (df_routes["start"] == route_data["start"]) &
                (df_routes["end"] == route_data["end"])
            ).any()
            if not exists:
                df_routes = pd.concat([df_routes, pd.DataFrame([route_data])], ignore_index=True)
                df_routes.to_csv(route_file, index=False)
                st.success("Rutt sparad!")
            else:
                st.info("Denna rutt är redan sparad.")
        else:
            df_routes = pd.DataFrame([route_data])
            df_routes.to_csv(route_file, index=False)
            st.success("Rutt sparad!")

    if st.button("Beräkna rutt"):
        start_coords = geocode_address(start_address)
        end_coords = geocode_address(end_address)
        if not start_coords or not end_coords:
            st.error(
                "❌ En eller båda adresserna kunde inte hittas. Kontrollera stavningen och försök igen.\n"
                "Tips: använd både gatunamn och stad, t.ex. 'Järntorget, Göteborg'."
            )
            st.stop()
        from geopy.distance import geodesic
        distance_km = geodesic((start_coords[1], start_coords[0]), (end_coords[1], end_coords[0])).km
        if distance_km > 6000:
            st.error(
                f"❌ Rutten är {distance_km:.0f} km lång, vilket överskrider tillåten gräns.\n"
                "Kontrollera att adresserna är rätt och inom rimligt avstånd."
            )
            st.stop()
        st.write(f"Startkoord: {start_coords}")
        st.write(f"Slutkoord: {end_coords}")
        try:
            route = client.directions(
                coordinates=[start_coords, end_coords],
                profile=ors_profile,
                format='geojson',
                instructions=True,
                language='en'
            )
            route_coords = route['features'][0]['geometry']['coordinates']
            show_map_with_position(route_coords, start_coords, end_coords)
            # --- Spara senaste rutt i session_state ---
            st.session_state["last_route"] = {
                "email": user_info["email"],
                "start": start_address,
                "end": end_address,
                "route_coords": json.dumps(route_coords)
            }
            # ...resten av koden för instruktioner och analys...

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

            # --- Steg-för-steg-instruktioner sist ---
            st.subheader("📝 Steg-för-steg-instruktioner")
            for step in route['features'][0]['properties']['segments'][0]['steps']:
                st.write(f"➡ {step['instruction']} – {step['distance']:.0f} m ({step['duration']/60:.1f} min)")

        except Exception as e:
            st.exception(e)

    
# SID: SPARADE RUTTER
elif st.session_state.page == "sparade":
    show_menu()
    st.title("⭐ Sparade rutter")

    route_file = "sparade_rutter.csv"
    user_email = st.session_state.user_info["email"]

    # Läs rutter från fil
    if os.path.exists(route_file):
        try:
            df_routes = pd.read_csv(route_file)
            user_routes = df_routes[df_routes["email"] == user_email].to_dict(orient="records")
        except pd.errors.EmptyDataError:
            user_routes = []
    else:
        user_routes = []

    if not user_routes:
        st.info("Inga sparade rutter ännu.")
    else:
        for i, rutt in enumerate(user_routes):
            col1, col2 = st.columns([5, 1])
            with col1:
                st.write(f"📍 Från: {rutt['start']} → Till: {rutt['end']}")
            with col2:
                if st.button("🗑️ Ta bort", key=f"delete_route_{i}"):
                    # Ta bort från DataFrame och spara om
                    df_routes = df_routes[~(
                        (df_routes["email"] == rutt["email"]) &
                        (df_routes["start"] == rutt["start"]) &
                        (df_routes["end"] == rutt["end"])
                    )]
                    df_routes.to_csv(route_file, index=False)
                    st.success("Rutt borttagen!")
                    st.rerun()

   

# SID: FORUM
elif st.session_state.page == "forum":
    show_menu()
    st.title("💬 Forum")
    st.markdown("Skriv en kommentar nedan och se tidigare inlägg.")

    forum_file = "forum.csv"

    # Läs inlägg
    if os.path.exists(forum_file):
        try:
            forum_df = pd.read_csv(forum_file)
            forum_posts = forum_df.to_dict(orient="records")
        except pd.errors.EmptyDataError:
            forum_posts = []
    else:
        forum_posts = []

    user_info = st.session_state.user_info
    user_name = user_info.get("namn", "")
    user_email = user_info.get("email", "")

    # Visa gamla inlägg
    st.subheader("Tidigare inlägg")
    if not forum_posts:
        st.info("Inga inlägg ännu.")
    else:
        for i, post in enumerate(reversed(forum_posts)):
            actual_index = len(forum_posts) - 1 - i  # Räkna baklänges pga reversed()
            col1, col2 = st.columns([5, 1])
            with col1:
                st.markdown(f"""
                    <div style='border:1px solid #ccc; padding:10px; border-radius:8px; margin-bottom:10px; background-color:#f9f9f9;'>
                        <strong>{post.get('Namn', 'Okänd användare')}</strong><br>
                        {post.get('Kommentar', post.get('message', ''))}
                    </div>
                """, unsafe_allow_html=True)
            with col2:
                if post.get("E-post") == user_email:
                    if st.button("Ta bort", key=f"delete_forum_{i}"):
                        forum_posts.pop(actual_index)
                        if forum_posts:
                            pd.DataFrame(forum_posts).to_csv(forum_file, index=False)
                        else:
                            pd.DataFrame(columns=["Namn", "Kommentar", "E-post"]).to_csv(forum_file, index=False)
                        st.success("Inlägg borttaget!")
                        st.rerun()

    # Nytt inlägg
    st.subheader("Lägg till inlägg")
    with st.form("forum_form"):
        kommentar = st.text_area("Din kommentar")
        skickat = st.form_submit_button("Skicka")
        if skickat:
            if kommentar.strip():
                nytt_inlägg = {
                    "Namn": user_name,
                    "Kommentar": kommentar.strip(),
                    "E-post": user_email
                }
                forum_posts.append(nytt_inlägg)
                pd.DataFrame(forum_posts).to_csv(forum_file, index=False)
                st.success("Inlägget har sparats!")
                st.rerun()
            else:
                st.warning("⚠️ Skriv något innan du skickar.")

    # 🔍 MASKININLÄRNING – LUTNINGSKLUSTER (automatisk från geojson om tillgänglig)
    import matplotlib.pyplot as plt
    from sklearn.cluster import KMeans
    import geopandas as gpd
    import numpy as np
    import seaborn as sns
    import warnings
    warnings.filterwarnings("ignore")

    path = "data/gangvagar_majorna.geojson"
    if os.path.exists(path):
        gangvagar = gpd.read_file(path)
        inclines = []

        for incline in gangvagar["incline"]:
            if isinstance(incline, str) and incline.endswith('%'):
                try:
                    inclines.append(float(incline.strip('%')))
                except:
                    continue

        if len(inclines) >= 5:
            st.subheader("🧠 Klustring av gångvägars lutning")
            X = np.array(inclines).reshape(-1, 1)
            kmeans = KMeans(n_clusters=3, random_state=42)
            kmeans.fit(X)
            labels = kmeans.labels_

            cluster_df = pd.DataFrame({
                "Lutning (%)": np.ravel(X),
                "Kluster": labels
            })

            st.markdown(f"Analys baserad på {len(inclines)} gångvägar.")
            for i in sorted(cluster_df["Kluster"].unique()):
                grupp = cluster_df[cluster_df["Kluster"] == i]
                medel = grupp["Lutning (%)"].mean()
                st.write(f"- **Kluster {i}**: {len(grupp)} vägar – medellutning: {medel:.1f}%")

            fig, ax = plt.subplots()
            sns.histplot(data=cluster_df, x="Lutning (%)", hue="Kluster", bins=10, palette="tab10", ax=ax)
            ax.set_title("K-means-klustring av gångvägars lutning")
            st.pyplot(fig)

    # 📈 Enkel lutningsanalys av utvalda vägar
    st.subheader("📈 Lutning på utvalda vägar i Göteborg")

    vagar = [
        {"Väg": "Linnégatan", "Lutning": 2.5},
        {"Väg": "Masthuggsgatan", "Lutning": 8.0},
        {"Väg": "Skånegatan", "Lutning": 1.2},
        {"Väg": "Andra Långgatan", "Lutning": 4.5},
        {"Väg": "Stigbergsliden", "Lutning": 9.8},
        {"Väg": "Kungsgatan", "Lutning": 1.5},
        {"Väg": "Övre Husargatan", "Lutning": 7.1}
    ]

    lutningar = np.array([v["Lutning"] for v in vagar]).reshape(-1, 1)
    kmeans = KMeans(n_clusters=3, random_state=42)
    kmeans.fit(lutningar)
    kluster = kmeans.predict(lutningar)

    kluster_namn = ["Platt", "Medel", "Brant"]
    ordning = np.argsort(kmeans.cluster_centers_.flatten())
    etiketter = [kluster_namn[np.where(ordning == k)[0][0]] for k in kluster]

    for i, etikett in enumerate(etiketter):
        vagar[i]["Kategori"] = etikett

    df = pd.DataFrame(vagar)
    st.dataframe(df[["Väg", "Lutning", "Kategori"]])

    fig, ax = plt.subplots()
    farger = {'Platt': '#66c2a5', 'Medel': '#fc8d62', 'Brant': '#8da0cb'}
    for v in vagar:
        ax.bar(v['Väg'], v['Lutning'], color=farger[v['Kategori']])
    ax.set_ylabel("Lutning (%)")
    ax.set_title("Klustring av utvalda vägar i Göteborg")
    plt.xticks(rotation=45, ha="right")
    st.pyplot(fig)

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
