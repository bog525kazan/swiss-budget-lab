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
if 'extra_budget' not in st.session_state: st.session_state.extra_budget = 0
if 'event_solved_flag' not in st.session_state: st.session_state.event_solved_flag = False
if 'active_warnings' not in st.session_state: st.session_state.active_warnings = []
if 'event_history' not in st.session_state: st.session_state.event_history = []

if 'inflation' not in st.session_state: st.session_state.inflation = 1.5
if 'trust_score' not in st.session_state: st.session_state.trust_score = 60.0
if 'national_reserves' not in st.session_state: st.session_state.national_reserves = 10.0

# --- 3. ДАННЫЕ СОБЫТИЙ ---
BAD_EVENTS = [
    {"title": "🦠 ВСПЫШКА ГРИППА!", "desc": "Больницы переполнены. Соц. обеспечение > 42 млрд!", "condition": lambda s: s['social'] >= 42, "type": "bad", "weight": 5},
    {"title": "👵 ПЕНСИОННЫЙ КРИЗИС!", "desc": "Фонд AHV пуст. Соц. обеспечение > 45 млрд!", "condition": lambda s: s['social'] >= 45, "type": "bad", "weight": 5},
    {"title": "🏥 РОСТ СТРАХОВОК!", "desc": "Население требует субсидий. Соц. обеспечение > 38 млрд!", "condition": lambda s: s['social'] >= 38, "type": "bad", "weight": 4},
    {"title": "👶 ДЕФИЦИТ ДЕТСАДОВ!", "desc": "Родители бастуют. Соц. обеспечение > 35 млрд!", "condition": lambda s: s['social'] >= 35, "type": "bad", "weight": 3},
    {"title": "🧪 ДЕФИЦИТ ЛЕКАРСТВ!", "desc": "Сбой поставок. Соц. обеспечение > 40 млрд!", "condition": lambda s: s['social'] >= 40, "type": "bad", "weight": 4},
    {"title": "🚆 СБОЙ SBB!", "desc": "Поезда встали по всей стране. Транспорт > 18 млрд!", "condition": lambda s: s['transport'] >= 18, "type": "bad", "weight": 4},
    {"title": "❄️ СНЕГ В ГОТТАРДЕ!", "desc": "Тоннель заблокирован. Транспорт > 20 млрд!", "condition": lambda s: s['transport'] >= 20, "type": "bad", "weight": 4},
    {"title": "🚧 РЕМОНТ АВТОБАНОВ!", "desc": "Пробки на A1. Транспорт > 16 млрд!", "condition": lambda s: s['transport'] >= 16, "type": "bad", "weight": 3},
    {"title": "✈️ ЗАБАСТОВКА SWISS!", "desc": "Аэропорт Цюриха парализован. Транспорт > 19 млрд!", "condition": lambda s: s['transport'] >= 19, "type": "bad", "weight": 3},
    {"title": "📉 СИЛЬНЫЙ ФРАНК!", "desc": "Экспорт падает. Поддержите экономику (Гос > 12 млрд)!", "condition": lambda s: s['admin'] >= 12, "type": "bad", "weight": 3},
    {"title": "💻 КИБЕРАТАКА!", "desc": "Взлом федеральных серверов. Гос > 14 млрд!", "condition": lambda s: s['admin'] >= 14, "type": "bad", "weight": 2},
    {"title": "🏦 СКАНДАЛ В БАНКЕ!", "desc": "Спасение Credit Swiss. Гос > 15 млрд!", "condition": lambda s: s['admin'] >= 15, "type": "bad", "weight": 2},
    {"title": "🎓 ЗАБАСТОВКА ETH!", "desc": "Студенты требуют грантов. Образование > 16 млрд!", "condition": lambda s: s['education'] >= 16, "type": "bad", "weight": 3},
    {"title": "🧠 УТЕЧКА МОЗГОВ!", "desc": "Ученые уезжают в США. Образование > 18 млрд!", "condition": lambda s: s['education'] >= 18, "type": "bad", "weight": 2},
    {"title": "🪖 МОДЕРНИЗАЦИЯ АРМИИ!", "desc": "Нужно обновить истребители. Оборона > 12 млрд!", "condition": lambda s: s['security'] >= 12, "type": "bad", "weight": 1},
]

