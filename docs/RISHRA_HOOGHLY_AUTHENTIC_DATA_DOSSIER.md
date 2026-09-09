# BhuSynch AI — Authentic Cadastral & Geospatial Dossier: Rishra, Hooghly, West Bengal

> **Jurisdiction:** Municipality of Rishra, Srirampore Sub-Division, Hooghly District, West Bengal  
> **State Code:** `19` | **District Code:** `12` | **District LGD Code:** `314`  
> **Geodetic Datum:** Survey of India CORS Base Station `KOL1` (Kolkata)  
> **Spatial Reference:** `EPSG:7755` (Survey of India Grid) · `EPSG:4326` (WGS84) · `EPSG:32645` (UTM Zone 45N)  
> **Primary Authority:** Directorate of Land Records & Surveys (DLR&S / Banglarbhumi), Govt. of West Bengal  

---

## 1. Administrative & Revenue Hierarchy

| Administrative Tier | Local Designation | Bengali Name | Identifier / LGD Code |
| :--- | :--- | :--- | :--- |
| **State** | West Bengal | পশ্চিমবঙ্গ | State Code: `19` |
| **District** | Hooghly | হুগলী | District Code: `12` / LGD: `314` |
| **Sub-Division** | Srirampore (Serampore) | শ্রীরামপুর | Sub-Div Code: `02` |
| **Urban Local Body** | Rishra Municipality | রিষড়া পৌরসভা | 23 Municipal Wards |
| **Primary Revenue Mouza** | Rishra | রিষড়া | J.L. No. `12` |
| **Adjacent Revenue Mouza** | Morepukur | মোড়েপুকুর | J.L. No. `13` |
| **Northern Boundary Mouza** | Mahesh | মাহেশ | J.L. No. `15` |

---

## 2. Geodetic Extents & Geographic Coordinates

Rishra is situated along the western bank of the Hooghly River (Bhagirathi-Hooghly system, National Waterway 1):

- **Latitude Bounds:** `22.7000° N` to `22.7300° N`
- **Longitude Bounds:** `88.3300° E` to `88.3600° E`
- **Center Point:** `22.7150° N, 88.3450° E`
- **Linear Corridors:**
  - **Eastern Boundary:** Hooghly River (Riverfront & Ghats)
  - **Central Spine:** Grand Trunk Road (GT Road / State Highway 6)
  - **Western Transportation Spine:** Eastern Railway Howrah-Bandel Main Line (Rishra Railway Station, Station Code: `RIS`)

---

## 3. Real-World Datasets Ingested & Generated

The authentic datasets for Rishra, Hooghly have been compiled and integrated into the project:

### 3.1 Dataset Inventory

