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
if 'game_active' not in st.session_state:
    st.session_state.game_active = False
if 'start_time' not in st.session_state:
    st.session_state.start_time = 0
if 'penalties' not in st.session_state:
    st.session_state.penalties = 0 
if 'last_event_time' not in st.session_state:
    st.session_state.last_event_time = 0
if 'current_event' not in st.session_state:
    st.session_state.current_event = None
if 'game_result' not in st.session_state:
    st.session_state.game_result = None
if 'revenue_shock_factor' not in st.session_state:
    st.session_state.revenue_shock_factor = 1.0
if 'bonus_trust' not in st.session_state:
    st.session_state.bonus_trust = 0 
if 'extra_budget' not in st.session_state:
    st.session_state.extra_budget = 0
if 'event_solved_flag' not in st.session_state:
    st.session_state.event_solved_flag = False
if 'active_warnings' not in st.session_state:
    st.session_state.active_warnings = []

# --- 3. ДАННЫЕ СОБЫТИЙ ---
BAD_EVENTS = [
    {"title": "🦠 ВСПЫШКА ГРИППА!", "desc": "Больницы переполнены. Соц. обеспечение > 42 млрд!", "condition": lambda s: s['social'] >= 42, "type": "bad"},
    {"title": "👵 ПЕНСИОННЫЙ КРИЗИС!", "desc": "Фонд пуст. Соц. обеспечение > 45 млрд!", "condition": lambda s: s['social'] >= 45, "type": "bad"},
    {"title": "📉 ОБВАЛ БИРЖИ!", "desc": "Банки просят помощи. Госуправление > 12 млрд!", "condition": lambda s: s['admin'] >= 12, "type": "bad"},
    {"title": "💻 КИБЕРАТАКА!", "desc": "Взлом реестров. Госуправление > 15 млрд!", "condition": lambda s: s['admin'] >= 15, "type": "bad"},
    {"title": "🚆 ОБВАЛ В АЛЬПАХ!", "desc": "Тоннель заблокирован. Транспорт > 18 млрд!", "condition": lambda s: s['transport'] >= 18, "type": "bad"},
    {"title": "❄️ СНЕЖНЫЙ ШТОРМ!", "desc": "Дороги встали. Транспорт > 22 млрд!", "condition": lambda s: s['transport'] >= 22, "type": "bad"},
    {"title": "🪖 ВОЕННАЯ УГРОЗА!", "desc": "Усилить границы. Оборона > 14 млрд!", "condition": lambda s: s['security'] >= 14, "type": "bad"},
    {"title": "🎓 ЗАБАСТОВКА УЧИТЕЛЕЙ!", "desc": "Школы закрыты. Образование > 16 млрд!", "condition": lambda s: s['education'] >= 16, "type": "bad"},
    {"title": "🔥 АНОМАЛЬНАЯ ЖАРА!", "desc": "Нужны кондиционеры и врачи. Соц. обеспечение > 35 и Транспорт > 12!", "condition": lambda s: s['social'] >= 35 and s['transport'] >= 12, "type": "bad"},
]

GOOD_EVENTS = [
    {"title": "💉 НАУЧНЫЙ ПРОРЫВ!", "desc": "Наши ученые получили Нобелевку! (+4% доверия)", "effect": "trust", "val": 4, "type": "good"},
    {"title": "🏆 ПОБЕДА В СПОРТЕ!", "desc": "Нация ликует! (+3% доверия)", "effect": "trust", "val": 3, "type": "good"},
    {"title": "🏔️ ТУРИСТИЧЕСКИЙ БУМ!", "desc": "Все едут в Альпы. (+6 млрд в бюджет)", "effect": "money", "val": 6, "type": "good"},
    {"title": "🍫 РЕКОРД ЭКСПОРТА!", "desc": "Сверхприбыль корпораций. (+4 млрд в бюджет)", "effect": "money", "val": 4, "type": "good"},
    {"title": "☮️ МИРНАЯ КОНФЕРЕНЦИЯ!", "desc": "Женева - столица мира. (+5% доверия)", "effect": "trust", "val": 5, "type": "good"},
]

