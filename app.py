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
    
    /* Уведомления */
    .game-alert-bad {
        padding: 15px; background-color: #e74c3c; color: white; border-radius: 10px;
        text-align: center; font-size: 20px; font-weight: bold; margin-bottom: 10px;
        animation: pulse 1s infinite; border: 2px solid #c0392b; box-shadow: 0 4px 10px rgba(0,0,0,0.2);
    }
    .game-alert-good {
        padding: 15px; background-color: #27ae60; color: white; border-radius: 10px;
        text-align: center; font-size: 20px; font-weight: bold; margin-bottom: 10px;
        border: 2px solid #2ecc71; box-shadow: 0 4px 10px rgba(0,0,0,0.2);
    }
    
    /* Статусы */
    .referendum-alert {
        background-color: #8e44ad; color: white; padding: 20px; border-radius: 10px;
        text-align: center; font-size: 24px; font-weight: bold; margin-bottom: 20px;
        border: 3px solid #6c3483; animation: shake 0.5s infinite;
    }
    .global-status {
        background-color: #ecf0f1; padding: 10px; border-radius: 5px; 
        text-align: center; font-weight: bold; border: 1px solid #bdc3c7; color: #2c3e50;
    }

    .critical-warning {
        color: #c0392b; font-weight: bold; font-size: 15px; background-color: #fadbd8;
        padding: 8px; border-radius: 5px; margin-bottom: 5px; border-left: 5px solid #c0392b;
    }

    @keyframes shake { 0% { transform: translate(1px, 1px) rotate(0deg); } 50% { transform: translate(-1px, 2px) rotate(-1deg); } 100% { transform: translate(1px, -2px) rotate(-1deg); } }
    @keyframes pulse { 0% { transform: scale(1); } 50% { transform: scale(1.02); } 100% { transform: scale(1); } }
    
    .timer-box { font-size: 24px; font-weight: bold; color: #2C3E50; text-align: center; border: 2px solid #2C3E50; padding: 8px; border-radius: 8px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. ИНИЦИАЛИЗАЦИЯ СОСТОЯНИЯ ---
if 'game_active' not in st.session_state: st.session_state.game_active = False
if 'start_time' not in st.session_state: st.session_state.start_time = 0
if 'last_event_time' not in st.session_state: st.session_state.last_event_time = 0
if 'current_event' not in st.session_state: st.session_state.current_event = None
if 'game_result' not in st.session_state: st.session_state.game_result = None
if 'extra_budget' not in st.session_state: st.session_state.extra_budget = 0
if 'event_solved_flag' not in st.session_state: st.session_state.event_solved_flag = False
if 'active_warnings' not in st.session_state: st.session_state.active_warnings = []
if 'event_history' not in st.session_state: st.session_state.event_history = []

# Экономические показатели
if 'inflation' not in st.session_state: st.session_state.inflation = 1.5
if 'trust_score' not in st.session_state: st.session_state.trust_score = 60.0
if 'national_reserves' not in st.session_state: st.session_state.national_reserves = 10.0
if 'unemployment' not in st.session_state: st.session_state.unemployment = 2.5 # База 2.5%
if 'exchange_rate' not in st.session_state: st.session_state.exchange_rate = 1.00 # CHF к EUR

# Внешний фон и Референдумы
if 'global_status' not in st.session_state: st.session_state.global_status = "stable"
if 'last_global_change' not in st.session_state: st.session_state.last_global_change = 0
if 'last_tax_rate' not in st.session_state: st.session_state.last_tax_rate = 30
if 'referendum_active' not in st.session_state: st.session_state.referendum_active = False
if 'referendum_message' not in st.session_state: st.session_state.referendum_message = ""

# --- 3. ДАННЫЕ СОБЫТИЙ ---
BAD_EVENTS = [
    {"title": "🦠 ВСПЫШКА ГРИППА!", "desc": "Больницы переполнены. Соц. обеспечение > 42 млрд!", "condition": lambda s: s['social'] >= 42, "type": "bad", "weight": 5},
    {"title": "👵 ПЕНСИОННЫЙ КРИЗИС!", "desc": "Фонд AHV пуст. Соц. обеспечение > 45 млрд!", "condition": lambda s: s['social'] >= 45, "type": "bad", "weight": 5},
    {"title": "🏥 РОСТ СТРАХОВОК!", "desc": "Население требует субсидий. Соц. обеспечение > 38 млрд!", "condition": lambda s: s['social'] >= 38, "type": "bad", "weight": 4},
    {"title": "🚆 СБОЙ SBB!", "desc": "Поезда встали по всей стране. Транспорт > 18 млрд!", "condition": lambda s: s['transport'] >= 18, "type": "bad", "weight": 4},
    {"title": "❄️ СНЕГ В ГОТТАРДЕ!", "desc": "Тоннель заблокирован. Транспорт > 20 млрд!", "condition": lambda s: s['transport'] >= 20, "type": "bad", "weight": 4},
    {"title": "📉 СИЛЬНЫЙ ФРАНК!", "desc": "Экспорт падает. Поддержите экономику (Гос > 12 млрд)!", "condition": lambda s: s['admin'] >= 12, "type": "bad", "weight": 3},
    {"title": "💻 КИБЕРАТАКА!", "desc": "Взлом федеральных серверов. Гос > 14 млрд!", "condition": lambda s: s['admin'] >= 14, "type": "bad", "weight": 2},
    {"title": "🏦 СКАНДАЛ В БАНКЕ!", "desc": "Спасение Credit Swiss. Гос > 15 млрд!", "condition": lambda s: s['admin'] >= 15, "type": "bad", "weight": 2},
    {"title": "🎓 ЗАБАСТОВКА ETH!", "desc": "Студенты требуют грантов. Образование > 16 млрд!", "condition": lambda s: s['education'] >= 16, "type": "bad", "weight": 3},
    {"title": "🪖 МОДЕРНИЗАЦИЯ АРМИИ!", "desc": "Нужно обновить истребители. Оборона > 12 млрд!", "condition": lambda s: s['security'] >= 12, "type": "bad", "weight": 1},
]

GOOD_EVENTS = [
    {"title": "💉 НАУЧНЫЙ ПРОРЫВ!", "desc": "Наши ученые получили Нобелевку! (+4% доверия)", "effect": "trust", "val": 4, "type": "good"},
    {"title": "🏔️ ТУРИСТИЧЕСКИЙ БУМ!", "desc": "Все едут в Альпы. (+6 млрд в бюджет)", "effect": "money", "val": 6, "type": "good"},
    {"title": "🍫 РЕКОРД ЭКСПОРТА!", "desc": "Сверхприбыль Nestlé и Lindt. (+4 млрд в бюджет)", "effect": "money", "val": 4, "type": "good"},
    {"title": "☮️ ДАВОССКИЙ ФОРУМ!", "desc": "Успешные переговоры. (+5% доверия)", "effect": "trust", "val": 5, "type": "good"},
    {"title": "⌚ ЧАСОВОЙ ГИГАНТ!", "desc": "Rolex заплатил рекордные налоги. (+5 млрд)", "effect": "money", "val": 5, "type": "good"},
]

def get_next_event(event_type):
    pool = BAD_EVENTS if event_type == "bad" else GOOD_EVENTS
    recent_history = st.session_state.event_history[-4:]
    available_events = [e for e in pool if e['title'] not in recent_history]
    if not available_events: available_events = pool

    if event_type == "bad":
        total_weight = sum(evt['weight'] for evt in available_events)
        r = random.uniform(0, total_weight)
        current_weight = 0
        selected = available_events[0]
        for evt in available_events:
            current_weight += evt['weight']
            if r <= current_weight:
                selected = evt
                break
    else:
        selected = random.choice(available_events)
    st.session_state.event_history.append(selected['title'])
    return selected

def start_game():
    st.session_state.game_active = True
    st.session_state.start_time = time.time()
    st.session_state.last_event_time = time.time()
    st.session_state.current_event = None
    st.session_state.game_result = None
    st.session_state.extra_budget = 0
    st.session_state.event_solved_flag = False
    st.session_state.event_history = []
    
    # Сброс показателей
    st.session_state.inflation = 1.0 # Понизил старт до 1% по просьбе
    st.session_state.trust_score = 60.0
    st.session_state.national_reserves = 10.0
    st.session_state.unemployment = 2.5
    st.session_state.exchange_rate = 1.00
    st.session_state.global_status = "stable"
    st.session_state.last_tax_rate = 30

def get_color_for_trust(value):
    if value < 30: return "#e74c3c" 
    if value < 50: return "#e67e22" 
    if value < 75: return "#f1c40f" 
    return "#2ecc71" 

# --- 5. ЭКРАНЫ ИГРЫ ---

if not st.session_state.game_active and st.session_state.game_result is None:
    st.title("🇨🇭 Симулятор Госбюджета: 180 Секунд Власти")
    st.markdown("""
    ### Добро пожаловать. У вас есть 180 секунд.
    
    ---
    **⚡ ВАШИ ИНСТРУМЕНТЫ И РИСКИ:**
    
    1.  **📊 Ставка ЦБ и Валюта:**
        * Высокая ставка = **Сильный франк** (убивает экспорт) + **Рост безработицы**.
        * Низкая ставка = **Слабый франк** (дорогой импорт) + **Рост инфляции**.
    2.  **🗣️ Референдумы:**
        * Не делайте резких движений налогами! Если доверие низкое, народ **заблокирует** ваше решение.
    3.  **📉 Безработица (Кривая Филлипса):**
        * Если сбивать инфляцию слишком жестко, люди потеряют работу. Безработица > 5% = крах доверия.
    4.  **🌍 Внешний мир:**
        * Следите за статусом (сверху). Кризис в Европе ударит по вашему экспорту.
    """)
    if st.button("ПРИНЯТЬ ВЫЗОВ", type="primary", use_container_width=True):
        start_game()
        st.rerun()

elif st.session_state.game_result:
    if st.session_state.game_result == "win":
        st.balloons()
        st.success(f"🏆 ПОБЕДА! Доверие: {int(st.session_state.trust_score)}%. Резервы: {int(st.session_state.national_reserves)} млрд.")
    else:
        st.error(f"💀 ВЫ УВОЛЕНЫ! {st.session_state.fail_reason}")
    if st.button("Играть снова"):
        start_game()
        st.rerun()

else:
    elapsed_time = int(time.time() - st.session_state.start_time)
    time_left = 180 - elapsed_time
    
    # --- 4. МЕХАНИКА: ВНЕШНИЙ ФОН ---
    if time.time() - st.session_state.last_global_change > 40:
        statuses = ["stable", "growth", "recession", "crisis"]
        weights = [0.4, 0.3, 0.2, 0.1]
        st.session_state.global_status = random.choices(statuses, weights)[0]
        st.session_state.last_global_change = time.time()
        st.toast(f"Мировая обстановка изменилась: {st.session_state.global_status.upper()}", icon="🌍")

    # Отображение статуса
    status_map = {
        "stable": ("Стабильность", "Нормальный экспорт", "#ecf0f1"),
        "growth": ("Глобальный рост", "Экспорт растет! (+Доходы)", "#d4edda"),
        "recession": ("Рецессия в ЕС", "Экспорт падает (-Доходы)", "#f8d7da"),
        "crisis": ("Геополитический кризис", "Бегство в франк (Валюта растет резко!)", "#fff3cd")
    }
    curr_status = status_map[st.session_state.global_status]
    st.markdown(f"<div class='global-status' style='background-color:{curr_status[2]}'>🌍 {curr_status[0]}: {curr_status[1]}</div>", unsafe_allow_html=True)

    # --- САЙДБАР (УПРАВЛЕНИЕ) ---
    st.sidebar.markdown("---")
    st.sidebar.header("💰 Доходы (Налоги) и Ставка ЦБ")
    interest_rate = st.sidebar.slider("Ключевая ставка ЦБ (%)", 0.0, 15.0, 1.5, 0.5)
    tax_rate = st.sidebar.slider("Ставка налога (%)", 0, 100, 30, 1)
    
    st.sidebar.markdown("---")
    st.sidebar.header("⚙️ Расходы Бюджета")
    exp_social = st.sidebar.slider("🏥 Соц. обеспечение (Мин. 19)", 0.0, 60.0, 30.0, 0.5)
    exp_education = st.sidebar.slider("🎓 Образование (Мин. 10)", 0.0, 30.0, 10.0, 0.5)
    exp_transport = st.sidebar.slider("🚆 Транспорт (Мин. 10)", 0.0, 30.0, 10.0, 0.5)
    exp_security = st.sidebar.slider("🛡️ Оборона (Мин. 12)", 0.0, 30.0, 12.0, 0.5)
    exp_admin = st.sidebar.slider("🏛️ Госуправление (Мин. 8)", 0.0, 20.0, 8.0, 0.5)
    
    current_stats = {
        'social': exp_social, 'admin': exp_admin, 
        'transport': exp_transport, 'security': exp_security, 
        'education': exp_education
    }
    total_spending = sum(current_stats.values())

    # --- 2. МЕХАНИКА: РЕФЕРЕНДУМЫ ---
    # Проверка резкого изменения налога
    if abs(tax_rate - st.session_state.last_tax_rate) > 15:
        st.session_state.referendum_active = True
        # Если доверие низкое, референдум проваливается
        if st.session_state.trust_score < 50:
            st.session_state.referendum_message = "🚫 НАРОД ЗАБЛОКИРОВАЛ РЕШЕНИЕ! (Низкое доверие)"
            tax_rate = st.session_state.last_tax_rate # Откат
        else:
            st.session_state.referendum_message = "⚠️ РЕФЕРЕНДУМ... ОДОБРЕНО (Доверие позволяет)"
            st.session_state.last_tax_rate = tax_rate
            time.sleep(1.5) # Задержка симуляции
    else:
        st.session_state.referendum_active = False
        st.session_state.last_tax_rate = tax_rate

    # --- РАСЧЕТЫ ЭКОНОМИКИ ---
    trust_change = 0.0
    
    # 1. МЕХАНИКА: КУРС ФРАНКА
    # База 1.00. Ставка выше 1.5% укрепляет, ниже - ослабляет.
    # + Влияние кризиса (все бегут в франк)
    base_exchange_impact = (interest_rate - 1.5) * 0.05
    crisis_impact = 0.15 if st.session_state.global_status == "crisis" else 0
    st.session_state.exchange_rate = 1.00 + base_exchange_impact + crisis_impact
    
    # 3. МЕХАНИКА: БЕЗРАБОТИЦА (Phillips Curve)
    # Высокая ставка и сильный франк (плохой экспорт) растят безработицу
    unemployment_pressure = (interest_rate - 2.0) * 0.02 + (st.session_state.exchange_rate - 1.0) * 0.05
    st.session_state.unemployment += unemployment_pressure * 0.1 # Инерция
    # Естественное стремление к 2.5%
    if st.session_state.unemployment > 2.5: st.session_state.unemployment -= 0.01
    if st.session_state.unemployment < 1.0: st.session_state.unemployment = 1.0
    
    # Влияние Налогов и Инфляции
    if tax_rate < 30:
        trust_change += 0.5 # Приятно платить меньше
        inflation_growth = (30 - tax_rate) * 0.00715
        st.session_state.inflation += inflation_growth
    
    # Влияние Ставки на Инфляцию
    # Если ставка низкая - инфляция растет. Если высокая - падает.
    if interest_rate > 2.0:
        st.session_state.inflation -= (interest_rate - 2.0) * 0.052
    elif interest_rate < 2.0:
        st.session_state.inflation += (2.0 - interest_rate) * 0.0455

    # Влияние Курса на Инфляцию (Слабый франк = дорогой импорт = инфляция)
    if st.session_state.exchange_rate < 0.9:
        st.session_state.inflation += 0.05

    # Инфляция от расходов
    if total_spending > 60:
        st.session_state.inflation += (total_spending - 60) * 0.0026

    # Штрафы за инфляцию и безработицу
    inflation_warning = False
    if st.session_state.inflation > 7.0:
        st.session_state.inflation += 0.2
        trust_change -= (st.session_state.inflation - 7.0) * 0.2
        inflation_warning = True
    
    if st.session_state.unemployment > 5.0:
        trust_change -= (st.session_state.unemployment - 5.0) * 0.5 # Сильный штраф
        
    st.session_state.inflation = max(0, st.session_state.inflation)

    # Логика Бюджета и Щедрости
    st.session_state.active_warnings = []
    if inflation_warning: st.session_state.active_warnings.append(f"🔥 ВЫСОКАЯ ИНФЛЯЦИЯ! ({st.session_state.inflation:.1f}%)")
    if st.session_state.unemployment > 5.0: st.session_state.active_warnings.append(f"📉 БЕЗРАБОТИЦА! ({st.session_state.unemployment:.1f}%)")

    def calculate_budget_impact(value, min_val, warning_text):
        if value < min_val:
            st.session_state.active_warnings.append(warning_text)
            return -random.uniform(0.2, 0.5)
        elif value > min_val + 2.0:
            excess = value - (min_val + 2.0)
            return excess * 0.0075 
        return -0.05

    if exp_social < 19.0:
        trust_change -= random.uniform(0.3, 0.5)
        st.session_state.active_warnings.append(f"🏥 ЭПИДЕМИЯ! (<19)")
    elif exp_social > 22.0: trust_change += (exp_social - 22.0) * 0.0075
    else: trust_change -= 0.05

    trust_change += calculate_budget_impact(exp_transport, 10.0, "🚆 КОЛЛАПС!")
    trust_change += calculate_budget_impact(exp_education, 10.0, "🎓 ЗАБАСТОВКИ!")
    trust_change += calculate_budget_impact(exp_security, 12.0, "🛡️ БУНТ!")
    trust_change += calculate_budget_impact(exp_admin, 8.0, "🏛️ ХАОС!")

    # --- СОБЫТИЯ ---
    time_since_last = time.time() - st.session_state.last_event_time
    if st.session_state.current_event:
        evt = st.session_state.current_event
        if evt['type'] == 'bad':
            is_solved = evt['condition'](current_stats)
            status_msg = "✅ РЕШЕНО!" if is_solved else "❌ КРИЗИС!"
            if is_solved and not st.session_state.event_solved_flag:
                st.session_state.trust_score += random.randint(3, 6)
                st.session_state.event_solved_flag = True
                st.toast("Решено! +Доверие", icon="🚀")
            
            if time_since_last > 15:
                if not is_solved:
                    st.session_state.trust_score -= random.randint(10, 16)
                    st.toast("ПРОВАЛ!", icon="💥")
                st.session_state.current_event = None
                st.session_state.last_event_time = time.time()
                st.session_state.event_solved_flag = False
        elif evt['type'] == 'good':
            if time_since_last > 5:
                st.session_state.current_event = None
                st.session_state.last_event_time = time.time()
                st.session_state.event_solved_flag = False

    elif time_since_last > random.randint(9, 16):
        if random.random() < 0.73:
            st.session_state.current_event = get_next_event("bad")
        else:
            st.session_state.current_event = get_next_event("good")
            ge = st.session_state.current_event
            if ge['effect'] == 'trust': st.session_state.trust_score += ge['val']
            elif ge['effect'] == 'money': 
                st.session_state.national_reserves += ge['val']
                st.toast(f"Бонус: +{ge['val']} млрд", icon="💰")
        st.session_state.last_event_time = time.time()
        st.rerun()

    # --- ФИНАЛЬНЫЙ РАСЧЕТ БЮДЖЕТА ---
    # Доход зависит от налога И от курса валюты (экспорт)
    # Сильный франк (>1.0) снижает доход экспортеров
    export_factor = 1.0 - (st.session_state.exchange_rate - 1.0) * 0.5 
    
    # Влияние внешнего фона
    global_factor = 1.0
    if st.session_state.global_status == "growth": global_factor = 1.1
    elif st.session_state.global_status == "recession": global_factor = 0.85
    
    income_rate = (10 + (tax_rate * 2.5)) * export_factor * global_factor
    balance_rate = income_rate - total_spending
    
    # Долг
    if st.session_state.national_reserves < 0:
        debt_service = abs(st.session_state.national_reserves) * (interest_rate / 100.0) / 5.0
        st.session_state.national_reserves -= debt_service

    st.session_state.national_reserves += balance_rate / 5.0
    
    trust_change -= 0.1 # Энтропия
    st.session_state.trust_score += trust_change
    st.session_state.trust_score = max(min(st.session_state.trust_score, 100), 0)

    # --- GAME OVER ---
    if st.session_state.trust_score < 30:
        st.session_state.game_result = "lose"
        st.session_state.fail_reason = "Революция! Доверие < 30%."
        st.rerun()
    if st.session_state.national_reserves < -50: 
        st.session_state.game_result = "lose"
        st.session_state.fail_reason = "Дефолт! Долг > 50 млрд."
        st.rerun()
    if time_left <= 0:
        st.session_state.final_trust = st.session_state.trust_score
        st.session_state.game_result = "win"
        st.rerun()

    # --- ИНТЕРФЕЙС ---
    if st.session_state.referendum_active:
        st.markdown(f"<div class='referendum-alert'>{st.session_state.referendum_message}</div>", unsafe_allow_html=True)

    c1, c2 = st.columns([1, 2])
    with c1:
        st.markdown(f'<div class="timer-box">🗓 День {elapsed_time*2} / 365</div>', unsafe_allow_html=True)
        unique_warnings = list(set(st.session_state.active_warnings))
        if unique_warnings:
            for w in unique_warnings[:3]: st.markdown(f"<div class='critical-warning'>{w}</div>", unsafe_allow_html=True)

    with c2:
        if st.session_state.current_event:
            evt = st.session_state.current_event
            color_cls = "game-alert-bad" if evt['type'] == 'bad' else "game-alert-good"
            st.markdown(f"""<div class="{color_cls}">
            {evt['title']}<br><span style="font-size:16px">{evt['desc']}</span><br>
            </div>""", unsafe_allow_html=True)
        else:
            st.info("Ситуация стабильная...")

    st.divider()

    # Метрики: 4 Колонки
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        ic = "#e74c3c" if st.session_state.inflation > 7.0 else "#2C3E50"
        st.markdown(f"<div style='text-align:center'>ИНФЛЯЦИЯ</div><div style='text-align:center; font-size:40px; font-weight:bold; color:{ic}'>{st.session_state.inflation:.1f}%</div>", unsafe_allow_html=True)
    with m2:
        uc = "#e74c3c" if st.session_state.unemployment > 5.0 else "#2C3E50"
        st.markdown(f"<div style='text-align:center'>БЕЗРАБОТИЦА</div><div style='text-align:center; font-size:40px; font-weight:bold; color:{uc}'>{st.session_state.unemployment:.1f}%</div>", unsafe_allow_html=True)
    with m3:
        ec = "#27ae60" if st.session_state.exchange_rate > 1.05 else "#2C3E50"
        st.markdown(f"<div style='text-align:center'>КУРС CHF</div><div style='text-align:center; font-size:40px; font-weight:bold; color:{ec}'>{st.session_state.exchange_rate:.2f}</div>", unsafe_allow_html=True)
    with m4:
        tc = get_color_for_trust(st.session_state.trust_score)
        st.markdown(f"<div style='text-align:center'>ДОВЕРИЕ</div><div style='text-align:center; font-size:40px; font-weight:bold; color:{tc}'>{int(st.session_state.trust_score)}%</div>", unsafe_allow_html=True)

    # Резервы и График
    st.divider()
    rc = "normal" if st.session_state.national_reserves >= 0 else "inverse"
    st.metric("Гос. Резервы", f"{st.session_state.national_reserves:.1f} млрд", delta=f"{balance_rate:.1f} / сек", delta_color=rc)
    
    fig_bar = go.Figure(go.Bar(
        x=[total_spending, income_rate],
        y=['Расходы', 'Доходы'],
        orientation='h',
        marker_color=['#c0392b', '#27ae60'],
        text=[f"{total_spending:.1f}", f"{income_rate:.1f}"],
        textposition='auto'
    ))
    fig_bar.update_layout(height=100, margin={"r":0,"t":0,"l":0,"b":0}, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig_bar, use_container_width=True)

    time.sleep(1)
    st.rerun()