GOOD_EVENTS = [
    {"title": "💉 НАУЧНЫЙ ПРОРЫВ!", "desc": "Наши ученые получили Нобелевку! (+4% доверия)", "effect": "trust", "val": 4, "type": "good"},
    {"title": "🏆 ПОБЕДА В ТЕННИСЕ!", "desc": "Национальный герой выиграл турнир! (+3% доверия)", "effect": "trust", "val": 3, "type": "good"},
    {"title": "🏔️ ТУРИСТИЧЕСКИЙ БУМ!", "desc": "Все едут в Альпы. (+6 млрд в бюджет)", "effect": "money", "val": 6, "type": "good"},
    {"title": "🍫 РЕКОРД ЭКСПОРТА!", "desc": "Сверхприбыль Nestlé и Lindt. (+4 млрд в бюджет)", "effect": "money", "val": 4, "type": "good"},
    {"title": "☮️ ДАВОССКИЙ ФОРУМ!", "desc": "Успешные переговоры. (+5% доверия)", "effect": "trust", "val": 5, "type": "good"},
    {"title": "⌚ ЧАСОВОЙ ГИГАНТ!", "desc": "Rolex заплатил рекордные налоги. (+5 млрд)", "effect": "money", "val": 5, "type": "good"},
    {"title": "🔋 ЗЕЛЕНАЯ ЭНЕРГИЯ!", "desc": "Новые ГЭС эффективнее. (+3 млрд)", "effect": "money", "val": 3, "type": "good"},
]

def get_next_event(event_type):
    pool = BAD_EVENTS if event_type == "bad" else GOOD_EVENTS
    recent_history = st.session_state.event_history[-4:]
    available_events = [e for e in pool if e['title'] not in recent_history]
    
    if not available_events:
        available_events = pool

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
    st.session_state.revenue_shock_factor = 1.0
    st.session_state.extra_budget = 0
    st.session_state.event_solved_flag = False
    st.session_state.event_history = []
    st.session_state.inflation = 1.5
    st.session_state.trust_score = 60.0
    st.session_state.national_reserves = 10.0

def get_color_for_trust(value):
    if value < 30: return "#e74c3c" 
    if value < 50: return "#e67e22" 
    if value < 75: return "#f1c40f" 
    return "#2ecc71" 

# --- 5. ЭКРАНЫ ИГРЫ ---

if not st.session_state.game_active and st.session_state.game_result is None:
    st.title("🇨🇭 Симулятор Госбюджета: 180 Секунд Власти")
    st.markdown("""
    ### Добро пожаловать. Вы думаете, управлять государством легко? 
    У вас есть ровно **180 секунд**, чтобы убедиться в обратном.
    
    Вам предстоит на своей шкуре ощутить этот жесткий баланс: когда денег не хватает, кризисы бьют без предупреждения, а население требует заботы.
    
    ---
    **⚡ МЕХАНИКА:**
    1.  **Кубышка (Резервы):** Профицит копится, дефицит тратит резервы. Не уйдите в минус 50 млрд!
    2.  **Налоги:** >30% быстро убивают доверие. <30% растят инфляцию.
    3.  **Щедрость:** Если вы тратите на сферы больше минимума, доверие медленно растет. Но осторожно: большие расходы разгоняют инфляцию!
    4.  **Ставка ЦБ и Инфляция:** Высокая ставка снижает инфляцию, но повышает долги. Инфляция выше 7% начинает снижать доверие!
    """)
    if st.button("ПРИНЯТЬ ВЫЗОВ", type="primary", use_container_width=True):
        start_game()
        st.rerun()

