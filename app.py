import os
import math
import time
import requests
import pandas as pd
import streamlit as st
import osmnx as ox
import networkx as nx
from shapely.geometry import Point
try:
    import folium
    from folium import PolyLine, Marker
    FOLIUM_AVAILABLE = True
except Exception:
    folium = None
    PolyLine = None
    Marker = None
    FOLIUM_AVAILABLE = False

from streamlit.components.v1 import html

# -------------------------------
# Config
# -------------------------------
# Hardcoded OpenCage API key (per user request). Replace with your key.
OPENCAGE_KEY = "792b50d494e945bab9442e95fde1d09a"

# Distance threshold (km) used to decide hybrid vs local routing
DISTANCE_THRESHOLD_KM = 150.0

AIRPORTS_CSV = os.path.join(os.path.dirname(__file__), "airports.csv")

# Haversine distance (meters)
def haversine(a, b):
    lat1, lon1 = a
    lat2, lon2 = b
    R = 6371000
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    x = math.sin(dphi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda/2)**2
    return 2 * R * math.asin(math.sqrt(x))

# -------------------------------
# Geocoding (OpenCage) with retries
# -------------------------------
OPENCAGE_KEY = "792b50d494e945bab9442e95fde1d09a"
# Distance threshold (km) used to decide hybrid vs local routing
# removed from UI as requested — keep here as a constant
DISTANCE_THRESHOLD_KM = 150.0

@st.cache_data
def geocode_open_cage(place, key, max_retries=3, pause=1.0):
    """Geocode a place using OpenCage. 'key' must be provided (used in cache key)."""
    if not key:
        raise RuntimeError("OpenCage API key not set. Put it in code or set OPENCAGE_API_KEY env var.")

    url = "https://api.opencagedata.com/geocode/v1/json"
    params = {"q": place, "key": key, "limit": 1}

    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.get(url, params=params, timeout=10)
            # record HTTP status for debugging
            st.session_state.setdefault("geo_logs", []).append(f"HTTP {resp.status_code} for '{place}' (attempt {attempt})")
            resp.raise_for_status()
            data = resp.json()
            # helpful debug info when no results
            if not data.get("results"):
                summary = {
                    "status": data.get("status"),
                    "total_results": data.get("total_results"),
                }
                st.session_state.setdefault("geo_logs", []).append(f"No results for '{place}': {summary}")
                # also add a short preview of the response for debugging
                st.session_state.setdefault("geo_logs", []).append(str(data)[:500])
                return None

            g = data["results"][0]["geometry"]
            return (g["lat"], g["lng"])
        except requests.exceptions.RequestException as e:
            st.session_state.setdefault("geo_logs", []).append(f"Attempt {attempt} failed: {e}")
            time.sleep(pause * attempt)
    return None
def load_airports(csv_path=AIRPORTS_CSV):
    df = pd.read_csv(csv_path)
    # Expect columns: name, city, country, lat, lon
    for c in ["lat", "lon"]:
        if c not in df.columns:
            raise RuntimeError(f"airports.csv missing required column: {c}")
    return df

    current_key = OPENCAGE_KEY
# Find nearest airport
# -------------------------------
@st.cache_data
def find_nearest_airport(coords, airports_df):
    distances = airports_df.apply(lambda r: haversine(coords, (r["lat"], r["lon"])), axis=1)
    idx = distances.idxmin()
    row = airports_df.loc[idx]
    return {"name": row.get("name"), "city": row.get("city"), "lat": row.get("lat"), "lon": row.get("lon"), "dist_m": distances[idx]}

# -------------------------------
# Load road graph between two points
# -------------------------------
@st.cache_resource
def load_road_graph(src_coords, dest_coords):
    center = ((src_coords[0] + dest_coords[0]) / 2, (src_coords[1] + dest_coords[1]) / 2)
    dist_m = haversine(src_coords, dest_coords)
    # radius: at least 2km, or based on distance
    radius = max(int(dist_m * 0.75), 2000)
    G = ox.graph_from_point(center, dist=radius, network_type="drive")
    # modern osmnx versions include 'length' attributes on edges already.
    # If your osmnx version requires explicit addition, replace this line.
    return G

# -------------------------------
# Helper: path node coords
# -------------------------------
def nodes_to_coords(G, path):
    coords = []
    for n in path:
        data = G.nodes[n]
        coords.append((data.get("y"), data.get("x")))
    return coords

