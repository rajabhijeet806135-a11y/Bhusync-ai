/**
 * BhuSynch AI — Mock Data & Adjudication Cases
 * Provides fallback and ground-truth dispute cases for West Bengal & Maharashtra
 */

const MockData = {
    center: [88.3450, 22.7150], // Default centered on Rishra, Hooghly
    zoom: 16.2,

    adjudicationCases: {
        // ─── Piska More (Ranchi, Jharkhand) Disputes ───
        'CONF-JH-RNC-PSK-101': {
            id: 'CONF-JH-RNC-PSK-101',
            ulpin: '20340204000101',
            khasra_no: 'प्लॉट नं. २०१, खाता नं. ४०१ (Piska More Chowk / Ratu Road)',
            village: 'Piska More Chowk (Thana No. 202)',
            district: 'Ranchi (राँची, Jharkhand)',
            legal: {
                owner: 'सुरेश प्रसाद केशरी (Suresh Prasad Keshri)',
                area: '345.00 m² (8.52 Decimal)',
                khasra: 'प्लॉट २०१ / खाता ४०१',
                landType: 'व्यावसायिक दुकान (Commercial Market)'
            },
            physical: {
                observedArea: '379.20 m² (9.37 Decimal)',
                rmse: '0.038 m',
                vertices: 16,
                ndsmChange: '+3.8 m (RCC Canopy & Highway Frontage)'
            },
            admin: {
                khataNo: '401',
                zone: 'Ratu Road NH-75 30m RoW Commercial Corridor',
                taxStatus: 'Current (RMC Sukhdeonagar Ward)',
                encumbrance: 'NHAI / PWD Highway Reservation Notice'
            },
            discrepancy: {
                deltaArea: '+34.20 m² (+9.91%)',
                tolerance: '± 2.0%',
                sigmaMajor: '0.038 m',
                frechetDistance: '0.36 m'
            },
            aiRecommendation: 'Commercial market frontage and portico project 3.4m into the statutory 30-meter Right-of-Way of NH-75 (Ratu Road) at Piska More Chowk. Direct setback alignment to highway boundary under Control of National Highways Act 2002.'
        },

        'CONF-JH-RNC-PSK-102': {
            id: 'CONF-JH-RNC-PSK-102',
            ulpin: '20340204000102',
            khasra_no: 'प्लॉट नं. २०२, खाता नं. ४०२ (Hehal ITI Road Tribal Land)',
            village: 'Hehal (Thana No. 204)',
            district: 'Ranchi (राँची, Jharkhand)',
            legal: {
                owner: 'सोमरा उरांव (Somra Oraon, ST Raiyat)',
                area: '820.00 m² (20.26 Decimal)',
                khasra: 'प्लॉट २०२ / खाता ४०२',
                landType: 'बकास्त रैयती (Bakast Raiyati - CNT Protected)'
            },
            physical: {
                observedArea: '888.40 m² (21.95 Decimal)',
                rmse: '0.041 m',
                vertices: 14,
                ndsmChange: '+2.4 m (Unauthorized Godown Foundation)'
            },
            admin: {
                khataNo: '402',
                zone: 'Hehal Urban Expansion Zone',
                taxStatus: 'Restricted Mutation Hold',
                encumbrance: 'Section 46 / 71A CNT Act 1908 Statutory Restriction'
            },
            discrepancy: {
                deltaArea: '+68.40 m² (+8.34%)',
                tolerance: '± 2.0%',
                sigmaMajor: '0.041 m',
                frechetDistance: '0.40 m'
            },
            aiRecommendation: 'Tribal raiyati holding in Mouza Hehal illegally transferred for commercial godown without Deputy Commissioner Ranchi sanction. Order eviction under Sec 71A CNT Act and freeze title mutation in Jharbhoomi.'
        },

        // ─── Ranchi General City Disputes ───
        'CONF-JH-RNC-101': {
            id: 'CONF-JH-RNC-101',
            ulpin: '20340000000101',
            khasra_no: 'प्लॉट नं. १०१, खाता नं. ३०१ (Morabadi Tribal Land)',
            village: 'Morabadi (Thana No. 198)',
            district: 'Ranchi (राँची, Jharkhand)',
            legal: {
                owner: 'बीरेंद्र मुंडा (Birendra Munda, ST Raiyat)',
                area: '720.00 m² (17.80 Decimal)',
                khasra: 'प्लॉट १०१ / खाता ३०१',
                landType: 'बकास्त रैयती (Bakast Raiyati)'
            },
            physical: {
                observedArea: '792.80 m² (19.60 Decimal)',
                rmse: '0.045 m',
                vertices: 14,
                ndsmChange: '+4.2 m (Commercial RCC Column Skeletons)'
            },
            admin: {
                khataNo: '301',
                zone: 'Morabadi Urban Zone',
                taxStatus: 'Restricted Mutation Hold',
                encumbrance: 'Section 46 / 71A CNT Act 1908 Restriction'
            },
            discrepancy: {
                deltaArea: '+72.80 m² (+10.11%)',
                tolerance: '± 2.0%',
                sigmaMajor: '0.045 m',
                frechetDistance: '0.42 m'
            },
            aiRecommendation: 'Tribal raiyati land transfer without Deputy Commissioner Ranchi prior sanction is void under Sec 46 CNT Act 1908. Restore possession to tribal raiyat under Sec 71A and halt mutation in Jharbhoomi.'
        },

        'CONF-JH-RNC-102': {
            id: 'CONF-JH-RNC-102',
            ulpin: '20340000000102',
            khasra_no: 'प्लॉट नं. २०२, खाता नं. ३०२ (Subarnarekha Riverfront)',
            village: 'Namkum (Thana No. 220)',
            district: 'Ranchi (राँची, Jharkhand)',
            legal: {
                owner: 'Subarnarekha Resorts & Banquets',
                area: '3,850.00 m² (95.13 Decimal)',
                khasra: 'प्लॉट २०२ / खाता ३०२',
                landType: 'व्यावसायिक (Commercial)'
            },
            physical: {
                observedArea: '3,902.40 m² (96.43 Decimal)',
                rmse: '0.042 m',
                vertices: 18,
                ndsmChange: '+1.8 m (Riparian Retaining Wall)'
            },
            admin: {
                khataNo: '302',
                zone: '50m River High Flood Buffer',
                taxStatus: 'Pending Clearance',
                encumbrance: 'NGT & State River Basin Order'
            },
            discrepancy: {
                deltaArea: '+52.40 m² (+1.36%)',
                tolerance: '± 2.0%',
                sigmaMajor: '0.042 m',
                frechetDistance: '0.34 m'
            },
            aiRecommendation: 'Commercial boundary wall encroaches 52.40 m² into the 50m statutory high-flood eco-buffer of Subarnarekha River. Issue removal notice under Bihar/Jharkhand Public Land Encroachment Act 1956.'
        },

        // ─── West Medinipur (Midnapore & Kharagpur) Disputes ───
        'CONF-WB-PMED-101': {
            id: 'CONF-WB-PMED-101',
            ulpin: '191833372909',
            khasra_no: 'দাগ নং ১০১, খতিয়ান ৩০১ (Inda / NH-16 Corridor)',
            village: 'Inda / Kharagpur (J.L. No. 142)',
            district: 'Paschim Medinipur (পশ্চিম মেদিনীপুর)',
            legal: {
                owner: 'Tata Metaliks Ancillary Logistics Hub',
                area: '3,250.00 m² (2 Bigha 8.5 Katha)',
                khasra: 'দাগ ১০১ / খতিয়ান ৩০১',
                landType: 'কলকারখানা (Industrial / Logistics)'
            },
            physical: {
                observedArea: '3,292.50 m² (2 Bigha 9.2 Katha)',
                rmse: '0.042 m',
                vertices: 16,
                ndsmChange: '+3.2 m (Heavy Concrete Boundary Wall & Ramp)'
            },
            admin: {
                khataNo: '301',
                zone: 'NH-16 60m Highway Right-of-Way Buffer',
                taxStatus: 'Current (Kharagpur Municipality)',
                encumbrance: 'NHAI Statutory Reservation Notice 2024'
            },
            discrepancy: {
                deltaArea: '+42.50 m² (+1.31%)',
                tolerance: '± 2.0%',
                sigmaMajor: '0.042 m',
                frechetDistance: '0.44 m'
            },
            aiRecommendation: 'Logistics loading ramp extends 3.8m into the 60m statutory Right-of-Way of National Highway 16 (Golden Quadrilateral). Realign boundary to NHAI Highway Boundary Line per Control of National Highways Act 2002.'
        },

        'CONF-WB-PMED-102': {
            id: 'CONF-WB-PMED-102',
            ulpin: '191833763160',
            khasra_no: 'দাগ নং ১০২, খতিয়ান ৩০২ (Kangsabati Riverfront Embankment)',
            village: 'Medinipur Town (J.L. No. 110)',
            district: 'Paschim Medinipur (পশ্চিম মেদিনীপুর)',
            legal: {
                owner: 'Kasai Riverfront Brickfield Consortium',
                area: '4,820.00 m² (3 Bigha 12.0 Katha)',
                khasra: 'দাগ ১০২ / খতিয়ান ৩০২',
                landType: 'ডাঙ্গা / ধানী (Commercial Arable)'
            },
            physical: {
                observedArea: '4,898.20 m² (3 Bigha 13.2 Katha)',
                rmse: '0.046 m',
                vertices: 20,
                ndsmChange: '+1.5 m (Earthen Bund & Chimney Siding)'
            },
            admin: {
                khataNo: '302',
                zone: 'Kangsabati 20m High Flood Line Conservation Zone',
                taxStatus: 'Notice Served (Medinipur Sadar BL&LRO)',
                encumbrance: 'Irrigation & Waterways Dept Embankment Order'
            },
            discrepancy: {
                deltaArea: '+78.20 m² (+1.62%)',
                tolerance: '± 2.0%',
                sigmaMajor: '0.046 m',
                frechetDistance: '0.52 m'
            },
            aiRecommendation: 'Brickfield boundary fence encroaches 8.5m into the 20m high-flood embankment buffer of River Kangsabati. Mandate set-back under Bengal Embankment Act 1882 to ensure structural safety of flood levees.'
        },

        'CONF-WB-PMED-103': {
            id: 'CONF-WB-PMED-103',
            ulpin: '191834132992',
            khasra_no: 'দাগ নং ১০৩, খতিয়ান ৩০৩ (Nimpura Industrial Growth Centre)',
            village: 'Nimpura Industrial (J.L. No. 156)',
            district: 'Paschim Medinipur (পশ্চিম মেদিনীপুর)',
            legal: {
                owner: 'Nimpura Precision Engineering Works',
                area: '1,850.00 m² (1 Bigha 7.6 Katha)',
                khasra: 'দাগ ১০৩ / খতিয়ান ৩০৩',
                landType: 'কলকারখানা (Industrial Engineering)'
            },
            physical: {
                observedArea: '1,881.40 m² (1 Bigha 8.1 Katha)',
                rmse: '0.038 m',
                vertices: 14,
                ndsmChange: '0.0 m'
            },
            admin: {
                khataNo: '303',
                zone: 'WBIDC Growth Centre Sector 2',
                taxStatus: 'Current (Corporate Lease)',
                encumbrance: 'WBIDC 99-year Industrial Lease'
            },
            discrepancy: {
                deltaArea: '+31.40 m² (+1.70%)',
                tolerance: '± 2.0%',
                sigmaMajor: '0.038 m',
                frechetDistance: '0.22 m'
            },
            aiRecommendation: 'Discrepancy is within 2.0% allowable tolerance under West Bengal Land Reforms Rules. Auto-conflate boundary with Survey of India KGP1 CORS baseline and issue updated ULPIN digital certificate.'
        },

        // ─── Rishra, Hooghly Disputes ───
        'CONF-WB-HGL-RIS-104': {
            id: 'CONF-WB-HGL-RIS-104',
            ulpin: '191472303480',
            khasra_no: 'দাগ নং ১০৪, খতিয়ান ২০৪ (GT Road, Rishra Ward 4)',
            village: 'Rishra (J.L. No. 12)',
            district: 'Hooghly (হুগলী)',
            legal: {
                owner: 'Tarapada Mukherjee & Brothers (ব্যক্তিগত রায়ত)',
                area: '267.50 m² (4.00 Katha)',
                khasra: 'দাগ ১০৪ / খতিয়ান ২০৪',
                landType: 'বাস্তু (Bastu / Homestead)'
            },
            physical: {
                observedArea: '298.20 m² (4.46 Katha)',
                rmse: '0.048 m',
                vertices: 14,
                ndsmChange: '+2.1 m (New Masonry Commercial Frontage)'
            },
            admin: {
                khataNo: '204',
                zone: 'Grand Trunk Road Arterial Commercial',
                taxStatus: 'Current (Rishra Municipality Ward 4)',
                encumbrance: 'Nil / Clean Title'
            },
            discrepancy: {
                deltaArea: '+30.70 m² (+11.47%)',
                tolerance: '± 2.0%',
                sigmaMajor: '0.048 m',
                frechetDistance: '0.38 m'
            },
            aiRecommendation: 'Physical fence and shop canopy extend 3.2m into Grand Trunk Road (SH-6 / PWD Highway RoW). Realign cadastral boundary to official 1955 Sajra alignment and issue notice under West Bengal Highways Act 1964.'
        },

        'CONF-WB-HGL-RIS-108': {
            id: 'CONF-WB-HGL-RIS-108',
            ulpin: '191472203478',
            khasra_no: 'দাগ নং ১০৮, খতিয়ান ২০৮ (Riverfront Ferry Ghat Zone)',
            village: 'Rishra (J.L. No. 12)',
            district: 'Hooghly (হুগলী)',
            legal: {
                owner: 'Hastings Jute Mill Estate (Leasehold)',
                area: '1,420.00 m² (1 Bigha 1.2 Katha)',
                khasra: 'দাগ ১০৮ / খতিয়ান ২০৮',
                landType: 'কলকারখানা / নয়ানজুলি (Industrial / River Buffer)'
            },
            physical: {
                observedArea: '1,488.50 m² (1 Bigha 2.2 Katha)',
                rmse: '0.042 m',
                vertices: 18,
                ndsmChange: '+0.8 m'
            },
            admin: {
                khataNo: '208',
                zone: 'National Waterway 1 / Hooghly High Water Line',
                taxStatus: 'Industrial Lease Vested',
                encumbrance: 'National Green Tribunal Buffer Review'
            },
            discrepancy: {
                deltaArea: '+68.50 m² (+4.82%)',
                tolerance: '± 2.0%',
                sigmaMajor: '0.042 m',
                frechetDistance: '0.45 m'
            },
            aiRecommendation: 'Encroachment into 15m statutory high-water buffer of River Hooghly. Enforce mandatory ecological set-back and re-triangulate boundary to high-tide line.'
        },

        'CONF-WB-HGL-RIS-112': {
            id: 'CONF-WB-HGL-RIS-112',
            ulpin: '191472153472',
            khasra_no: 'দাগ নং ১১২, খতিয়ান ২১২ (Morepukur Industrial Estate)',
            village: 'Morepukur (J.L. No. 13)',
            district: 'Hooghly (হুগলী)',
            legal: {
                owner: 'Aditya Birla Nuvo / Jayshree Textiles Ltd',
                area: '2,850.00 m² (2 Bigha 2.6 Katha)',
                khasra: 'দাগ ১১২ / খতিয়ান ২১২',
                landType: 'কলকারখানা (Industrial Manufacturing)'
            },
            physical: {
                observedArea: '2,825.40 m² (2 Bigha 2.2 Katha)',
                rmse: '0.038 m',
                vertices: 22,
                ndsmChange: '0.0 m'
            },
            admin: {
                khataNo: '212',
                zone: 'Heavy Industry Zone (Rishra Ward 14)',
                taxStatus: 'Current (Corporate)',
                encumbrance: 'Industrial Mortgage (State Bank of India)'
            },
            discrepancy: {
                deltaArea: '-24.60 m² (-0.86%)',
                tolerance: '± 2.0%',
                sigmaMajor: '0.038 m',
                frechetDistance: '0.12 m'
            },
            aiRecommendation: 'Boundary deviation is within 1.0% allowable tolerance under West Bengal Land Reforms Rules. Auto-conflate boundary to physical masonry fence line using CORS KOL1 baseline.'
        },

        // ─── Bidhannagar / Kolkata Disputes ───
        'CONF-WB-2026-0002': {
            id: 'CONF-WB-2026-0002',
            ulpin: '19312010010002',
            khasra_no: 'দাগ নং ২০৮, খতিয়ান নং ১১২ (Mahisbathan, Bidhannagar)',
            village: 'Mahisbathan / Sector V',
            district: 'North 24 Parganas / Kolkata Metro',
            legal: {
                owner: 'Debabrata Mukherjee & Co.',
                area: '420.00 m² (6.28 Katha)',
                khasra: 'দাগ ২০৮ / খতিয়ান ১১২',
                landType: 'বাস্তু (Bastu)'
            },
            physical: {
                observedArea: '458.20 m² (6.85 Katha)',
                rmse: '0.039 m',
                vertices: 16,
                ndsmChange: '+1.5 m'
            },
            admin: {
                khataNo: '112',
                zone: 'Biswa Bangla Sarani Arterial',
                taxStatus: 'Current',
                encumbrance: 'KMDA RoW Acquisition Notice'
            },
            discrepancy: {
                deltaArea: '+38.20 m² (+9.09%)',
                tolerance: '± 2.0%',
                sigmaMajor: '0.039 m',
                frechetDistance: '0.34 m'
            },
            aiRecommendation: 'Boundary wall and guard pavilion extend 3.2m into sanctioned 24m DP Road Right-of-Way along Biswa Bangla Sarani. Realign boundary to KMDA approved alignment.'
        },

        'CONF-WB-2026-0005': {
            id: 'CONF-WB-2026-0005',
            ulpin: '19312010010005',
            khasra_no: 'দাগ নং ২২৪, খতিয়ান নং ১১৪ (Bidhannagar South)',
            village: 'Bidhannagar South',
            district: 'North 24 Parganas',
            legal: {
                owner: 'Eastern Infrastructure Projects Ltd',
                area: '850.00 m² (12.71 Katha)',
                khasra: 'দাগ ২২৪ / খতিয়ান ১১৪',
                landType: 'বাগান (Bagan / Orchard)'
            },
            physical: {
                observedArea: '914.50 m² (13.67 Katha)',
                rmse: '0.045 m',
                vertices: 20,
                ndsmChange: '+0.5 m'
            },
            admin: {
                khataNo: '114',
                zone: 'East Kolkata Wetlands Ramsar Site 1208',
                taxStatus: 'Notice Served',
                encumbrance: 'EKWMA Conservation Order 2006'
            },
            discrepancy: {
                deltaArea: '+64.50 m² (+7.58%)',
                tolerance: '± 2.0%',
                sigmaMajor: '0.045 m',
                frechetDistance: '0.42 m'
            },
            aiRecommendation: 'Intrusion into Ramsar Site 1208 protected buffer. Issue demolition order for unauthorized embankment under EKWMA Act 2006.'
        },

        // ─── Maharashtra / Pune Disputes ───
        'CONF-2026-0001': {
            id: 'CONF-2026-0001',
            ulpin: '27010410010002',
            khasra_no: 'Gat No: 118/2, Ward 14 (Shivajinagar)',
            village: 'Pune Urban Ward 14',
            district: 'Pune (Maharashtra State 27)',
            legal: {
                owner: 'Ramchandra K. Joshi',
                area: '529.80 m²',
                khasra: 'Gat 118/2, CTS 402',
                landType: 'Gaothan Residential'
            },
            physical: {
                observedArea: '558.20 m²',
                rmse: '0.042 m',
                vertices: 12,
                ndsmChange: '+1.2 m'
            },
            admin: {
                khataNo: '275',
                zone: 'DP 24m Road RoW',
                taxStatus: 'Current (PMC)',
                encumbrance: 'None'
            },
            discrepancy: {
                deltaArea: '+28.40 m² (+5.36%)',
                tolerance: '± 2.0%',
                sigmaMajor: '0.042 m',
                frechetDistance: '0.28 m'
            },
            aiRecommendation: 'Realign boundary to DP 24m road master plan reservation. Award proportional TDR credit to landowner.'
        },

        'CONF-2026-0002': {
            id: 'CONF-2026-0002',
            ulpin: '27010410010005',
            khasra_no: 'Gat No: 120/A, Ward 14 (Shivajinagar)',
            village: 'Pune Urban Ward 14',
            district: 'Pune (Maharashtra State 27)',
            legal: {
                owner: 'Shinde Housing Cooperative',
                area: '840.00 m²',
                khasra: 'Gat 120/A, CTS 405',
                landType: 'Residential R-2'
            },
            physical: {
                observedArea: '895.00 m²',
                rmse: '0.044 m',
                vertices: 16,
                ndsmChange: '+0.4 m'
            },
            admin: {
                khataNo: '310',
                zone: 'Mutha River Nallah Buffer',
                taxStatus: 'Current',
                encumbrance: 'Irrigation Dept Flood Line'
            },
            discrepancy: {
                deltaArea: '+55.00 m² (+6.55%)',
                tolerance: '± 2.0%',
                sigmaMajor: '0.044 m',
                frechetDistance: '0.36 m'
            },
            aiRecommendation: 'Encroachment into 9m blue flood line buffer. Enforce flood safety set-back per Irrigation Act.'
        }
    }
};

window.MockData = MockData;