elif st.session_state.game_result:
    if st.session_state.game_result == "win":
        st.balloons()
        st.success(f"🏆 ПОБЕДА! Год завершен успешно. Доверие: {int(st.session_state.trust_score)}%. Резервы: {int(st.session_state.national_reserves)} млрд.")
    else:
        st.error(f"💀 ВЫ УВОЛЕНЫ! {st.session_state.fail_reason}")
    
    if st.button("Играть снова"):
        start_game()
        st.rerun()

else:
    elapsed_time = int(time.time() - st.session_state.start_time)
    time_left = 180 - elapsed_time
    
    if st.session_state.revenue_shock_factor == 1.0 and random.random() < 0.015:
        shock = random.uniform(0.07, 0.10)
        st.session_state.revenue_shock_factor = 1.0 - shock
        st.toast(f"📉 ЧЕРНЫЙ ЛЕБЕДЬ! Доходы упали на {int(shock*100)}%!", icon="🦢")

    # --- САЙДБАР (УПРАВЛЕНИЕ) ---
    st.sidebar.markdown("---")
    st.sidebar.header("💰 Доходы (Налоги) и Ставка ЦБ")
    interest_rate = st.sidebar.slider("Ключевая ставка ЦБ (%)", 0.0, 15.0, 1.5, 0.5)
    tax_rate = st.sidebar.slider("Ставка налога (%)", 0, 100, 30, 1)
    
    st.sidebar.markdown("---")
    st.sidebar.header("⚙️ Расходы Бюджета")
    # Добавлены подсказки с минимумами
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

    # --- ЛОГИКА ДОВЕРИЯ И ИНФЛЯЦИИ ---
    trust_change = 0.0
    
    # 1. Налоги
    high_tax_warning = False
    if tax_rate > 30:
        trust_drop = 0.1 + (tax_rate - 30) * 0.09857
        trust_change -= trust_drop
        high_tax_warning = True
    elif tax_rate < 30:
        trust_change += 0.5 
        # Уменьшено влияние налога на инфляцию на 35%
        inflation_growth = (30 - tax_rate) * 0.00715 
        st.session_state.inflation += inflation_growth
    elif tax_rate == 30:
        pass 

    # 2. Влияние Процентной Ставки
    if interest_rate > 2.0:
        st.session_state.inflation -= (interest_rate - 2.0) * 0.052 # Снижено на 35%
        trust_change -= (interest_rate - 2.0) * 0.05 
    elif interest_rate < 2.0:
        # Уменьшено влияние низкой ставки на инфляцию на 35%
        st.session_state.inflation += (2.0 - interest_rate) * 0.0455

    # 3. Инфляция от расходов
    if total_spending > 60:
        # Уменьшено влияние расходов на инфляцию на 35%
        st.session_state.inflation += (total_spending - 60) * 0.0026

    if st.session_state.inflation > 0.5:
        # Убрали естественное снижение
        pass

    # 4. Инфляция и Доверие (Порог 7%)
    inflation_warning = False
    if st.session_state.inflation > 7.0:
        # Ускоренный рост инфляции, если она уже высокая
        st.session_state.inflation += 0.2
        
        inflation_penalty = (st.session_state.inflation - 7.0) * 0.2
        trust_change -= inflation_penalty
        inflation_warning = True
        
    # 5. ЛОГИКА РАСХОДОВ (ХАЛАТНОСТЬ VS ЩЕДРОСТЬ)
    st.session_state.active_warnings = []
    
    if inflation_warning:
         st.session_state.active_warnings.append(f"🔥 ВЫСОКАЯ ИНФЛЯЦИЯ! ({st.session_state.inflation:.1f}%)")

    def calculate_budget_impact(value, min_val, warning_text):
        if value < min_val:
            st.session_state.active_warnings.append(warning_text)
            return -random.uniform(0.2, 0.5) 
        elif value > min_val + 2.0:
            excess = value - (min_val + 2.0)
            return excess * 0.0075 # Увеличено на 50%
        elif value >= min_val:
             return -0.05
        return 0

    if exp_social < 19.0:
        trust_change -= random.uniform(0.3, 0.5)
        if st.session_state.revenue_shock_factor > 0.6: 
            st.session_state.revenue_shock_factor -= 0.0015
        st.session_state.active_warnings.append(f"🏥 ЭПИДЕМИЯ! (Расходы < 19 млрд)")
    elif exp_social > 22.0: 
        trust_change += (exp_social - 22.0) * 0.0075 # Увеличено на 50%
    else:
        trust_change -= 0.05

    trust_change += calculate_budget_impact(exp_transport, 10.0, "🚆 ТРАНСПОРТНЫЙ КОЛЛАПС!")
    trust_change += calculate_budget_impact(exp_education, 10.0, "🎓 ЗАБАСТОВКИ!")
    trust_change += calculate_budget_impact(exp_security, 12.0, "🛡️ БУНТ АРМИИ!")
    trust_change += calculate_budget_impact(exp_admin, 8.0, "🏛️ ХАОС В МЭРИЯХ!")

    # --- ОБРАБОТКА СОБЫТИЙ ---
    time_since_last = time.time() - st.session_state.last_event_time
    
    if st.session_state.current_event:
        evt = st.session_state.current_event
        if evt['type'] == 'bad':
            is_solved = evt['condition'](current_stats)
            if is_solved:
                status_msg = "✅ РЕШЕНО! ДЕРЖАТЬ ПОЗИЦИИ"
                if not st.session_state.event_solved_flag:
                    bonus = random.randint(3, 6)
                    st.session_state.trust_score += bonus 
                    st.session_state.event_solved_flag = True
                    st.toast(f"Отлично! Доверие +{bonus}%", icon="🚀")
            else:
                status_msg = "❌ КРИЗИС! ПРИМИТЕ МЕРЫ"
            
            if time_since_last > 15: 
                if not is_solved:
                    damage = random.randint(10, 16)
                    st.session_state.trust_score -= damage 
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

    elif time_since_last > random.randint(9, 16):
        if random.random() < 0.73:
            st.session_state.current_event = get_next_event("bad")
            st.session_state.event_solved_flag = False
        else:
            st.session_state.current_event = get_next_event("good")
            st.session_state.event_solved_flag = False
            good_evt = st.session_state.current_event
            if good_evt['effect'] == 'trust':
                st.session_state.trust_score += good_evt['val']
                st.toast(f"Хорошие новости! +{good_evt['val']}%", icon="🎉")
            elif good_evt['effect'] == 'money':
                st.session_state.extra_budget += good_evt['val'] 
                st.session_state.national_reserves += good_evt['val']
                st.toast(f"Прибыль! +{good_evt['val']} млрд в резервы", icon="💰")
        st.session_state.last_event_time = time.time()
        st.rerun()

    # --- ФИНАНСЫ ---
    income_rate = 10 + (tax_rate * 2.5) 
    current_revenue = income_rate * st.session_state.revenue_shock_factor
    balance_rate = current_revenue - total_spending
    
    # Обслуживание долга
    debt_service_cost = 0
    if st.session_state.national_reserves < 0:
        debt_service_cost = abs(st.session_state.national_reserves) * (interest_rate / 100.0) / 5.0 
        st.session_state.national_reserves -= debt_service_cost

    st.session_state.national_reserves += balance_rate / 5.0
    
    # --- ОБНОВЛЕНИЕ ---
    trust_change -= 0.1
    st.session_state.trust_score += trust_change
    st.session_state.trust_score = max(min(st.session_state.trust_score, 100), 0)
    st.session_state.inflation = max(0, st.session_state.inflation) 

    if st.session_state.trust_score < 30:
        st.session_state.game_result = "lose"
        st.session_state.fail_reason = "Революция! Доверие упало ниже 30%."
        st.rerun()
    if st.session_state.national_reserves < -50: 
        st.session_state.game_result = "lose"
        st.session_state.fail_reason = "Дефолт! Долг > 50 млрд."
        st.rerun()
    if time_left <= 0:
        st.session_state.final_trust = st.session_state.trust_score
        st.session_state.game_result = "win"
        st.rerun()

    # --- ОТРИСОВКА ИНТЕРФЕЙСА ---
    c1, c2 = st.columns([1, 2])
    with c1:
        st.markdown(f'<div class="timer-box">🗓 День {elapsed_time*2} / 365</div>', unsafe_allow_html=True)
        # Убираем дубликаты
        unique_warnings = list(set(st.session_state.active_warnings))
        if unique_warnings:
            for w in unique_warnings[:3]: 
                st.markdown(f"<div class='critical-warning'>{w}</div>", unsafe_allow_html=True)
        if high_tax_warning: st.markdown(f"<div class='critical-warning' style='border-color:orange; background:#fef5e7; color:#d35400'>🔥 НАЛОГИ!</div>", unsafe_allow_html=True)
        if debt_service_cost > 0.1: st.markdown(f"<div class='critical-warning' style='border-color:black; background:#ecf0f1; color:black'>💸 ПЛАТА ПО ДОЛГАМ: -{debt_service_cost*5:.1f} млрд/сек</div>", unsafe_allow_html=True)

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

    col_infl, col_trust, col_balance = st.columns([1, 1, 2])
    
    with col_infl:
        st.markdown(f"<div style='text-align:center; color:#7f8c8d; font-size:20px;'>ИНФЛЯЦИЯ</div>", unsafe_allow_html=True)
        ic = "#e74c3c" if st.session_state.inflation > 7.0 else "#2C3E50"
        st.markdown(f"<div style='font-size: 60px; font-weight: bold; text-align: center; color: {ic};'>{st.session_state.inflation:.1f}%</div>", unsafe_allow_html=True)
        if inflation_warning: st.caption("⚠️ ОПАСНОСТЬ!")
        elif tax_rate < 30: st.caption("📈 Растет (Низкий налог)")
        elif total_spending > 80: st.caption("📈 Растет (Высокие расходы)")

    with col_trust:
        trust_color = get_color_for_trust(st.session_state.trust_score)
        st.markdown(f"<div style='text-align:center; color:#7f8c8d; font-size:20px;'>ДОВЕРИЕ</div>", unsafe_allow_html=True)
        st.markdown(f"""
        <div style="font-size: 60px; font-weight: bold; text-align: center; color: {trust_color};">
        {int(st.session_state.trust_score)}%
        </div>
        """, unsafe_allow_html=True)

    with col_balance:
        st.markdown(f"<div style='text-align:center; color:#7f8c8d; font-size:20px;'>РЕЗЕРВЫ (НАКОПЛЕНИЯ)</div>", unsafe_allow_html=True)
        
        reserves_color = "normal" if st.session_state.national_reserves >= 0 else "inverse"
        st.metric("Гос. Кубышка", f"{st.session_state.national_reserves:.1f} млрд", delta=f"{balance_rate:.1f} / сек", delta_color=reserves_color)
        
        fig_bar = go.Figure(go.Bar(
            x=[total_spending, current_revenue],
            y=['Расходы', 'Доходы'],
            orientation='h',
            marker_color=['#c0392b', '#27ae60'],
            text=[f"{total_spending:.1f}", f"{current_revenue:.1f}"],
            textposition='auto'
        ))
        fig_bar.update_layout(height=100, margin={"r":0,"t":0,"l":0,"b":0}, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_bar, use_container_width=True)

    time.sleep(1)
    st.rerun()