# --- 4. ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---
def start_game():
    st.session_state.game_active = True
    st.session_state.start_time = time.time()
    st.session_state.last_event_time = time.time()
    st.session_state.penalties = 0
    st.session_state.current_event = None
    st.session_state.game_result = None
    st.session_state.revenue_shock_factor = 1.0
    st.session_state.bonus_trust = 0
    st.session_state.extra_budget = 0
    st.session_state.event_solved_flag = False

def get_color_for_trust(value):
    if value < 30: return "#e74c3c" 
    if value < 50: return "#e67e22" 
    if value < 75: return "#f1c40f" 
    return "#2ecc71" 

# --- 5. ЭКРАНЫ ИГРЫ ---

# 5.1 Стартовый экран
if not st.session_state.game_active and st.session_state.game_result is None:
    st.title("🇨🇭 Симулятор Швейцарии: Реалистичный режим")
    st.info("""
    ### ⚡ ВНИМАНИЕ! Новые правила безопасности:
    Нельзя просто так урезать бюджет. За критически низкие расходы будут последствия:
    
    * 🛡️ **Оборона < 12 млрд:** Армия бунтует (Очень быстро падает доверие!).
    * 🎓 **Образование < 10 млрд:** Забастовки учителей.
    * 🏛️ **Госуправление < 8 млрд:** Хаос в мэриях.
    * 🏥 **Медицина < 19 млрд:** **ДВОЙНОЙ УДАР!** Падает доверие И падают доходы (люди не работают).
    """)
    if st.button("НАЧАТЬ ИГРУ", type="primary", use_container_width=True):
        start_game()
        st.rerun()

# 5.2 Экран конца игры
elif st.session_state.game_result:
    if st.session_state.game_result == "win":
        st.balloons()
        st.success(f"🏆 ПОБЕДА! Год завершен успешно. Доверие: {st.session_state.final_trust}%")
    else:
        st.error(f"💀 ВЫ УВОЛЕНЫ! {st.session_state.fail_reason}")
    
    if st.button("Играть снова"):
        start_game()
        st.rerun()

