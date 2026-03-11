import streamlit as st
import math

# --- 1. ページ構成 ---
st.set_page_config(page_title="繊維実務：自動原価計算ツール Pro", page_icon="📊", layout="wide")

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
    
    # 購入モードの選択
    purchase_mode = st.radio(
        "購入モード",
        ["ケース単位で購入", "必要数のみ購入"],
        help="ケース単位：1ケース(22.68kg等)ごとに切り上げて計算します。\n必要数のみ：ロスを含めた計算上の必要重量で計算します。"
    )
    
    if purchase_mode == "ケース単位で購入":
        case_weight = st.number_input("1ケースの重量 (kg)", value=22.68, step=0.01)
    else:
        case_weight = 0 # 使用しない

    loss_rate_percent = st.number_input("設定ロス率 (%)", value=2.0, step=0.1, format="%.1f")
    loss_rate = 1 + (loss_rate_percent / 100)
    
    st.divider()
    st.caption("実務用シミュレーター v4.1 (単位換算対応版)")

# --- 3. メイン画面 ---
st.title("📊 生機原価自動シミュレーター")
st.write("混率・単価の微調整、および「梱」「玉」単位の計算に対応しました。")

# --- 入力セクション：オーダー基本情報 ---
col_order_1, col_order_2, col_order_3 = st.columns(3)
with col_order_1:
    num_rolls = st.number_input("発注反数 (反)", min_value=1, value=15)
with col_order_2:
    weight_per_roll = st.number_input("1反あたりの重量 (kg)", min_value=0.1, value=10.0, step=0.1)
with col_order_3:
    knitting_fee = st.number_input("編賃単価 (円/kg)", min_value=0, value=200)

total_raw_weight = num_rolls * weight_per_roll

st.divider()

# --- 入力セクション：使用糸の設定 ---
st.subheader("🧵 使用糸の設定")
num_yarns = st.radio("糸の種類数", [1, 2, 3], horizontal=True)

yarn_data = []
y_cols = st.columns(num_yarns)

for i in range(num_yarns):
    with y_cols[i]:
        st.markdown(f"**糸 {i+1}**")
        name = st.text_input(f"素材名 {i+1}", value=f"素材{chr(65+i)}", key=f"name_{i}")
        
        # 混率を小数点2位まで対応
        percentage = st.number_input(f"混率 {i+1} (%)", min_value=0.00, max_value=100.00, value=100.0/num_yarns, step=0.01, format="%.2f", key=f"p_{i}")
        
        # 単価入力と単位選択
        price_val = st.number_input(f"入力単価 {i+1}", min_value=0.00, value=1000.00, step=0.01, format="%.2f", key=f"pr_val_{i}")
        unit = st.selectbox(f"単価単位 {i+1}", ["円/kg", "円/梱 (181.4kg)", "円/玉 (梱/40)"], key=f"unit_{i}")
        
        # 単位換算ロジック
        if unit == "円/kg":
            price_per_kg = price_val
        elif unit == "円/梱 (181.4kg)":
            price_per_kg = price_val / 181.4
        else: # 玉単価
            # 梱単価 = 玉単価 * 40
            # kg単価 = 梱単価 / 181.4
            price_per_kg = (price_val * 40) / 181.4
            
        yarn_data.append({"name": name, "p": percentage, "price_per_kg": price_per_kg, "input_price": price_val, "unit": unit})

# 混率チェック
total_p = sum(y['p'] for y in yarn_data)
if abs(total_p - 100.0) > 0.001:
    st.warning(f"⚠️ 混率の合計が {total_p:.2f}% です。100%になるよう調整してください。")

st.divider()

# --- 計算ロジック ---
if abs(total_p - 100.0) <= 0.001:
    total_yarn_cost = 0
    calculation_details = []

    for y in yarn_data:
        # ロスを含めた純粋な必要重量
        net_required = total_raw_weight * (y['p'] / 100) * loss_rate
        
        if purchase_mode == "ケース単位で購入":
            cases = math.ceil(net_required / case_weight)
            purchase_weight = cases * case_weight
            buy_desc = f"{cases}ケース ({purchase_weight:.2f}kg)"
        else:
            # 必要数のみ購入（ケース切り上げなし）
            purchase_weight = net_required
            buy_desc = f"{purchase_weight:.2f}kg (現物合わせ)"
            
        cost = purchase_weight * y['price_per_kg']
        total_yarn_cost += cost
        
        calculation_details.append({
            "name": y['name'],
            "net": net_required,
            "buy_desc": buy_desc,
            "cost": cost,
            "price_kg": y['price_per_kg'],
            "unit": y['unit'],
            "input_price": y['input_price']
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

    with st.expander("📝 算出根拠の内訳（単位換算詳細）"):
        st.write(f"**購入モード**: {purchase_mode}")
        for det in calculation_details:
            st.write(f"---")
            st.write(f"**【{det['name']}】**")
            st.write(f"・入力単価: ¥{det['input_price']:,.2f} ({det['unit']}) → 換算後: ¥{det['price_kg']:,.2f}/kg")
            st.write(f"・必要量(ロス込): {det['net']:.2f}kg")
            st.write(f"・購入量: {det['buy_desc']}")
            st.write(f"・糸代小計: ¥{det['cost']:,.0f}")
            
        st.write(f"---")
        st.write(f"**編賃**: {total_raw_weight:,.1f}kg × ¥{knitting_fee} = ¥{total_knitting_cost:,.0f}")
        st.write(f"**合計**: (糸代 ¥{total_yarn_cost:,.0f} + 編賃 ¥{total_knitting_cost:,.0f}) ÷ {total_raw_weight:,.1f}kg = **¥{final_unit_price:,.2f}/kg**")

else:
    st.error("混率を合計100%に設定してください。")
