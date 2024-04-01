import streamlit as st
from streamlit_gsheets import GSheetsConnection
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import pydeck as pdk

st.header("Personal Application Tracker")

# Create a connection object.
conn = st.connection("gsheets", type=GSheetsConnection)

df = conn.read(
    usecols=list(range(10)), # using the first 10 columns
    ttl=5
)

df = df.dropna(how="all") # remove all rows without entries

# alternative: -> usecols in conn.read does not need to be set
# remove empty cols
#df = df.dropna(axis=1, how='all')

# remove empty rows
#df = df.dropna(axis=0, how='all')

# Optional: Ersetzen Sie NaN-Werte in bestimmten Spalten durch einen Standardwert, z.B. einen leeren String
#df.fillna('', inplace=True)


for column in ['ongoing', 'rejection', 'referral']:
    df[column] = df[column].apply(lambda x: True if x == 'x' else False)

st.dataframe(df)

geolocator = Nominatim(user_agent="applicationTrackerGeoCoder")

geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)

# Eindeutige Städte extrahieren
cities = df['City'].unique()

# Koordinaten für Städte ermitteln
locations = {}
for city in cities:
    location = geocode(city + ", Germany")
    if location:
        locations[city] = (location.latitude, location.longitude)

# Anzahl der Nennungen pro Stadt berechnen
city_counts = df['City'].value_counts().reset_index()
city_counts.columns = ['City', 'Count']

# Koordinaten hinzufügen
city_counts['Latitude'] = city_counts['City'].apply(lambda x: locations[x][0] if x in locations else None)
city_counts['Longitude'] = city_counts['City'].apply(lambda x: locations[x][1] if x in locations else None)

#print(city_counts)

# Konfiguration der HeatmapLayer
heatmap_layer = pdk.Layer(
    'HeatmapLayer',
    data=city_counts,
    get_position=['Longitude', 'Latitude'],
    get_weight='Count',
    radius_pixels=60,
    intensity=1,
    threshold=0.05,
    colors=[(193, 39, 45, 0.2), (244, 114, 1, 1), (255, 255, 178, 0.2)],
)

view_state = pdk.ViewState(latitude=50.1109, longitude=10.6840, zoom=5, bearing=0, pitch=0)

st.pydeck_chart(pdk.Deck(layers=[heatmap_layer], initial_view_state=view_state))