# 5.3 Основной игровой процесс
else:
    elapsed_time = int(time.time() - st.session_state.start_time)
    time_left = 180 - elapsed_time
    
    # ЭНТРОПИЯ (падение доверия со временем)
    entropy_loss = elapsed_time * 0.1
    
    # ЧЕРНЫЙ ЛЕБЕДЬ (Случайный обвал доходов)
    if st.session_state.revenue_shock_factor == 1.0 and random.random() < 0.015:
        shock = random.uniform(0.07, 0.10)
        st.session_state.revenue_shock_factor = 1.0 - shock
        st.toast(f"📉 ЧЕРНЫЙ ЛЕБЕДЬ! Доходы упали на {int(shock*100)}%!", icon="🦢")

    # --- САЙДБАР (УПРАВЛЕНИЕ) ---
    st.sidebar.header("⚙️ Распределение Бюджета")
    exp_social = st.sidebar.slider("🏥 Соц. обеспечение (Мин. 19)", 0.0, 60.0, 30.0, 0.5)
    exp_education = st.sidebar.slider("🎓 Образование (Мин. 10)", 0.0, 30.0, 10.0, 0.5)
    exp_transport = st.sidebar.slider("🚆 Транспорт", 0.0, 30.0, 10.0, 0.5)
    exp_security = st.sidebar.slider("🛡️ Оборона (Мин. 12)", 0.0, 30.0, 12.0, 0.5)
    exp_admin = st.sidebar.slider("🏛️ Госуправление (Мин. 8)", 0.0, 20.0, 8.0, 0.5)
    
    current_stats = {
        'social': exp_social, 'admin': exp_admin, 
        'transport': exp_transport, 'security': exp_security, 
        'education': exp_education
    }

    # --- ЛОГИКА "ХАЛАТНОСТИ" ---
    st.session_state.active_warnings = []
    
    # 1. Оборона (< 12.0)
    if exp_security < 12.0:
        penalty_hit = random.uniform(0.6, 0.9) # Быстрое падение
        st.session_state.penalties += penalty_hit
        st.session_state.active_warnings.append(f"🛡️ БУНТ АРМИИ! (Расходы < 12 млрд)")

    # 2. Образование (< 10.0)
    if exp_education < 10.0:
        penalty_hit = random.uniform(0.4, 0.6) # Среднее падение
        st.session_state.penalties += penalty_hit
        st.session_state.active_warnings.append(f"🎓 ЗАБАСТОВКИ! (Расходы < 10 млрд)")

    # 3. Госуправление (< 8.0)
    if exp_admin < 8.0:
        penalty_hit = random.uniform(0.3, 0.5) # Умеренное падение
        st.session_state.penalties += penalty_hit
        st.session_state.active_warnings.append(f"🏛️ ХАОС В МЭРИЯХ! (Расходы < 8 млрд)")

    # 4. Медицина (< 19.0)
    if exp_social < 19.0:
        penalty_hit = random.uniform(0.4, 0.6)
        st.session_state.penalties += penalty_hit
        # Падение доходов
        if st.session_state.revenue_shock_factor > 0.6: 
            st.session_state.revenue_shock_factor -= 0.0015
        st.session_state.active_warnings.append(f"🏥 ЭПИДЕМИЯ! Доходы падают! (Расходы < 19 млрд)")

    # --- ОБРАБОТКА СОБЫТИЙ ---
    time_since_last = time.time() - st.session_state.last_event_time
    
    # Если событие активно
    if st.session_state.current_event:
        evt = st.session_state.current_event
        if evt['type'] == 'bad':
            is_solved = evt['condition'](current_stats)
            
            if is_solved:
                status_msg = "✅ РЕШЕНО! ДЕРЖАТЬ ПОЗИЦИИ"
                if not st.session_state.event_solved_flag:
                    bonus = random.randint(3, 6)
                    st.session_state.bonus_trust += bonus
                    st.session_state.event_solved_flag = True
                    st.toast(f"Отлично! Доверие +{bonus}%", icon="🚀")
            else:
                status_msg = "❌ КРИЗИС! ПРИМИТЕ МЕРЫ"
            
            if time_since_last > 15: 
                if not is_solved:
                    damage = random.randint(10, 16)
                    st.session_state.penalties += damage
                    st.toast(f"Провал! Штраф -{damage}%", icon="💥")
                else:
                    st.toast("Угроза миновала.", icon="🛡️")
                
                st.session_state.current_event = None
                st.session_state.last_event_time = time.time()
                st.session_state.event_solved_flag = False

        elif evt['type'] == 'good':
            if time_since_last > 5:
                st.session_state.current_event = None
                st.session_state.last_event_time = time.time()
                st.session_state.event_solved_flag = False

    # ГЕНЕРАЦИЯ НОВОГО (каждые 9-16 сек)
    elif time_since_last > random.randint(9, 16):
        if random.random() < 0.73:
            st.session_state.current_event = random.choice(BAD_EVENTS)
            st.session_state.event_solved_flag = False
        else:
            good_evt = random.choice(GOOD_EVENTS)
            st.session_state.current_event = good_evt
            st.session_state.event_solved_flag = False
            
            if good_evt['effect'] == 'trust':
                st.session_state.bonus_trust += good_evt['val']
                st.toast(f"Хорошие новости! +{good_evt['val']}%", icon="🎉")
            elif good_evt['effect'] == 'money':
                st.session_state.extra_budget += good_evt['val']
                st.toast(f"Прибыль! +{good_evt['val']} млрд", icon="💰")
        
        st.session_state.last_event_time = time.time()
        st.rerun()

    # --- ФИНАНСЫ ---
    revenue_base = 85.0
    revenue = (revenue_base * st.session_state.revenue_shock_factor) + st.session_state.extra_budget
    total_spending = sum(current_stats.values())
    balance = revenue - total_spending
    
    # --- ДОВЕРИЕ ---
    base_trust = 60 
    
    # Штраф за дефицит
    if balance < 0: base_trust -= abs(balance) * 0.8
    
    final_trust = base_trust - st.session_state.penalties - entropy_loss + st.session_state.bonus_trust
    final_trust = max(min(int(final_trust), 100), 0)

    # --- GAME OVER ---
    if final_trust < 30:
        st.session_state.game_result = "lose"
        st.session_state.fail_reason = "Революция! Доверие упало ниже 30%."
        st.rerun()
    if balance < -35: 
        st.session_state.game_result = "lose"
        st.session_state.fail_reason = "Банкротство! Дефицит превысил 35 млрд."
        st.rerun()
    if time_left <= 0:
        st.session_state.final_trust = final_trust
        st.session_state.game_result = "win"
        st.rerun()

    # --- ОТРИСОВКА ИНТЕРФЕЙСА ---
    c1, c2 = st.columns([1, 2])
    with c1:
        st.markdown(f'<div class="timer-box">🗓 День {elapsed_time*2} / 365</div>', unsafe_allow_html=True)
        if st.session_state.active_warnings:
            for warn in st.session_state.active_warnings:
                st.markdown(f"<div class='critical-warning'>{warn}</div>", unsafe_allow_html=True)
            
    with c2:
        if st.session_state.current_event:
            evt = st.session_state.current_event
            if evt['type'] == 'bad':
                st.markdown(f"""
                <div class="game-alert-bad">
                🚨 {evt['title']}<br>
                <span style="font-size:16px">{evt['desc']}</span><br>
                <div style="margin-top:5px; background:white; color:black; border-radius:5px; display:inline-block; padding:2px 8px;">
                {status_msg}
                </div>
                </div>
                """, unsafe_allow_html=True)
            elif evt['type'] == 'good':
                st.markdown(f"""
                <div class="game-alert-good">
                ✨ {evt['title']}<br>
                <span style="font-size:16px">{evt['desc']}</span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("В стране спокойно...")

    st.divider()

    col_main_trust, col_main_balance = st.columns([1, 1])
    
    with col_main_trust:
        trust_color = get_color_for_trust(final_trust)
        st.markdown(f"<div style='text-align:center; color:#7f8c8d; font-size:20px;'>ДОВЕРИЕ НАСЕЛЕНИЯ</div>", unsafe_allow_html=True)
        st.markdown(f"""
        <div class="big-trust-number" style="color: {trust_color};">
        {final_trust}%
        </div>
        """, unsafe_allow_html=True)
        st.caption(f"Бонусы: +{st.session_state.bonus_trust}% | Штрафы: -{int(st.session_state.penalties + entropy_loss)}%")

    with col_main_balance:
        st.markdown(f"<div style='text-align:center; color:#7f8c8d; font-size:20px;'>БЮДЖЕТ (МЛРД CHF)</div>", unsafe_allow_html=True)
        
        b1, b2, b3 = st.columns(3)
        b1.metric("Доходы", f"{revenue:.1f}", delta="-Кризис" if st.session_state.revenue_shock_factor < 1 else None, delta_color="inverse")
        b2.metric("Расходы", f"{total_spending:.1f}")
        b3.metric("БАЛАНС", f"{balance:.1f}", delta="OK" if balance > 0 else "Дефицит")
        
        fig_bar = go.Figure(go.Bar(
            x=[total_spending, revenue],
            y=['Расходы', 'Доходы'],
            orientation='h',
            marker_color=['#c0392b', '#27ae60'],
            text=[f"{total_spending:.1f}", f"{revenue:.1f}"],
            textposition='auto'
        ))
        fig_bar.update_layout(height=120, margin={"r":0,"t":0,"l":0,"b":0}, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_bar, use_container_width=True)

    time.sleep(1)
    st.rerun()
