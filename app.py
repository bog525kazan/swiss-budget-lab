import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- 1. НАСТРОЙКА ДИЗАЙНА ---
st.set_page_config(layout="wide", page_title="Swiss Strategy Lab")

st.markdown("""
    <style>
    .main { background-color: #FFFFFF; color: #2C3E50; font-family: 'Helvetica Neue', sans-serif; }
    h1, h2, h3 { color: #003366; }
    
    /* Стили для метрик */
    div[data-testid="stMetricValue"] { color: #0055A6; font-weight: bold; }
    
    /* Слайдеры */
    .stSlider > div[data-baseweb="slider"] > div > div { background-color: #0055A6 !important; }
    
    /* Бейдж для рейтинга */
    .rating-badge {
        padding: 5px 15px;
        border-radius: 5px;
        color: white;
        font-weight: bold;
        text-align: center;
        display: inline-block;
        font-size: 20px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. БОКОВАЯ ПАНЕЛЬ (УПРАВЛЕНИЕ) ---
st.sidebar.header("🇨🇭 Кабинет Министра")
st.sidebar.markdown("---")

# МАКРОЭКОНОМИКА
st.sidebar.subheader("🌍 Макроэкономика")
gdp_growth = st.sidebar.slider("Рост ВВП (%)", -5.0, 5.0, 1.2, 0.1)
inflation = st.sidebar.slider("Уровень инфляции (%)", 0.0, 15.0, 1.5, 0.1)
revenue_base = st.sidebar.slider("Базовые доходы (млрд CHF)", 60.0, 100.0, 82.0, 0.5)

st.sidebar.markdown("---")

# РАСПРЕДЕЛЕНИЕ БЮДЖЕТА
st.sidebar.subheader("💰 Структура расходов (млрд)")
exp_social = st.sidebar.slider("🏥 Соц. обеспечение", 10.0, 50.0, 30.0, 0.5)
exp_education = st.sidebar.slider("🎓 Образование и Наука", 5.0, 20.0, 10.0, 0.5)
exp_transport = st.sidebar.slider("🚆 Транспорт/Инфраструктура", 5.0, 20.0, 10.0, 0.5)
exp_security = st.sidebar.slider("🛡️ Безопасность/Оборона", 1.0, 20.0, 6.0, 0.5)
exp_admin = st.sidebar.slider("🏛️ Госуправление", 1.0, 15.0, 5.0, 0.5)

st.sidebar.markdown("---")
st.sidebar.subheader("⚡ События")
event_crisis = st.sidebar.button("💥 Банковский кризис (+20 млрд)")
event_tax_cut = st.sidebar.button("🗳 Референдум: -Налоги (-5 млрд)")

# --- 3. РАСЧЕТНАЯ МОДЕЛЬ (Backend) ---

revenue = revenue_base * (1 + inflation / 200) 
total_spending_program = (exp_social + exp_education + exp_transport + exp_security + exp_admin) * (1 + inflation / 100)

if event_crisis: total_spending_program += 20
if event_tax_cut: revenue -= 5

k_factor = 1 + (1.8 - gdp_growth) * 0.1
spending_ceiling = revenue * k_factor

pre_balance = revenue - total_spending_program
debt_base = 120
projected_debt = debt_base - pre_balance 
debt_to_gdp_proxy = (projected_debt / 800) * 100 

rating = "AAA"
rating_color = "#27ae60"
interest_rate = 1.0

if debt_to_gdp_proxy > 20 or pre_balance < -5:
    rating = "AA"; rating_color = "#f1c40f"; interest_rate = 2.5
if debt_to_gdp_proxy > 30 or pre_balance < -10:
    rating = "A"; rating_color = "#e67e22"; interest_rate = 4.5
if debt_to_gdp_proxy > 40 or pre_balance < -15:
    rating = "BBB"; rating_color = "#c0392b"; interest_rate = 7.0

debt_service = projected_debt * (interest_rate / 100)
total_spending_final = total_spending_program + debt_service
final_balance = revenue - total_spending_final

# Логика ДОВЕРИЯ (Popularity)
trust = 75 
if exp_social > 32: trust += 10
elif exp_social < 25: trust -= 20
if exp_security > 10 and gdp_growth > 0: trust -= 10 
if inflation > 3.5: trust -= (inflation - 3.5) * 6
if exp_admin > 8: trust -= 5 
if final_balance < -5: trust -= 10
if rating != "AAA": trust -= 15 

trust = max(min(int(trust), 100), 0)

# --- 4. ГЛАВНЫЙ ЭКРАН ---
st.title("🇨🇭 Бюджетная Лаборатория: Управление и Карта Доверия")
st.markdown("---")

# МЕТРИКИ + КАРТА (ВЕРХНИЙ РЯД)
col_metrics, col_map = st.columns([3,2])

with col_metrics:
    m1, m2 = st.columns(2)
    m1.metric("Баланс Бюджета", f"{final_balance:.2f} млрд", delta=f"Инфл: {inflation}%", delta_color="normal" if final_balance>=0 else "inverse")
    m2.metric("Общий Госдолг", f"{projected_debt:.1f} млрд", delta=f"-% Обслуж: {debt_service:.2f}", delta_color="inverse")
    
    m3, m4 = st.columns(2)
    with m3:
        st.markdown("**Рейтинг S&P**")
        st.markdown(f'<div class="rating-badge" style="background-color: {rating_color};">{rating}</div>', unsafe_allow_html=True)
    with m4:
        st.metric("Долг на душу (CHF)", f"{int((projected_debt*1000)/9):,}")

with col_map:
    # --- ВИЗУАЛИЗАЦИЯ КАРТЫ ШВЕЙЦАРИИ ---
    # Создаем фиктивный датафрейм для отрисовки страны
    swiss_map_data = pd.DataFrame({'Country': ['Switzerland'], 'Trust': [trust]})
    
    fig_map = go.Figure(go.Choropleth(
        locations=['CHE'],
        z=[trust],
        locationmode='ISO-3',
        colorscale='RdYlGn', # Red-Yellow-Green
        zmin=0, zmax=100,
        showscale=False,
        marker_line_color='white',
        marker_line_width=2,
    ))
    
    # Настройка камеры и аннотации (цифры на карте)
    fig_map.update_geos(
        visible=False, resolution=50,
        scope='europe',
        center=dict(lat=46.8, lon=8.2), # Центр Швейцарии
        projection_scale=12 # Зум на страну
    )
    
    fig_map.update_layout(
        height=300,
        margin={"r":0,"t":0,"l":0,"b":0},
        annotations=[dict(
            x=0.5, y=0.5, xref='paper', yref='paper',
            text=f"<b>{trust}%</b>",
            showarrow=False,
            font=dict(size=40, color="black" if 30 < trust < 70 else "white")
        )]
    )
    st.plotly_chart(fig_map, use_container_width=True)

# --- 5. ВИЗУАЛИЗАЦИЯ (ГРАФИКИ) ---
st.markdown("---")
g1, g2 = st.columns([1, 1])

with g1:
    st.subheader("📊 Распределение ресурсов")
    labels = ['Социалка', 'Образование', 'Транспорт', 'Оборона', 'Управление', 'Долг']
    values = [exp_social, exp_education, exp_transport, exp_security, exp_admin, debt_service]
    fig_pie = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.4, marker_colors=['#3498db', '#9b59b6', '#1abc9c', '#e74c3c', '#95a5a6', '#f39c12'])])
    fig_pie.update_layout(margin=dict(t=0, b=0, l=0, r=0), height=300)
    st.plotly_chart(fig_pie, use_container_width=True)

with g2:
    st.subheader("⚖️ Анализ «Долгового тормоза»")
    is_compliant = total_spending_final <= spending_ceiling
    fig_bar = go.Figure(go.Bar(
        x=['Доходы', 'Лимит', 'Траты'],
        y=[revenue, spending_ceiling, total_spending_final],
        marker_color=['#0055A6', '#bdc3c7', '#e74c3c' if not is_compliant else '#27ae60'],
        text=[f"{revenue:.1f}", f"{spending_ceiling:.1f}", f"{total_spending_final:.1f}"],
        textposition='auto'
    ))
    fig_bar.update_layout(margin=dict(t=0, b=0, l=0, r=0), height=300)
    st.plotly_chart(fig_bar, use_container_width=True)

# --- 6. ПРОГНОЗ И ВЕРДИКТ ---
st.subheader("📉 Прогноз динамики госдолга")
years = [2025, 2026, 2027, 2028, 2029]
debt_trend = []
curr_debt = projected_debt
for _ in years:
    curr_debt -= final_balance
    debt_trend.append(curr_debt)

fig_line = go.Figure(go.Scatter(x=years, y=debt_trend, mode='lines+markers', line=dict(color='#2C3E50', width=3), fill='tozeroy'))
fig_line.update_layout(height=250, margin=dict(t=10, b=10, l=0, r=0))
st.plotly_chart(fig_line, use_container_width=True)

# Финальный вердикт
if rating != "AAA":
    st.error(f"🚨 **КРИЗИС:** Рейтинг {rating}. Инвесторы требуют повышенный процент. Доверие падает.")
elif trust < 45:
    st.warning("⚠️ **НАПРЯЖЕННОСТЬ:** Низкое доверие (красная карта). Риск массовых референдумов против правительства.")
elif is_compliant and trust > 65:
    st.success("✅ **СТАБИЛЬНОСТЬ:** Вы соблюдаете закон и сохраняете народную поддержку. Карта в зеленой зоне.")