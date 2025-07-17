import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import datetime
import numpy as np
from dateutil.relativedelta import relativedelta

# --- 상수 정의 ---
DEFAULT_PER_CAPITA_WATER_USAGE = 305  # L/일
ENERGY_PER_CUBIC_METER_WATER_SUPPLY = 0.5  # kWh/m³
ENERGY_TO_HEAT_1L_WATER = 0.029  # kWh/L
CO2_PER_KWH = 0.4  # kg CO2/kWh
CO2_ABSORBED_PER_TREE_PER_YEAR = 21  # kg CO2/년

BASE_COST_PER_KWH = {"저압": [78.3, 147.3, 215.6]}
TIER_THRESHOLDS = [200, 400]
VAT_RATE = 0.1
ELECTRICITY_FUND_RATE = 0.037

# --- CO2 배출량 설정 (한국 기준, gCO2eq/kWh) ---
# 출처: Low-Carbon Power Data (2024년 기준 약 409 gCO2eq/kWh)
CO2_EMISSION_FACTOR_G_PER_KWH = 409

# --- 함수 정의 ---
def calculate_monthly_bill(kwh_usage, contract_type="저압"):
    tier_costs = BASE_COST_PER_KWH[contract_type]
    tier_thresholds = TIER_THRESHOLDS
    energy_charge = 0

    if kwh_usage <= tier_thresholds[0]:
        energy_charge += kwh_usage * tier_costs[0]
    elif kwh_usage <= tier_thresholds[1]:
        energy_charge += (tier_thresholds[0] * tier_costs[0])
        energy_charge += ((kwh_usage - tier_thresholds[0]) * tier_costs[1])
    else:
        energy_charge += (tier_thresholds[0] * tier_costs[0])
        energy_charge += ((tier_thresholds[1] - tier_thresholds[0]) * tier_costs[1])
        energy_charge += ((kwh_usage - tier_thresholds[1]) * tier_costs[2])

    base_fee = 0
    electricity_fund = energy_charge * ELECTRICITY_FUND_RATE
    vat = (energy_charge + electricity_fund) * VAT_RATE
    total_bill = base_fee + energy_charge + electricity_fund + vat

    return total_bill, energy_charge, electricity_fund, vat

def count_months(start_date, end_date):
    return (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month) + 1

# --- UI ---
st.set_page_config(layout="wide")
st.title("🌱 지속가능성 수치 시뮬레이터")

# --- 전기 절약 분석기 ---
st.header("💡 전기 절약 분석기")
col_date1, col_date2 = st.columns(2)
with col_date1:
    start_date = st.date_input("시작일", datetime.date.today().replace(day=1))
with col_date2:
    end_date = st.date_input("종료일", datetime.date.today() + datetime.timedelta(days=365))

if start_date > end_date:
    st.error("❌ 종료일은 시작일보다 앞설 수 없습니다.")
    st.stop()

col1, col2 = st.columns(2)
with col1:
    usage_before = st.number_input("절약 전 월 사용량 (kWh)", min_value=1.0, value=400.0, step=1.0)
with col2:
    usage_after = st.number_input("절약 후 월 사용량 (kWh)", min_value=0.0, value=300.0, step=1.0)

if usage_after > usage_before:
    st.error("절약 후 사용량이 절약 전보다 많습니다.")
    st.stop()

if st.button("전기 절약 분석하기"):
    num_months = count_months(start_date, end_date)
    saved_kwh_per_month = usage_before - usage_after
    total_saved_kwh = saved_kwh_per_month * num_months
    saved_percent = (saved_kwh_per_month / usage_before) * 100

    original_bill, _, _, _ = calculate_monthly_bill(usage_before)
    reduced_bill, _, _, _ = calculate_monthly_bill(usage_after)

    saved_won_per_month = original_bill - reduced_bill
    total_saved_won = saved_won_per_month * num_months
    
    # CO2 배출량 계산
    co2_before_kg = (usage_before * CO2_EMISSION_FACTOR_G_PER_KWH * num_months) / 1000
    co2_after_kg = (usage_after * CO2_EMISSION_FACTOR_G_PER_KWH * num_months) / 1000
    total_co2_saved_kg = co2_before_kg - co2_after_kg
    

    st.metric("총 절약한 전력량", f"{total_saved_kwh:.2f} kWh")
    st.metric("절약률 (월 기준)", f"{saved_percent:.2f}%")
    st.metric("총 절약한 금액", f"{total_saved_won:,.0f} 원")

    st.subheader("🌳 이산화탄소 배출량 분석")
    st.metric("총 감축한 이산화탄소 배출량", f"{total_co2_saved_kg:,.2f} kg CO2e")
    st.markdown(f"- 절약 전 총 이산화탄소 배출량: **{co2_before_kg:,.2f} kg CO2e**")
    st.markdown(f"- 절약 후 총 이산화탄소 배출량: **{co2_after_kg:,.2f} kg CO2e**")

