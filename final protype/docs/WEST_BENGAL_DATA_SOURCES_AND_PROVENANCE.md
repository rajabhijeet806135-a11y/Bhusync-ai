# BhuSynch AI — West Bengal Statutory Cadastral & Multi-Ministry Ingestion Blueprint

> **Jurisdiction:** State of West Bengal (State Code: `19`)  
> **Territorial Coverage:** All 23 Administrative Districts of West Bengal (Presidency, Medinipur, Burdwan, Malda, Jalpaiguri Divisions)  
> **Geodetic Datum:** Survey of India CORS Base Station `KOL1` (Kolkata) · Target CRS: `EPSG:7755` / `EPSG:32645` (WGS84 UTM 45N) & `EPSG:4326`  
> **Primary Authority:** Department of Land & Land Reforms and Refugee Relief & Rehabilitation (Banglarbhumi)

---

## 1. Statutory Authorities & Ministry Mapping

| Domain | Government Authority | Central / State Ministry | Statutory Act / Mandate | Official Portal |
| :--- | :--- | :--- | :--- | :--- |
| **Cadastral Records & Dag/Khatian Maps** | Directorate of Land Records & Surveys (DLR&S, Alipore) | Land & Land Reforms Dept, Govt of West Bengal & DoLR (MoRD) | West Bengal Land Reforms Act, 1955 & DILRMP / NAKSHA | [banglarbhumi.gov.in](https://banglarbhumi.gov.in/) |
| **Geodesy & CORS Base Station** | Survey of India (Eastern Zone Directorate, Kolkata) | Ministry of Science & Technology, Govt of India | National Geospatial Policy 2022 | [surveyofindia.gov.in](https://www.surveyofindia.gov.in/) |
| **Urban Planning & Road RoW** | KMDA / SJDA / ADDA / HDA / KMC / Municipal Corporations | Urban Development & Municipal Affairs Dept & MoHUA | West Bengal Town and Country (Planning and Development) Act, 1979 | [kmda.wb.gov.in](https://kmda.wb.gov.in/) |
| **Highways & Arterials** | PWD West Bengal / WBHDCL / NHAI | MoRTH & PWD West Bengal | National Highways Act, 1956 & WB Highways Act, 1964 | [wbpwd.gov.in](https://wbpwd.gov.in/) |
| **Waterways & Wetland Buffer** | Irrigation & Waterways Directorate & EKWMA | Department of Irrigation & Waterways & Department of Environment | East Kolkata Wetlands (Conservation and Management) Act, 2006 | [wbiwd.gov.in](https://wbiwd.gov.in/) |
| **Forest & Wildlife Sanctuaries** | Directorate of Forests / West Bengal Forest Development Corp | Department of Forests, Govt of West Bengal & MoEFCC | Wildlife Protection Act, 1972 & Forest Conservation Act, 1980 | [westbengalforest.gov.in](https://westbengalforest.gov.in/) |
| **Power Distribution Grid** | WBSEDCL / WBSETCL / CESC Limited | Department of Power, Govt of West Bengal & Ministry of Power | Electricity Act, 2003 | [wbsedcl.in](https://wbsedcl.in/) |
| **Railway & Metro Corridors** | Eastern Railway / South Eastern Railway / NFR / KMRC | Ministry of Railways | Railways Act, 1989 & Metro Railways Act, 1978 | [er.indianrailways.gov.in](https://er.indianrailways.gov.in/) |

---

## 2. Land Nomenclature & Metrics in West Bengal

| Term (Bengali / English) | Meaning | Standard Metric Equivalent |
| :--- | :--- | :--- |
| **দাগ নং (Dag No.)** | Cadastral Plot / Survey Number | Plot Identifier within Mouza |
| **খতিয়ান নং (Khatian No.)** | Record of Rights (RoR) Ledger Sheet | Record of Rights / Ownership Ledger |
| **মৌজা (Mouza) & জে.এল. নং (JL No.)** | Revenue Village & Jurisdiction List Number | Lowest Cadastral Administrative Unit |
| **কাঠা (Katha)** | Traditional West Bengal Land Area Unit | $1 \text{ Katha} = 720 \text{ sq.ft} \approx 66.89 \text{ m}^2$ |
| **ছটাক (Chhatak)** | Sub-division of Katha ($1/16$ Katha) | $1 \text{ Chhatak} = 45 \text{ sq.ft} \approx 4.18 \text{ m}^2$ |
| **বিঘা (Bigha)** | Standard Bengal Agricultural/Urban unit ($20 \text{ Katha}$) | $1 \text{ Bigha} = 14,400 \text{ sq.ft} \approx 1,337.80 \text{ m}^2$ |
| **বাস্তু (Bastu)** | Residential Homestead Land Class | High-value urban settlement zone |
| **ধানী / সালী (Dhani / Sali)** | Agricultural Land / Single Crop Paddy | Agricultural zone |
| **ডাঙ্গা (Danga)** | High Arable Land | Agricultural/commercial conversion zone |
| **বাগান (Bagan)** | Orchard / Plantation | Green conservation buffer |
| **নয়ানজুলি / জলা (Nayan-Juli / Jala)** | Canal roadside drain / Waterbody | Zero-construction conservation buffer |
| **সরকারি খাস (Sarkari Khas)** | Government Vested Land | State-owned public property |

---

## 3. Actual Downloaded & Integrated Statewide Datasets

All files are stored in `frontend/data/` and mirrored in `C:/Users/rajab/Desktop/Data/`:

1. `official_west_bengal_districts.geojson`: Official 23 District Boundaries of West Bengal (DataMeet / Census of India, 437.6 KB).
2. `official_kolkata_wards.geojson`: Official 141 Municipal Wards of Kolkata (DataMeet Municipal Spatial Data, 6.65 MB).
3. `official_west_bengal_state_boundary.geojson`: Official State Administrative Divisions (BharatViz / Survey of India Specifications, 110.7 KB).
4. `official_kolkata_city_boundary.geojson`: Official Kolkata Metropolitan Urban Polygon (Uber Movement Open Data, 5.9 KB).
5. `official_osm_bidhannagar_elements.geojson`: Real Bidhannagar Sector V Cadastre & Infrastructure (OpenStreetMap Overpass, 270.8 KB).
6. `indian_states_all.geojson`: All 35 Indian States & UT Boundaries (Survey of India, 12.0 MB).
7. `statewide_west_bengal_cadastral_parcels.geojson`: 552 Cadastral Parcels with Dag/Khatian numbers across all 23 districts (943.5 KB).
8. `statewide_west_bengal_ror_records.json`: 552 Banglarbhumi Certified RoR Khatians across all 23 districts (280 KB).
9. `statewide_west_bengal_highways.geojson`: NH-12, NH-16, NH-19, NH-27, NH-10 Expressways and Arterials.
10. `statewide_west_bengal_railways.geojson`: Eastern Railway, South Eastern Railway, and NFR corridors.
11. `statewide_west_bengal_rivers.geojson`: Hooghly (NW-1), Teesta, Damodar, Mahananda, Subarnarekha rivers.
12. `statewide_west_bengal_forests.geojson`: Sundarbans, Buxa, Jaldapara, Gorumara, Singalila protected zones.
13. `statewide_west_bengal_spatial_conflicts.geojson`: Multi-district statutory conflict dossiers.
