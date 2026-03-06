import streamlit as st
import math

# --- 1. ページ構成 ---
st.set_page_config(page_title="繊維実務：自動原価計算ツール", page_icon="📊", layout="wide")

# カスタムCSS
st.markdown("""
    <style>
    .stMetric { background-color: #ffffff; border: 1px solid #eee; padding: 15px; border-radius: 10px; }
    .main { background-color: #f8f9fa; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. サイドバー（基本設定） ---
with st.sidebar:
    st.title("⚙️ 基本設定")
    case_weight = st.number_input("1ケースの重量 (kg)", value=22.68, step=0.01)
    loss_rate_percent = st.slider("設定ロス率 (%)", 0.0, 10.0, 2.0, step=0.1)
    loss_rate = 1 + (loss_rate_percent / 100)
    st.divider()
    st.caption("実務用シミュレーター v4.0")

# --- 3. メイン画面 ---
st.title("📊 生機原価自動シミュレーター")
st.write("必要項目を入力すると、リアルタイムで原価を算出します。")

# --- 入力セクション ---
col_order_1, col_order_2, col_order_3 = st.columns(3)
with col_order_1:
    num_rolls = st.number_input("発注反数 (反)", min_value=1, value=15)
with col_order_2:
    weight_per_roll = st.number_input("1反あたりの重量 (kg)", min_value=0.1, value=10.0, step=0.1)
with col_order_3:
    knitting_fee = st.number_input("編賃単価 (円/kg)", min_value=0, value=200)

total_raw_weight = num_rolls * weight_per_roll

st.divider()

st.subheader("🧵 使用糸の設定")
# 糸の数を動的に変更
num_yarns = st.radio("糸の種類数", [1, 2, 3], horizontal=True)

yarn_data = []
y_cols = st.columns(num_yarns)

for i in range(num_yarns):
    with y_cols[i]:
        st.markdown(f"**糸 {i+1}**")
        name = st.text_input(f"素材名 {i+1}", value=f"素材{chr(65+i)}", key=f"name_{i}")
        percentage = st.number_input(f"混率 {i+1} (%)", min_value=0, max_value=100, value=100//num_yarns, key=f"p_{i}")
        price = st.number_input(f"糸単価 {i+1} (円/kg)", min_value=0, value=1000, key=f"pr_{i}")
        yarn_data.append({"name": name, "p": percentage, "price": price})

# 混率チェック
total_p = sum(y['p'] for y in yarn_data)
if total_p != 100:
    st.warning(f"⚠️ 混率の合計が {total_p}% です。100%になるよう調整してください。")

st.divider()

# --- 計算ロジック ---
if total_p == 100:
    total_yarn_cost = 0
    calculation_details = []

    for y in yarn_data:
        net_required = total_raw_weight * (y['p'] / 100) * loss_rate
        cases = math.ceil(net_required / case_weight)
        purchase_weight = cases * case_weight
        cost = purchase_weight * y['price']
        total_yarn_cost += cost
        calculation_details.append({
            "name": y['name'],
            "net": net_required,
            "cases": cases,
            "buy_kg": purchase_weight,
            "cost": cost
        })

    total_knitting_cost = total_raw_weight * knitting_fee
    grand_total = total_yarn_cost + total_knitting_cost
    final_unit_price = grand_total / total_raw_weight

    # --- 結果表示 ---
    st.subheader("💰 計算結果")
    res_1, res_2, res_3 = st.columns(3)
    res_1.metric("生機総重量", f"{total_raw_weight:,.1f} kg")
    res_2.metric("総原価 (糸代+編賃)", f"¥{grand_total:,.0f}")
    res_3.metric("生機1kg単価", f"¥{final_unit_price:,.2f}")

    with st.expander("📝 算出根拠の内訳を表示"):
        st.write(f"**1. 生機重量**: {num_rolls}反 × {weight_per_roll}kg = {total_raw_weight:,.1f}kg")
        for det in calculation_details:
            st.write(f"**2. {det['name']}**: ロス込必要 {det['net']:.2f}kg → **{det['cases']}ケース** ({det['buy_kg']:.2f}kg) 購入 → コスト ¥{det['cost']:,.0f}")
        st.write(f"**3. 編賃**: {total_raw_weight:,.1f}kg × ¥{knitting_fee} = ¥{total_knitting_cost:,.0f}")
        st.write(f"**4. 合計**: (糸代 ¥{total_yarn_cost:,.0f} + 編賃 ¥{total_knitting_cost:,.0f}) ÷ {total_raw_weight:,.1f}kg = **¥{final_unit_price:,.2f}/kg**")

else:
    st.error("混率を合計100%に設定してください。")