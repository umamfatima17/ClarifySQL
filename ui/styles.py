
import streamlit as st


def load_styles():
    st.markdown(
        """
        <style>
        :root {
            --page: #F9F9F6;
            --surface: #FFFFFF;
            --green: #2D5A43;
            --green-dark: #204631;
            --green-soft: #EAF1EB;
            --ink: #202A24;
            --muted: #626E65;
            --line: #E2E7E1;
            --gold: #B69A62;
            --coral: #D47769;
        }

        .stApp {
            background: var(--page);
            color: var(--ink);
        }

        [data-testid="stHeader"] {
            background: transparent;
        }

        #MainMenu, footer {
            visibility: hidden;
        }

        /* Main content width and spacing */
        .block-container {
            width: 100%;
            max-width: 1600px;
            margin-left: auto;
            margin-right: auto;
            padding: 1.8rem 2rem 2.5rem;
        }

        /* Premium dark sidebar */
        section[data-testid="stSidebar"] {
            width: 280px !important;
            min-width: 280px !important;
            background: linear-gradient(
                180deg,
                #172A22 0%,
                #1B3026 48%,
                #14251D 100%
            );
            border-right: 1px solid #304638;
        }

        section[data-testid="stSidebar"] > div:first-child {
            padding: 1.5rem 1rem 1.5rem;
        }

        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
            color: #D8E2D9;
        }

        .brand {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 3px 0 22px;
            border-bottom: 1px solid rgba(218, 190, 128, 0.22);
            margin-bottom: 24px;
        }

        .brand-logo {
            width: 44px;
            height: 44px;
            flex-shrink: 0;
            display: flex;
            align-items: center;
            justify-content: center;
            border: 1px solid #C8AA6A;
            border-radius: 10px;
            background: linear-gradient(145deg, #D8BE82, #A9894E);
            color: #192B21;
            font: 28px Georgia, serif;
            box-shadow: 0 4px 14px rgba(0, 0, 0, 0.18);
        }

        .brand-name {
            color: #FFFDF7;
            font-size: 19px;
            font-weight: 800;
            letter-spacing: -0.6px;
        }

        .brand-tagline {
            color: #B8C8BB;
            font-size: 10px;
            line-height: 1.6;
            margin-top: 4px;
        }

        .sidebar-heading {
            color: #CDB47B;
            font-size: 10px;
            font-weight: 800;
            letter-spacing: 1.5px;
            margin: 21px 0 10px;
        }

        [data-testid="stSidebar"] div[role="radiogroup"] {
            gap: 6px;
        }

        [data-testid="stSidebar"] div[role="radiogroup"] label {
            min-height: 42px;
            box-sizing: border-box;
            padding: 10px 11px;
            border: 1px solid transparent;
            border-radius: 7px;
            background: transparent;
            transition: background 140ms ease, border-color 140ms ease;
        }

        [data-testid="stSidebar"] div[role="radiogroup"] label p {
            color: #D2DED4;
            font-size: 12px;
            font-weight: 550;
        }

        [data-testid="stSidebar"] div[role="radiogroup"] label:hover {
            background: rgba(255, 255, 255, 0.055);
            border-color: rgba(255, 255, 255, 0.08);
        }

        [data-testid="stSidebar"] div[role="radiogroup"]
        label:has(input:checked) {
            background: linear-gradient(
                90deg,
                rgba(201, 173, 111, 0.19),
                rgba(201, 173, 111, 0.07)
            );
            border: 1px solid rgba(211, 183, 120, 0.43);
            box-shadow: inset 3px 0 0 #D0B16F;
        }

        [data-testid="stSidebar"] div[role="radiogroup"]
        label:has(input:checked) p {
            color: #FFF7E2;
            font-weight: 750;
        }

        .dataset-card {
            padding: 14px;
            background: rgba(7, 18, 12, 0.28);
            border: 1px solid #3B5544;
            border-left: 3px solid #C6A765;
            border-radius: 8px;
            box-shadow: 0 5px 16px rgba(0, 0, 0, 0.08);
        }

        .dataset-title {
            color: #F8F5EB;
            font-size: 12px;
            font-weight: 750;
            line-height: 1.6;
        }

        .dataset-description {
            color: #B7C8BA;
            font-size: 10px;
            line-height: 2;
            margin-top: 7px;
        }

        .sidebar-footer {
            margin-top: 26px;
            padding-top: 15px;
            border-top: 1px solid rgba(218, 190, 128, 0.2);
            color: #AFC0B2;
            font-size: 10px;
            line-height: 1.95;
        }

        .sidebar-footer strong {
            color: #D7BC7C;
            font-size: 9px;
            letter-spacing: 0.8px;
        }

        /* Page header */
        h1 {
            color: var(--ink) !important;
            font-family: Georgia, "Times New Roman", serif !important;
            font-size: clamp(30px, 2.6vw, 42px) !important;
            font-weight: 500 !important;
            letter-spacing: -1.3px !important;
            line-height: 1.18 !important;
            margin: 0 0 8px !important;
        }

        h2, h3 {
            color: var(--ink) !important;
            letter-spacing: -0.4px;
        }

        .eyebrow {
            color: #465D4C;
            font-size: 10px;
            font-weight: 800;
            letter-spacing: 1.35px;
            margin-bottom: 11px;
        }

        .page-description {
            max-width: 720px;
            color: var(--muted);
            font-size: 13px;
            line-height: 1.8;
        }

        .workspace-badge {
            display: inline-block;
            padding: 7px 9px;
            background: white;
            border: 1px solid var(--line);
            border-radius: 5px;
            color: #46574A;
            font-size: 10px;
            font-weight: 750;
            letter-spacing: 0.5px;
            white-space: nowrap;
        }

        .gold-rule {
            width: 42px;
            height: 3px;
            margin: 17px 0 24px;
            background: var(--gold);
        }

        .section-title {
            color: var(--ink);
            font-size: 16px;
            font-weight: 750;
            letter-spacing: -0.35px;
            margin-bottom: 4px;
        }

        .section-subtitle {
            color: var(--muted);
            font-size: 12px;
            line-height: 1.6;
            margin-bottom: 14px;
        }

        .section-divider {
            border: 0;
            border-top: 1px solid var(--line);
            margin: 23px 0;
        }

        /* KPI cards */
        div[data-testid="stMetric"] {
            box-sizing: border-box;
            min-height: 105px;
            padding: 15px 17px;
            background: var(--surface);
            border: 1px solid var(--line);
            border-radius: 7px;
            box-shadow: 0 1px 3px rgba(30, 50, 35, 0.025);
        }

        div[data-testid="stMetricLabel"] {
            color: var(--muted);
            font-size: 12px;
            font-weight: 500;
        }

        div[data-testid="stMetricValue"] {
            color: var(--green);
            font-size: clamp(19px, 1.6vw, 27px);
            font-weight: 750;
            letter-spacing: -0.8px;
            overflow-wrap: anywhere;
        }

        div[data-testid="stMetricDelta"] {
            font-size: 11px;
        }

        /* Insights */
        .insight-card {
            padding: 15px;
            margin: 0 0 12px;
            background: #F0F5F0;
            border: 1px solid #DCE6DC;
            border-left: 3px solid var(--gold);
            border-radius: 5px;
        }

        .insight-card.secondary {
            background: white;
            border-left: 3px solid #BFCDBF;
        }

        .insight-label {
            color: var(--green);
            font-size: 10px;
            font-weight: 800;
            letter-spacing: 0.8px;
            line-height: 1.5;
            margin-bottom: 8px;
        }

        .insight-text {
            color: var(--ink);
            font-size: 12px;
            line-height: 1.8;
        }

        .insight-note {
            color: var(--muted);
            font-size: 10px;
            line-height: 1.6;
            margin: 1px 0 12px;
        }

        /* Buttons and form fields */
        .stButton > button,
        .stFormSubmitButton > button {
            min-height: 42px;
            background: var(--green);
            color: white;
            border: 1px solid var(--green);
            border-radius: 5px;
            font-size: 12px;
            font-weight: 650;
            transition: background 120ms ease;
        }

        .stButton > button:hover,
        .stFormSubmitButton > button:hover {
            background: var(--green-dark);
            color: white;
            border-color: var(--green-dark);
        }

        .stTextInput input,
        .stTextArea textarea,
        [data-baseweb="select"] > div {
            background: white;
            border-color: #DCE2DC;
            border-radius: 5px;
        }

        div[data-testid="stDataFrame"] {
            border: 1px solid var(--line);
            border-radius: 6px;
            overflow: hidden;
        }

        /* Footer */
        .app-footer {
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 8px 20px;
            width: 100%;
            box-sizing: border-box;
            border-top: 1px solid var(--line);
            margin-top: 27px;
            padding-top: 15px;
            color: var(--muted);
            font-size: 10px;
            line-height: 1.8;
        }

        .app-footer strong {
            color: #46574A;
            font-weight: 750;
        }

        @media (max-width: 1050px) {
            .block-container {
                padding: 1.4rem 1.2rem 2rem;
            }

            section[data-testid="stSidebar"] {
                width: 250px !important;
                min-width: 250px !important;
            }
        }

        @media (max-width: 650px) {
            .block-container {
                padding: 1rem 0.8rem 1.5rem;
            }

            h1 {
                font-size: 30px !important;
            }

            div[data-testid="stMetric"] {
                min-height: 96px;
                padding: 12px;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