# -------------------------------
# UI
# -------------------------------
st.set_page_config(layout="wide", page_title="Hybrid Route Planner")
st.title("🌍 Hybrid Route Planner")

# Show whether API key is available (helps debugging)
if OPENCAGE_KEY:
    st.sidebar.success("OpenCage API key: available (using in-code key)")
else:
    st.sidebar.error("OpenCage API key: missing — please set OPENCAGE_KEY in app.py or use env var.")

with st.sidebar:
    st.header("Controls")
    source = st.text_input("Source (city or address)", "Delhi, India")
    destination = st.text_input("Destination (city or address)", "Noida, India")
    # distance threshold is fixed (not editable in UI)
    distance_threshold_km = DISTANCE_THRESHOLD_KM

    run = st.button("Find Route")

st.markdown("---")

if run:
    st.info("Resolving locations...")
    # determine API key to use (session or env var)
    # use the hardcoded key (per user request)
    current_key = OPENCAGE_KEY

    try:
        src = geocode_open_cage(source, key=current_key)
        dest = geocode_open_cage(destination, key=current_key)
    except RuntimeError as e:
        st.error(str(e))
        st.stop()

    if not src or not dest:
        st.error("Invalid location: could not geocode source or destination. Try a more specific name.")
        logs = st.session_state.get("geo_logs")
        if logs:
            st.write("Geocode logs:")
            for l in logs:
                st.write(l)
        st.stop()

    # compute distance in km
    dist_m = haversine(src, dest)
    dist_km = dist_m / 1000.0

    airports_df = load_airports()

    if dist_km > distance_threshold_km:
        st.success("Long distance detected → using hybrid flight + road model")

        src_air = find_nearest_airport(src, airports_df)
        dest_air = find_nearest_airport(dest, airports_df)

        st.markdown("### ✈️ Hybrid Route Plan")
        st.write(f"🚗 {source} → {src_air['name']} ({src_air['city']}) — {src_air['dist_m']:.0f} m")
        st.write(f"✈️ {src_air['name']} → {dest_air['name']}")
        st.write(f"🚗 {dest_air['name']} → {destination} — {dest_air['dist_m']:.0f} m")

        # Create map (Folium if available, otherwise fallback to st.map)
        mid = ((src[0] + dest[0]) / 2, (src[1] + dest[1]) / 2)
        if FOLIUM_AVAILABLE:
            fmap = folium.Map(location=mid, zoom_start=4)
            Marker(location=src, tooltip="Source", icon=folium.Icon(color="green")).add_to(fmap)
            Marker(location=dest, tooltip="Destination", icon=folium.Icon(color="red")).add_to(fmap)
            # Airport markers
            Marker(location=(src_air['lat'], src_air['lon']), tooltip=f"Src Airport: {src_air['name']}", icon=folium.Icon(color="blue", icon="plane", prefix='fa')).add_to(fmap)
            Marker(location=(dest_air['lat'], dest_air['lon']), tooltip=f"Dst Airport: {dest_air['name']}", icon=folium.Icon(color="blue", icon="plane", prefix='fa')).add_to(fmap)
            # Road segments: straight lines (could be improved with local OSM routing)
            PolyLine(locations=[src, (src_air['lat'], src_air['lon'])], color="orange", weight=4, tooltip="Road to src airport").add_to(fmap)
            PolyLine(locations=[(dest_air['lat'], dest_air['lon']), dest], color="orange", weight=4, tooltip="Road from dest airport").add_to(fmap)
            # Flight leg
            PolyLine(locations=[(src_air['lat'], src_air['lon']), (dest_air['lat'], dest_air['lon'])], color="purple", weight=3, dash_array='10', tooltip="Flight").add_to(fmap)

            st.write("### Map")
            st.components.v1.html(fmap._repr_html_(), height=600)
        else:
            st.warning("Folium is not installed. Showing a simple map fallback. To enable full maps install: `pip install folium` in your app environment.")
            # Fallback: use st.map with key points
            try:
                df_pts = pd.DataFrame([
                    {"lat": src[0], "lon": src[1], "label": "Source"},
                    {"lat": dest[0], "lon": dest[1], "label": "Destination"},
                    {"lat": src_air['lat'], "lon": src_air['lon'], "label": "Src Airport"},
                    {"lat": dest_air['lat'], "lon": dest_air['lon'], "label": "Dst Airport"},
                ])
                st.map(df_pts.rename(columns={"lat": "lat", "lon": "lon"})[["lat", "lon"]])
            except Exception:
                st.write("Coordinates:\n", src, dest, (src_air['lat'], src_air['lon']), (dest_air['lat'], dest_air['lon']))

    else:
        st.info("Short distance detected → using OSM road routing")

        with st.spinner("Loading road graph and computing routes..."):
            G = load_road_graph(src, dest)

            # Project the graph to a metric CRS so nearest_nodes can search efficiently
            # without requiring scikit-learn. We will search on the projected graph
            # but map results using the original (unprojected) graph node coordinates.
            try:
                G_proj = ox.project_graph(G)

                # project the input points to the graph CRS
                src_point = Point(src[1], src[0])
                dest_point = Point(dest[1], dest[0])
                src_proj_geom, _ = ox.projection.project_geometry(src_point, to_crs=G_proj.graph.get('crs'))
                dest_proj_geom, _ = ox.projection.project_geometry(dest_point, to_crs=G_proj.graph.get('crs'))

                orig = ox.distance.nearest_nodes(G_proj, src_proj_geom.x, src_proj_geom.y)
                dst = ox.distance.nearest_nodes(G_proj, dest_proj_geom.x, dest_proj_geom.y)

                # use projected graph for routing (shortest path in meters)
                G_for_routing = G_proj
                G_for_mapping = G
            except Exception as e:
                # Fallback: try nearest_nodes on the unprojected graph (this requires scikit-learn)
                st.warning(f"Projection failed or not supported; attempting unprojected nearest_nodes: {e}")
                orig = ox.distance.nearest_nodes(G, src[1], src[0])
                dst = ox.distance.nearest_nodes(G, dest[1], dest[0])
                G_for_routing = G
                G_for_mapping = G

            # Dijkstra
            t0 = time.time()
            try:
                d_path = nx.shortest_path(G, orig, dst, weight="length")
                t_dijkstra = time.time() - t0
            except Exception as e:
                st.error(f"Error computing Dijkstra path: {e}")
                st.stop()

            # A* (use euclidean heuristic on node coords)
            def heuristic(u, v):
                uy, ux = G.nodes[u]["y"], G.nodes[u]["x"]
                vy, vx = G.nodes[v]["y"], G.nodes[v]["x"]
                return haversine((uy, ux), (vy, vx))

            t1 = time.time()
            try:
                a_path = nx.astar_path(G, orig, dst, heuristic=heuristic, weight="length")
                t_astar = time.time() - t1
            except Exception as e:
                st.error(f"Error computing A* path: {e}")
                st.stop()

        st.write("### Performance")
        st.write(f"Dijkstra time: {t_dijkstra:.4f} s")
        st.write(f"A* time: {t_astar:.4f} s")
        st.success(f"Faster: {'Dijkstra' if t_dijkstra < t_astar else 'A*'}")

        # Convert node paths to lat/lon sequences
        d_coords = nodes_to_coords(G, d_path)
        a_coords = nodes_to_coords(G, a_path)

        # Build map centered (Folium if available, otherwise fallback)
        mid = ((src[0] + dest[0]) / 2, (src[1] + dest[1]) / 2)
        if FOLIUM_AVAILABLE:
            fmap = folium.Map(location=mid, zoom_start=12)
            Marker(location=src, tooltip="Source", icon=folium.Icon(color="green")).add_to(fmap)
            Marker(location=dest, tooltip="Destination", icon=folium.Icon(color="red")).add_to(fmap)
            PolyLine(locations=d_coords, color="blue", weight=4, tooltip="Dijkstra path").add_to(fmap)
            PolyLine(locations=a_coords, color="green", weight=3, tooltip="A* path").add_to(fmap)

            st.write("### Map")
            st.components.v1.html(fmap._repr_html_(), height=600)
        else:
            st.warning("Folium is not installed. Showing a simple map fallback. To enable full maps install: `pip install folium` in your app environment.")
            try:
                df_pts = pd.DataFrame(d_coords)
                df_pts.columns = ["lat", "lon"]
                # show Dijkstra route points
                st.markdown("Dijkstra route coordinates (first/last shown):")
                st.write(df_pts.head())
                st.map(df_pts)
            except Exception:
                st.write("Route coordinates available in variables d_coords and a_coords.")

else:
    st.write("Enter source and destination in the sidebar and click 'Find Route'.")