st.divider()

# --- 재활용률 평가 시스템 ---
st.header("♻️ 재활용률 평가 시스템")
NATIONAL_RATE = 69.8
st.markdown(f"**전국 평균 재활용률: {NATIONAL_RATE}%**")

waste_amount = st.number_input("총 폐기물량 (톤)", 0.0, value=1000.0, step=1.0)
recycling_amount = st.number_input("재활용량 (톤)", 0.0, waste_amount, 300.0, step=1.0)

if waste_amount > 0:
    recycling_rate = (recycling_amount / waste_amount) * 100
    relative_rate = (recycling_rate / NATIONAL_RATE) * 100

    def get_grade(rate):
        if rate < 50: return "낮음", "🔴", "#ff4444"
        elif rate < 75: return "보통", "🟡", "#ffaa00"
        elif rate < 100: return "높음", "🟢", "#00aa00"
        else: return "매우 높음", "🔵", "#0066cc"

    grade, emoji, color = get_grade(relative_rate)

    st.metric("현재 재활용률", f"{recycling_rate:.1f}%")
    st.metric("전국 평균 대비", f"{relative_rate:.1f}%")
    st.metric("평가 등급", f"{emoji} {grade}")

    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=relative_rate,
        delta={'reference':100},
        gauge={
            'axis': {'range': [None, 200]},
            'bar': {'color': color},
            'steps': [
                {'range': [0, 50], 'color': "lightgray"},
                {'range': [50, 100], 'color': "gray"},
                {'range': [100, 150], 'color': "lightgreen"},
                {'range': [150, 200], 'color': "green"}
            ],
            'threshold': {'line': {'color': "red", 'width': 4}, 'value': 100}
        }
    ))
    fig_gauge.update_layout(height=300)
    st.plotly_chart(fig_gauge, use_container_width=True)

st.divider()

# --- 물 절약 효과 시뮬레이터 ---
st.header("💧 물 절약 효과 시뮬레이터")
user_daily_water_usage = st.slider(
    "하루에 물을 몇 리터 사용하시나요?",
    min_value=0,
    max_value=500,
    value=100,
    step=10
)

daily_saving = DEFAULT_PER_CAPITA_WATER_USAGE - user_daily_water_usage
annual_saving_liters = daily_saving * 365

if daily_saving > 0:
    hot_water_saving_liters = annual_saving_liters * 0.40
    cold_water_supply_saving_cubic_meters = (annual_saving_liters * 0.60) / 1000

    energy_saved_from_hot_water = hot_water_saving_liters * ENERGY_TO_HEAT_1L_WATER
    energy_saved_from_cold_supply = cold_water_supply_saving_cubic_meters * ENERGY_PER_CUBIC_METER_WATER_SUPPLY
    total_energy_saved_kwh = energy_saved_from_hot_water + energy_saved_from_cold_supply

    co2_reduced_kg = total_energy_saved_kwh * CO2_PER_KWH
    equivalent_trees = co2_reduced_kg / CO2_ABSORBED_PER_TREE_PER_YEAR

    st.metric("연간 예상 물 절약량", f"{annual_saving_liters:,.0f} L")
    st.metric("절약된 에너지 (연간)", f"{total_energy_saved_kwh:,.2f} kWh")
    st.metric("감소된 탄소 배출량 (연간)", f"{co2_reduced_kg:,.2f} kg CO2")
    st.metric("나무 심는 효과", f"약 {equivalent_trees:,.1f} 그루")
else:
    st.info("평균 사용량보다 적게 사용해보세요.")

st.divider()

# --- 탄소 발자국 시뮬레이터 ---
st.header("🌍 탄소 발자국 시뮬레이터")
mode = st.radio("이동 수단을 선택하세요:", ["자동차", "버스", "지하철", "자전거/도보"])
distance = st.number_input("일일 이동 거리 (왕복, km)", min_value=0.0, value=10.0, step=0.1)

