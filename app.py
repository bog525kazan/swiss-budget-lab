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
if 'negligence_recovery' not in st.session_state:
    st.session_state.negligence_recovery = 0 
# НОВОЕ: История событий для уникальности
if 'event_history' not in st.session_state:
    st.session_state.event_history = []

# --- 3. ДАННЫЕ СОБЫТИЙ ---
BAD_EVENTS = [
    # Социалка (Частые, вес высокий)
    {"title": "🦠 ВСПЫШКА ГРИППА!", "desc": "Больницы переполнены. Соц. обеспечение > 42 млрд!", "condition": lambda s: s['social'] >= 42, "type": "bad", "weight": 5},
    {"title": "👵 ПЕНСИОННЫЙ КРИЗИС!", "desc": "Фонд AHV пуст. Соц. обеспечение > 45 млрд!", "condition": lambda s: s['social'] >= 45, "type": "bad", "weight": 5},
    {"title": "🏥 РОСТ СТРАХОВОК!", "desc": "Население требует субсидий. Соц. обеспечение > 38 млрд!", "condition": lambda s: s['social'] >= 38, "type": "bad", "weight": 4},
    {"title": "👶 ДЕФИЦИТ ДЕТСАДОВ!", "desc": "Родители бастуют. Соц. обеспечение > 35 млрд!", "condition": lambda s: s['social'] >= 35, "type": "bad", "weight": 3},
    {"title": "🧪 ДЕФИЦИТ ЛЕКАРСТВ!", "desc": "Сбой поставок. Соц. обеспечение > 40 млрд!", "condition": lambda s: s['social'] >= 40, "type": "bad", "weight": 4},

    # Транспорт (Частые, вес высокий)
    {"title": "🚆 СБОЙ SBB!", "desc": "Поезда встали по всей стране. Транспорт > 18 млрд!", "condition": lambda s: s['transport'] >= 18, "type": "bad", "weight": 4},
    {"title": "❄️ СНЕГ В ГОТТАРДЕ!", "desc": "Тоннель заблокирован. Транспорт > 20 млрд!", "condition": lambda s: s['transport'] >= 20, "type": "bad", "weight": 4},
    {"title": "🚧 РЕМОНТ АВТОБАНОВ!", "desc": "Пробки на A1. Транспорт > 16 млрд!", "condition": lambda s: s['transport'] >= 16, "type": "bad", "weight": 3},
    {"title": "✈️ ЗАБАСТОВКА SWISS!", "desc": "Аэропорт Цюриха парализован. Транспорт > 19 млрд!", "condition": lambda s: s['transport'] >= 19, "type": "bad", "weight": 3},
    
    # Госуправление / Экономика
    {"title": "📉 СИЛЬНЫЙ ФРАНК!", "desc": "Экспорт падает. Поддержите экономику (Гос > 12 млрд)!", "condition": lambda s: s['admin'] >= 12, "type": "bad", "weight": 3},
    {"title": "💻 КИБЕРАТАКА!", "desc": "Взлом федеральных серверов. Гос > 14 млрд!", "condition": lambda s: s['admin'] >= 14, "type": "bad", "weight": 2},
    {"title": "🏦 СКАНДАЛ В БАНКЕ!", "desc": "Спасение Credit Swiss. Гос > 15 млрд!", "condition": lambda s: s['admin'] >= 15, "type": "bad", "weight": 2},
    
    # Образование
    {"title": "🎓 ЗАБАСТОВКА ETH!", "desc": "Студенты требуют грантов. Образование > 16 млрд!", "condition": lambda s: s['education'] >= 16, "type": "bad", "weight": 3},
    {"title": "🧠 УТЕЧКА МОЗГОВ!", "desc": "Ученые уезжают в США. Образование > 18 млрд!", "condition": lambda s: s['education'] >= 18, "type": "bad", "weight": 2},

    # Оборона (Редкие - маленький вес)
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

# Функция выбора события с учетом истории и весов
def get_next_event(event_type):
    # 1. Выбираем пул событий
    pool = BAD_EVENTS if event_type == "bad" else GOOD_EVENTS
    
    # 2. Фильтруем: исключаем те, что были в последних 4 ходах
    recent_history = st.session_state.event_history[-4:]
    available_events = [e for e in pool if e['title'] not in recent_history]
    
    # Если вдруг все доступные события закончились (редко, но бывает), берем весь пул
    if not available_events:
        available_events = pool

    # 3. Выбираем из доступных
    if event_type == "bad":
        # Для плохих используем веса
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
        # Для хороших - просто рандом
        selected = random.choice(available_events)
    
    # 4. Записываем в историю
    st.session_state.event_history.append(selected['title'])
    return selected

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
    st.session_state.negligence_recovery = 0
    st.session_state.event_history = [] # Очищаем историю

def get_color_for_trust(value):
    if value < 30: return "#e74c3c" 
    if value < 50: return "#e67e22" 
    if value < 75: return "#f1c40f" 
    return "#2ecc71" 

# --- 5. ЭКРАНЫ ИГРЫ ---

# 5.1 Стартовый экран
if not st.session_state.game_active and st.session_state.game_result is None:
    st.title("🇨🇭 Симулятор Госбюджета: 180 Секунд Власти")
    st.markdown("""
    ### Добро пожаловать. Вы думаете, управлять государством легко? 
    У вас есть ровно **180 секунд**, чтобы убедиться в обратном.
    
    Вам предстоит на своей шкуре ощутить этот жесткий баланс: когда денег не хватает, кризисы бьют без предупреждения, а население требует заботы. Любое ваше решение имеет цену. Попробуйте удержать страну от краха и сохранить доверие людей.
    
    ---
    **⚡ ВНИМАНИЕ! Правила безопасности:**
    Нельзя просто так урезать бюджет. За критически низкие расходы будут последствия:
    
    * 🏥 **Медицина < 19 млрд:** **ДВОЙНОЙ УДАР!** Падает доверие И падают доходы (люди не работают).
    * 🚆 **Транспорт < 10 млрд:** Коллапс логистики.
    * 🎓 **Образование < 10 млрд:** Забастовки.
    * 🛡️ **Оборона < 12 млрд:** Проблемы с безопасностью (редко, но метко).
    """)
    if st.button("ПРИНЯТЬ ВЫЗОВ", type="primary", use_container_width=True):
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
    exp_transport = st.sidebar.slider("🚆 Транспорт (Мин. 10)", 0.0, 30.0, 10.0, 0.5)
    exp_security = st.sidebar.slider("🛡️ Оборона (Мин. 12)", 0.0, 30.0, 12.0, 0.5)
    exp_admin = st.sidebar.slider("🏛️ Госуправление (Мин. 8)", 0.0, 20.0, 8.0, 0.5)
    
    current_stats = {
        'social': exp_social, 'admin': exp_admin, 
        'transport': exp_transport, 'security': exp_security, 
        'education': exp_education
    }

    # --- ЛОГИКА "ХАЛАТНОСТИ" (С восстановлением) ---
    st.session_state.active_warnings = []
    current_penalty_increment = 0
    is_negligent = False
    
    # 1. Медицина (< 19.0)
    if exp_social < 19.0:
        current_penalty_increment += random.uniform(0.3, 0.5)
        if st.session_state.revenue_shock_factor > 0.6: 
            st.session_state.revenue_shock_factor -= 0.0015
        st.session_state.active_warnings.append(f"🏥 ЭПИДЕМИЯ! (Расходы < 19 млрд)")
        is_negligent = True

    # 2. Транспорт (< 10.0)
    if exp_transport < 10.0:
        current_penalty_increment += random.uniform(0.2, 0.4)
        st.session_state.active_warnings.append(f"🚆 ТРАНСПОРТНЫЙ КОЛЛАПС! (Расходы < 10 млрд)")
        is_negligent = True

    # 3. Образование (< 10.0)
    if exp_education < 10.0:
        current_penalty_increment += random.uniform(0.2, 0.4)
        st.session_state.active_warnings.append(f"🎓 ЗАБАСТОВКИ! (Расходы < 10 млрд)")
        is_negligent = True

    # 4. Оборона (< 12.0)
    if exp_security < 12.0:
        current_penalty_increment += random.uniform(0.5, 0.8)
        st.session_state.active_warnings.append(f"🛡️ РАЗВАЛ АРМИИ! (Расходы < 12 млрд)")
        is_negligent = True

    # 5. Госуправление (< 8.0)
    if exp_admin < 8.0:
        current_penalty_increment += random.uniform(0.2, 0.3)
        st.session_state.active_warnings.append(f"🏛️ ХАОС В МЭРИЯХ! (Расходы < 8 млрд)")
        is_negligent = True

    # Применение штрафа или восстановление
    if is_negligent:
        st.session_state.penalties += current_penalty_increment
    else:
        if st.session_state.penalties > 0:
            recovery_rate = 0.15 
            st.session_state.penalties = max(0, st.session_state.penalties - recovery_rate)

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
            # Используем новую функцию с проверкой уникальности
            st.session_state.current_event = get_next_event("bad")
            st.session_state.event_solved_flag = False
        else:
            st.session_state.current_event = get_next_event("good")
            st.session_state.event_solved_flag = False
            
            good_evt = st.session_state.current_event
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