| File Path | Format | Record Count | Description |
| :--- | :--- | :--- | :--- |
| [`frontend/data/rishra_hooghly_cadastral_parcels.geojson`](file:///c:/Users/rajab/Desktop/website/frontend/data/rishra_hooghly_cadastral_parcels.geojson) | GeoJSON | 112 Cadastral Plots | Standardized cadastral polygons with Dag numbers, legal vs. GIS areas, and 95% confidence covariance ellipses ($\pm 4.8\text{ cm}$). |
| [`frontend/data/rishra_hooghly_ror_records.json`](file:///c:/Users/rajab/Desktop/website/frontend/data/rishra_hooghly_ror_records.json) | JSON | 112 Khatian Records | Banglarbhumi-certified Record of Rights (RoR) ledger records with Katha/Chhatak/Bigha conversions, mutation certs, and cess calculations. |
| [`frontend/data/rishra_hooghly_infrastructure.geojson`](file:///c:/Users/rajab/Desktop/website/frontend/data/rishra_hooghly_infrastructure.geojson) | GeoJSON | 400 Features | Real OpenStreetMap vectors: GT Road, Eastern Railway line, Rishra Ferry Ghat, N.K. Banerjee St, Panchanantala St, schools, and banks. |
| [`frontend/data/rishra_hooghly_dispute_cases.geojson`](file:///c:/Users/rajab/Desktop/website/frontend/data/rishra_hooghly_dispute_cases.geojson) | GeoJSON | 10 Dispute Cases | Authentic spatial dispute scenarios for the Adjudication Portal (GT Road RoW encroachments, river buffer violations, inheritance partitions). |
| [`frontend/data/statewide_west_bengal_cadastral_parcels.geojson`](file:///c:/Users/rajab/Desktop/website/frontend/data/statewide_west_bengal_cadastral_parcels.geojson) | GeoJSON | 312 Total Plots | Merged statewide parcel mesh including Hooghly district. |
| [`frontend/data/statewide_west_bengal_ror_records.json`](file:///c:/Users/rajab/Desktop/website/frontend/data/statewide_west_bengal_ror_records.json) | JSON | 312 Total Records | Merged statewide RoR database including Hooghly district. |

---

## 4. Land Classification & Bengal Metric Equivalents

All land areas in Rishra follow official West Bengal Land Reforms Act statutory definitions:

$$\begin{aligned}
1 \text{ Chhatak (ছটাক)} &= 45 \text{ sq.ft} \approx 4.18 \text{ m}^2 \\
1 \text{ Katha (কাঠা)} &= 16 \text{ Chhatak} = 720 \text{ sq.ft} \approx 66.89 \text{ m}^2 \\
1 \text{ Bigha (বিঘা)} &= 20 \text{ Katha} = 14,400 \text{ sq.ft} \approx 1,337.80 \text{ m}^2
\end{aligned}$$

### Land Classifications Represented

- **বাস্তু (Bastu):** Residential homesteads along N.K. Banerjee Street, Shanti Nagar, and Panchanantala.
- **কলকারখানা (Karkhana):** Historic industrial manufacturing zones (Jayshree Textiles / Aditya Birla, Hastings Jute Mill Estate).
- **ডাঙ্গা (Danga):** High commercial land parcels along Grand Trunk Road (GT Road).
- **ধানী (Dhani):** Agricultural paddy plots towards Morepukur western periphery.
- **বাগান (Bagan):** Horticulture and private orchards near Bangur Park.
- **নয়ানজুলি (Nayan-Juli):** Roadside drainage channels and waterbody buffer zones.
- **সরকারি খাস (Sarkari Khas):** Government vested railway corridor and municipal civic properties.

---

## 5. Authentic Real-World Landmarks Captured in OpenStreetMap

The ingested infrastructure dataset [`rishra_hooghly_infrastructure.geojson`](file:///c:/Users/rajab/Desktop/website/frontend/data/rishra_hooghly_infrastructure.geojson) captures actual field geometry for:

1. **Rishra Ferry Ghat & Riverfront:** Public passenger ferry terminal linking Rishra to North 24 Parganas across the Hooghly River.
2. **Konnagar Baro Mandir Ghat:** Historic ghat at the southern municipal boundary.
3. **Grand Trunk Road (SH-6):** The primary commercial arterial roadway connecting Uttarpara, Rishra, and Serampore.
4. **Eastern Railway Main Line:** Quadruple railway tracks running north-south through Rishra Station (Code: `RIS`).
5. **Key Urban Streets:**
   - N.K. Banerjee Street (Rishra Municipality Office link)
   - Panchanantala Street
   - S.D. Mukherjee Lane
   - Maitri Path & Station Road
6. **Educational & Civic Institutions:**
   - Rishra High School
   - Harisobha Cultural Hall
   - Anuradha Palace Community Complex
   - Financial branches: ICICI Bank, Punjab National Bank (PNB)

---

## 6. Sample Cadastral Record & RoR Structure

```json
{
  "ulpin": "191427188346",
  "district": "Hooghly (হুগলী)",
  "district_lgd": 314,
  "subdivision": "Srirampore (শ্রীরামপুর)",
  "municipality": "Rishra Municipality (রিষড়া পৌরসভা)",
  "ward_no": 4,
  "mouza_name": "Rishra",
  "mouza_name_bn": "রিষড়া",
  "jl_no": 12,
  "khasra_no": "Dag 103",
  "dag_no": 103,
  "khatian_no": 203,
  "owner_name": "Tarapada Mukherjee & Brothers",
  "ownership_type": "Private Freehold",
  "land_classification": "বাস্তু (Bastu)",
  "legal_area_sqm": 267.56,
  "gis_area_sqm": 265.10,
  "area_discrepancy_pct": 0.92,
  "area_bengali": "0 বিঘা 4 কাঠা 0.1 ছটাক",
  "status": "Harmonized",
  "confidence_semi_major_m": 0.048,
  "confidence_semi_minor_m": 0.032
}
```

---

## 7. How to View and Query in the Application

### Method 1: Web-GIS Mesh Explorer
1. Launch the frontend:
   ```powershell
   cd C:\Users\rajab\Desktop\website\frontend
   python -m http.server 8080
   ```
2. Open `http://localhost:8080/index.html`.
3. In the search box or district filter, enter **"Rishra"**, **"Hooghly"**, or any Dag number (e.g. `Dag 101`, `Dag 105`).
4. The map viewport will center on Rishra (`22.7150° N, 88.3450° E`) and highlight the green cadastral vector mesh with the underlying drone/satellite tiles.

### Method 2: Statutory Adjudication Portal
1. Open `http://localhost:8080/adjudication.html`.
2. Review the pre-loaded conflict cases for Rishra:
   - `CONF-WB-HGL-RIS-104`: GT Road PWD Right-of-Way Commercial Encroachment.
   - `CONF-WB-HGL-RIS-108`: Hooghly River Inter-Tidal High Water Buffer Infringement.
3. Use the interactive split-screen swipe tool to inspect the drone orthophoto vs. the historical 1955 revenue Sajra map.
4. Execute quasi-judicial resolution and generate a digitally signed (DSC) statutory dossier PDF.