emission_factors = {
    "자동차": 0.170,
    "버스": 0.093,
    "지하철": 0.091,
    "자전거/도보": 0.056,
}

daily_co2 = emission_factors[mode] * distance
annual_co2 = daily_co2 * 365

st.metric("💨 선택 수단의 일일 탄소 배출량", f"{daily_co2:,.1f}g CO₂e")
st.metric("💨 선택 수단의 연간 탄소 배출량", f"{annual_co2:,.1f}kg CO₂e")

mode = st.radio("페기물 처리 방법을 선택하세요:", ["전면 분리수거", "부분 혼합 수거"])

emission = {
    "전면 분리수거": 203,
    "부분 혼합 수거": 193,
}

tresh_co2 = emission[mode]

# --- 한국 1인 평균 대비 총 탄소 배출량 비교 ---

# 한국 1인 평균 연간 CO2 배출량 (14톤 = 14,000 kg)
World_AVERAGE_CO2_KG = 4_800
water_co2_total= user_daily_water_usage * 0.01

# 총합 (각 시뮬레이터에서 나온 값 합산)
total_co2_electricity = co2_after_kg if 'co2_after_kg' in locals() else 0
total_co2_water = water_co2_total if 'co2_reduced_kg' in locals() else 0
total_co2_transport = annual_co2 if 'annual_co2' in locals() else 0

st.divider()

add_fixed_emission = st.toggle("고정 배출량 1300kg CO₂e 포함하기", value=True)
fixed_emission_value = 1300 if add_fixed_emission else 0

# 재활용은 CO2 절감량 반영 불가, 또는 추정하여 추가 가능
# 여기서는 재활용 제외 (원하면 추정 절감량 추가 가능)
total_annual_co2_kg = total_co2_electricity + total_co2_water + total_co2_transport + tresh_co2 + fixed_emission_value

# 세계 평균과 비교
delta_kg = World_AVERAGE_CO2_KG - total_annual_co2_kg

# --- 탄소 결산 버튼 및 결과 출력 ---
st.header("🐧 탄소 결산")

if st.button("탄소 결산 보기"):
    st.subheader("세계 평균 대비 연간 탄소 배출량 비교")
    st.metric("총 연간 탄소 배출량", f"{total_annual_co2_kg:,.0f} kg CO₂e")

    if delta_kg > 0:
        st.success(f"세계 평균보다 약 {delta_kg:,.0f} kg CO₂e 절감하고 있습니다!")
    else:
        st.warning(f"세계 평균보다 약 {abs(delta_kg):,.0f} kg CO₂e 더 배출하고 있습니다.")

    # 펭귄 살리기 계산
    CO2_SAVING_PER_PENGUIN_KG = 100
    penguins_saved = max(delta_kg, 0) / CO2_SAVING_PER_PENGUIN_KG

    st.subheader("🐧 펭귄 살리기 효과")
    st.metric("살린 펭귄 수 추정", f"{delta_kg / 5000:.1f} 마리")
    
    st.markdown("※ 추정값으로, CO₂ 감축이 생태계 보호에 기여하는 간접적 효과를 상징적으로 환산한 것입니다.")


# --- 펭귄 이미지 출력 ---
from PIL import Image

penguins_saved = delta_kg / 5000

# 이미지 불러오기
penguin_img = Image.open("C:/Users/user/Desktop/streamlit/penguin.jpg")

# 펭귄 수만큼 이미지 출력
if st.button("🐧 펭귄 살린 만큼 보기"):
    if penguins_saved > 0:
        full_penguins = int(penguins_saved)
        partial_penguin_fraction = penguins_saved - full_penguins

        cols = st.columns(5)  # 한 줄에 5마리씩
        for idx in range(full_penguins):
            with cols[idx % 5]:
                st.image(penguin_img, width=300)

        if partial_penguin_fraction > 0:
            # 펭귄 이미지 일부만 보여주기
            partial_height = int(penguin_img.height * partial_penguin_fraction)
            cropped_img = penguin_img.crop((0, 0, penguin_img.width, partial_height))
            with cols[(full_penguins) % 5]:
                st.image(cropped_img, width=300)

        st.caption(f"총 {penguins_saved:.1f} 마리 펭귄")
    else:
        st.info("아직 살린 펭귄이 없습니다. 탄소를 더 절감해보세요!")