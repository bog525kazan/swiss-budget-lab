import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import time
import random

# --- 1. НАСТРОЙКА ДИЗАЙНА ---
st.set_page_config(layout="wide", page_title="Swiss Strategy Game")

st.markdown("""
    <style>
    .main { background-color: #FFFFFF; color: #2C3E50; font-family: 'Helvetica Neue', sans-serif; }
    h1, h2, h3 { color: #003366; }
    div[data-testid="stMetricValue"] { color: #0055A6; font-weight: bold; }
    .stSlider > div[data-baseweb="slider"] > div > div { background-color: #0055A6 !important; }
    
    /* Стили уведомлений */
    .game-alert-bad {
        padding: 15px;
        background-color: #e74c3c;
        color: white;
        border-radius: 10px;
        text-align: center;
        font-size: 20px;
        font-weight: bold;
        margin-bottom: 10px;
        animation: pulse 1s infinite;
        border: 2px solid #c0392b;
        box-shadow: 0 4px 10px rgba(0,0,0,0.2);
    }
    
    .game-alert-good {
        padding: 15px;
        background-color: #27ae60;
        color: white;
        border-radius: 10px;
        text-align: center;
        font-size: 20px;
        font-weight: bold;
        margin-bottom: 10px;
        border: 2px solid #2ecc71;
        box-shadow: 0 4px 10px rgba(0,0,0,0.2);
    }
    
    /* Красный алерт для критической халатности */
    .critical-warning {
        color: #c0392b; 
        font-weight: bold; 
        font-size: 15px; 
        background-color: #fadbd8; 
        padding: 8px; 
        border-radius: 5px; 
        margin-bottom: 5px; 
        border-left: 5px solid #c0392b;
        animation: shake 0.5s;
        animation-iteration-count: infinite;
    }

    @keyframes shake {
        0% { transform: translate(1px, 1px) rotate(0deg); }
        10% { transform: translate(-1px, -2px) rotate(-1deg); }
        20% { transform: translate(-3px, 0px) rotate(1deg); }
        30% { transform: translate(3px, 2px) rotate(0deg); }
        40% { transform: translate(1px, -1px) rotate(1deg); }
        50% { transform: translate(-1px, 2px) rotate(-1deg); }
        60% { transform: translate(-3px, 1px) rotate(0deg); }
        70% { transform: translate(3px, 1px) rotate(-1deg); }
        80% { transform: translate(-1px, -1px) rotate(1deg); }
        90% { transform: translate(1px, 2px) rotate(0deg); }
        100% { transform: translate(1px, -2px) rotate(-1deg); }
    }
    
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.02); }
        100% { transform: scale(1); }
    }
    
    .timer-box {
        font-size: 24px;
        font-weight: bold;
        color: #2C3E50;
        text-align: center;
        border: 2px solid #2C3E50;
        padding: 8px;
        border-radius: 8px;
    }
    
    /* Большая цифра доверия */
    .big-trust-number {
        font-size: 110px;
        font-weight: 900;
        text-align: center;
        line-height: 1;
        text-shadow: 3px 3px 6px rgba(0,0,0,0.2);
        transition: color 0.5s ease;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. ИНИЦИАЛИЗАЦИЯ СОСТОЯНИЯ ---
if 'game_active' not in st.session_state: st.session_state.game_active = False
if 'start_time' not in st.session_state: st.session_state.start_time = 0
if 'last_event_time' not in st.session_state: st.session_state.last_event_time = 0
if 'current_event' not in st.session_state: st.session_state.current_event = None
if 'game_result' not in st.session_state: st.session_state.game_result = None
if 'revenue_shock_factor' not in st.session_state: st.session_state.revenue_shock_factor = 1.0
if 'extra_budget'
