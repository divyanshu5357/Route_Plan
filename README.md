# 🌍 Hybrid Route Planner

A **Streamlit web application** that computes optimal routes between two locations using a hybrid model combining **road navigation** and **flight paths**.

## 📋 Table of Contents
- [Overview](#overview)
- [Features](#features)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [How It Works](#how-it-works)
- [Requirements](#requirements)
- [Troubleshooting](#troubleshooting)

## 📖 Overview

This application intelligently determines the best route between two locations by:
- **Short distances (<150km):** Uses road-based routing with OSM data and compares two pathfinding algorithms
- **Long distances (>150km):** Recommends a hybrid plan using the nearest airports and connects them with road routes

The app provides interactive map visualizations, performance comparisons between routing algorithms, and supports both local and international route planning.

## ✨ Features

### Core Routing Features
- 🗺️ **Dual Routing Models:**
  - Short-distance: OSM-based road routing with Dijkstra and A* algorithms
  - Long-distance: Hybrid route (road → flight → road) with nearest airport detection

- 📍 **Intelligent Geocoding:**
  - OpenCage API integration for flexible location input
  - Converts city names, addresses, and landmarks to coordinates
  - Retry logic with automatic error handling

- 🛫 **Dynamic Airport Database:**
  - Loads airports from `airports.csv` (no hardcoded data)
  - Finds nearest airports to source and destination automatically
  - Extensible with additional airport data

- ⚡ **Algorithm Performance Analysis:**
  - Dijkstra's algorithm implementation
  - A* search with haversine heuristic
  - Timing comparison for both algorithms
  - Detailed performance metrics

- 🗺️ **Interactive Visualization:**
  - Folium-based map rendering with markers and paths
  - Color-coded route types (orange for roads, purple for flights, multi-color for algorithm comparison)
  - Zoom controls and tooltip information
  - Fallback to Streamlit maps if Folium unavailable

### User Experience
- Clean, intuitive sidebar controls
- Real-time geocoding logs for debugging
- Comprehensive error messages and validation
- Responsive design for desktop and mobile

## 🛠️ Technology Stack

| Component | Technology |
|-----------|-----------|
| **Framework** | Streamlit |
| **Routing Engine** | OSMnx + NetworkX |
| **Geocoding** | OpenCage API |
| **Mapping** | Folium |
| **Graph Processing** | NetworkX (Dijkstra, A*) |
| **Data Handling** | Pandas |
| **Distance Calculation** | Shapely, Haversine Formula |

## 📁 Project Structure

```
HybridRoutePlanner/
├── app.py                 # Main Streamlit application
├── airports.csv           # Airport database (name, city, country, lat, lon)
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables (OpenCage API key, thresholds)
├── README.md              # This file
└── cache/                 # Streamlit cache directory
```

## 🚀 Installation

### Prerequisites
- Python 3.8 or higher
- macOS, Linux, or Windows
- Internet connection (for API calls and map data)

### Step 1: Clone the Repository
```bash
git clone https://github.com/divyanshu5357/Route_Plan.git
cd Route_Plan
```

### Step 2: Create a Virtual Environment (Recommended)
```bash
# macOS/Linux
python3 -m venv .venv
source .venv/bin/activate

# Windows
python -m venv .venv
.venv\Scripts\activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

## ⚙️ Configuration

### 1. Set Up OpenCage API Key

**Option A: Using .env File (Recommended)**
1. Open `.env` file in the project root
2. Replace the placeholder with your actual OpenCage API key:
```env
OPENCAGE_API_KEY=your_actual_api_key_here
```

**Option B: Using Environment Variables**
```bash
# macOS/Linux
export OPENCAGE_API_KEY="your_api_key_here"

# Windows PowerShell
$env:OPENCAGE_API_KEY="your_api_key_here"
```

**Get Your API Key:**
1. Visit [OpenCage Geocoding](https://opencagedata.com/)
2. Sign up for a free account (includes 2,500 free requests/day)
3. Copy your API key from the dashboard

### 2. Configure Distance Threshold
Edit `.env` to adjust when hybrid routing is used:
```env
DISTANCE_THRESHOLD_KM=150.0  # Routes > 150km use flights
```

## 📖 Usage

### Running the Application
```bash
streamlit run app.py
```

The app will open at `http://localhost:8501`

### Basic Workflow
1. **Enter Source Location:** e.g., "Delhi, India" or "New York"
2. **Enter Destination Location:** e.g., "Mumbai, India" or "Los Angeles"
3. **Click "Find Route"** to compute and visualize the route
4. **Review Results:**
   - Interactive map with markers and paths
   - For short routes: Performance metrics comparing Dijkstra vs A*
   - For long routes: Hybrid route plan with nearest airports

### Example Scenarios

**Short Distance (Road Only)**
- Source: Delhi, India
- Destination: Noida, India
- Result: Dijkstra and A* comparison on OSM road network

**Long Distance (Hybrid)**
- Source: Delhi, India
- Destination: Tokyo, Japan
- Result: Nearest airports identified, hybrid route shown

## 🔄 How It Works

### Short Distance Routing (< 150 km)

1. **Geocoding:** Converts input locations to lat/lon using OpenCage
2. **Graph Loading:** Downloads OSM road network using OSMnx
3. **Algorithm Execution:**
   - Dijkstra: Traditional shortest-path algorithm
   - A*: Heuristic-based search using haversine distance
4. **Comparison:** Displays timing and optimal path
5. **Visualization:** Renders both routes on Folium map

### Long Distance Routing (> 150 km)

1. **Geocoding:** Converts source and destination to coordinates
2. **Airport Detection:** Finds nearest major airports to both locations
3. **Route Plan:** Suggests:
   - Road from source → nearest airport
   - Flight between airports
   - Road from destination airport → final destination
4. **Visualization:** Shows route segments with color coding

### Haversine Distance Formula

The haversine formula calculates the great-circle distance between two points on Earth:

```
d = 2R * arcsin(sqrt(sin²(Δφ/2) + cos(φ₁) * cos(φ₂) * sin²(Δλ/2)))
```

Where:
- R = Earth radius (6,371 km)
- φ₁, φ₂ = latitude coordinates
- Δφ, Δλ = differences in latitude/longitude

## 📦 Requirements

```
streamlit>=1.0.0
requests>=2.25.0
pandas>=1.2.0
osmnx>=1.1.0
networkx>=2.5
folium>=0.12.0
certifi>=2020.12.16
shapely>=1.7.0
```

## 🐛 Troubleshooting

### OpenCage API Errors
**Issue:** "OpenCage API key not set"
- **Solution:** Ensure `.env` file exists with valid API key or set `OPENCAGE_API_KEY` environment variable

### SSL Certificate Errors (macOS)
**Issue:** SSL certificate verification failed
- **Solution:** Run `/Applications/Python\ 3.x/Install\ Certificates.command` or reinstall certifi:
```bash
pip install --upgrade certifi
```

### OSMnx Graph Loading Fails
**Issue:** "Failed to get network graph"
- **Solution:** 
  - Check internet connection
  - Verify source/destination are real locations
  - Try with more specific location names (e.g., "Delhi, India" instead of "Delhi")

### Folium Map Not Displaying
**Issue:** Map shows warning about Folium not installed
- **Solution:** 
```bash
pip install folium
```

### Performance Issues
**Issue:** App is slow to respond
- **Solution:**
  - Streamlit caches results; restart browser cache if needed
  - Ensure internet connection is stable
  - Check OpenCage API rate limits (free tier: 2,500 requests/day)

## 📝 Notes

- The `airports.csv` contains a sample of major global airports. You can:
  - Expand with more airports from publicly available datasets
  - Filter by region for local-focused routing
  - Add custom airports for specific use cases

- The distance threshold (150 km) is configurable in `.env` based on your routing preferences

- Caching is enabled for geocoding and graph loading to improve performance on repeated queries

## 🤝 Contributing

Contributions are welcome! Feel free to:
- Report bugs or issues
- Suggest feature improvements
- Submit pull requests

## 📄 License

This project is open source and available under the MIT License.

## 📧 Contact

For questions or suggestions, please open an issue on the GitHub repository.

---

**Last Updated:** April 2026
**Version:** 1.0.0
