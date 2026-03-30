import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import date, datetime
import random

# ─────────────────────────────────────────
#  PAGE CONFIG
# ─────────────────────────────────────────
st.set_page_config(
    page_title="PriceOps — Pricing & CPQ Operations",
    page_icon="💲",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────
#  CSS
# ─────────────────────────────────────────
st.markdown("""
<style>
  [data-testid="stAppViewContainer"] { background: #f8fafc; }
  [data-testid="stSidebar"] { background: #0f172a; }
  [data-testid="stSidebar"] * { color: #e2e8f0 !important; }
  [data-testid="stSidebar"] hr { border-color: #1e293b !important; }
  .block-container { padding: 1.5rem 2rem; }
  .stTabs [data-baseweb="tab-list"] { background: white; border-bottom: 2px solid #e2e8f0; gap: 4px; }
  .stTabs [data-baseweb="tab"] { background: transparent; color: #64748b; font-weight: 600; font-size: 13px; }
  .stTabs [aria-selected="true"] { background: #f1f5f9 !important; color: #0f172a !important; border-bottom: 2px solid #3b82f6 !important; }
  .stButton > button { background: #3b82f6 !important; color: white !important; border: none !important; font-weight: 700 !important; border-radius: 6px !important; }
  .stButton > button:hover { background: #2563eb !important; }
  .metric-card { background: white; border: 1px solid #e2e8f0; border-radius: 10px; padding: 16px 20px; }
  .metric-val { font-size: 28px; font-weight: 800; color: #0f172a; }
  .metric-label { font-size: 11px; color: #64748b; text-transform: uppercase; letter-spacing: 0.8px; margin-bottom: 6px; }
  .metric-sub { font-size: 11px; color: #94a3b8; margin-top: 4px; }
  .pass { color: #16a34a; font-weight: 700; }
  .fail { color: #dc2626; font-weight: 700; }
  .warn { color: #d97706; font-weight: 700; }
  div[data-testid="stDataFrame"] { border: 1px solid #e2e8f0; border-radius: 8px; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────
#  SEED DATA
# ─────────────────────────────────────────

# Product catalog — datacenter & workstation SKUs
PRODUCTS = [
    {"sku": "DC-CPU-001", "name": "Xeon Platinum 8480+ (60C)",     "category": "Datacenter CPU",    "list_price": 8990,  "cost": 5200, "segment": "Enterprise"},
    {"sku": "DC-CPU-002", "name": "Xeon Gold 6438N (32C)",         "category": "Datacenter CPU",    "list_price": 3980,  "cost": 2100, "segment": "Mid-Market"},
    {"sku": "DC-GPU-001", "name": "H100 SXM5 80GB",                "category": "Datacenter GPU",    "list_price": 29900, "cost": 18000,"segment": "Enterprise"},
    {"sku": "DC-GPU-002", "name": "A30 24GB PCIe",                 "category": "Datacenter GPU",    "list_price": 6490,  "cost": 3800, "segment": "Mid-Market"},
    {"sku": "DC-MEM-001", "name": "DDR5 ECC RDIMM 256GB Kit",      "category": "Server Memory",     "list_price": 2890,  "cost": 1600, "segment": "Enterprise"},
    {"sku": "DC-MEM-002", "name": "DDR5 ECC RDIMM 128GB Kit",      "category": "Server Memory",     "list_price": 1490,  "cost": 820,  "segment": "Mid-Market"},
    {"sku": "DC-STO-001", "name": "NVMe PCIe Gen5 15.36TB",        "category": "Enterprise Storage","list_price": 7200,  "cost": 4100, "segment": "Enterprise"},
    {"sku": "DC-STO-002", "name": "NVMe PCIe Gen4 3.84TB",         "category": "Enterprise Storage","list_price": 1890,  "cost": 1050, "segment": "Mid-Market"},
    {"sku": "WS-CPU-001", "name": "Core Ultra 9 285K",             "category": "Workstation CPU",   "list_price": 589,   "cost": 310,  "segment": "SMB"},
    {"sku": "WS-GPU-001", "name": "RTX 6000 Ada 48GB",             "category": "Workstation GPU",   "list_price": 6800,  "cost": 4000, "segment": "Enterprise"},
    {"sku": "WS-GPU-002", "name": "RTX 4000 Ada 20GB",             "category": "Workstation GPU",   "list_price": 1250,  "cost": 720,  "segment": "SMB"},
    {"sku": "WS-MEM-001", "name": "DDR5 ECC 192GB Workstation Kit","category": "Workstation Memory","list_price": 990,   "cost": 540,  "segment": "Enterprise"},
    {"sku": "WS-STO-001", "name": "Z NVME SSD 4TB Workstation",    "category": "Workstation SSD",   "list_price": 480,   "cost": 260,  "segment": "SMB"},
    {"sku": "DC-NET-001", "name": "400GbE NIC Dual Port",          "category": "Networking",        "list_price": 3200,  "cost": 1800, "segment": "Enterprise"},
    {"sku": "DC-SYS-001", "name": "4U Rackmount Server Chassis",   "category": "Systems",           "list_price": 4500,  "cost": 2600, "segment": "Enterprise"},
]

# Partner program discount tiers
PARTNER_TIERS = {
    "Platinum": {"base_disc": 0.28, "vol_threshold": 500000, "vol_disc": 0.05, "mdf": 0.03, "max_disc": 0.40},
    "Gold":     {"base_disc": 0.20, "vol_threshold": 200000, "vol_disc": 0.03, "mdf": 0.02, "max_disc": 0.32},
    "Silver":   {"base_disc": 0.13, "vol_threshold": 75000,  "vol_disc": 0.02, "mdf": 0.01, "max_disc": 0.22},
    "Registered":{"base_disc": 0.06,"vol_threshold": 20000,  "vol_disc": 0.01, "mdf": 0.00, "max_disc": 0.12},
}

SEGMENTS = ["Enterprise", "Mid-Market", "SMB"]
REGIONS  = ["North America", "EMEA", "APAC", "LATAM"]

# ─────────────────────────────────────────
#  SESSION STATE
# ─────────────────────────────────────────
def init_state():
    if "products" not in st.session_state:
        st.session_state.products = pd.DataFrame(PRODUCTS)

    if "quotes" not in st.session_state:
        random.seed(42)
        quotes = []
        partners = ["TechNova Solutions", "DataCore Systems", "CloudPeak LLC",
                    "VertexIT Partners", "Apex Compute Group", "NexusWave Inc.",
                    "SilverBridge Tech", "OmniCloud Partners", "Redline Systems", "CorePath Global"]
        tiers_list = ["Platinum","Gold","Gold","Silver","Silver","Silver","Registered","Registered","Registered","Registered"]
        for i, (p, t) in enumerate(zip(partners, tiers_list)):
            n_items = random.randint(2, 5)
            items = random.sample(PRODUCTS, n_items)
            qty_list = [random.randint(1, 20) for _ in items]
            subtotal = sum(it["list_price"] * q for it, q in zip(items, qty_list))
            disc = PARTNER_TIERS[t]["base_disc"]
            if subtotal >= PARTNER_TIERS[t]["vol_threshold"]:
                disc += PARTNER_TIERS[t]["vol_disc"]
            net = subtotal * (1 - disc)
            margin = (net - sum(it["cost"] * q for it, q in zip(items, qty_list))) / net * 100
            status = random.choice(["Approved","Approved","Approved","Pending Review","Policy Violation"])
            quotes.append({
                "Quote ID": f"Q-2026-{1000+i}", "Partner": p, "Tier": t,
                "Segment": random.choice(SEGMENTS), "Region": random.choice(REGIONS),
                "Items": n_items, "List Total": subtotal,
                "Discount %": round(disc * 100, 1), "Net Price": round(net),
                "Gross Margin %": round(margin, 1), "Status": status,
                "Created": f"Mar {10+i}, 2026",
            })
        st.session_state.quotes = pd.DataFrame(quotes)

    if "uat_results" not in st.session_state:
        st.session_state.uat_results = []

    if "audit_log" not in st.session_state:
        st.session_state.audit_log = [
            {"Timestamp": "Mar 30, 2026 09:14", "User": "rsatish",  "Action": "Price updated",      "SKU": "DC-GPU-001", "Old Value": "$28,500", "New Value": "$29,900", "Status": "Approved"},
            {"Timestamp": "Mar 29, 2026 14:32", "User": "jsmith",   "Action": "Discount override",  "SKU": "DC-CPU-001", "Old Value": "28%",     "New Value": "35%",     "Status": "Flagged"},
            {"Timestamp": "Mar 29, 2026 11:05", "User": "rsatish",  "Action": "New SKU added",       "SKU": "WS-STO-001", "Old Value": "—",        "New Value": "$480",    "Status": "Approved"},
            {"Timestamp": "Mar 28, 2026 16:48", "User": "mwilson",  "Action": "Tier changed",        "SKU": "—",          "Old Value": "Silver",   "New Value": "Gold",    "Status": "Approved"},
            {"Timestamp": "Mar 27, 2026 10:22", "User": "jsmith",   "Action": "Price updated",       "SKU": "DC-MEM-001", "Old Value": "$3,100",   "New Value": "$2,890",  "Status": "Approved"},
        ]

init_state()
prods_df  = st.session_state.products
quotes_df = st.session_state.quotes

# ─────────────────────────────────────────
#  SIDEBAR
# ─────────────────────────────────────────
with st.sidebar:
    st.markdown("## 💲 PriceOps")
    st.markdown("**Pricing & CPQ Operations**")
    st.divider()
    st.markdown(f"**Company:** Nexus Semiconductor")
    st.markdown(f"**Fiscal Quarter:** Q2 2026")
    st.markdown(f"**Date:** {date.today().strftime('%b %d, %Y')}")
    st.divider()
    total_skus     = len(prods_df)
    active_quotes  = len(quotes_df)
    violations     = len(quotes_df[quotes_df["Status"] == "Policy Violation"])
    pending        = len(quotes_df[quotes_df["Status"] == "Pending Review"])
    st.markdown(f"📦 **{total_skus}** Active SKUs")
    st.markdown(f"📋 **{active_quotes}** Live Quotes")
    st.markdown(f"🔴 **{violations}** Policy Violations")
    st.markdown(f"⏳ **{pending}** Pending Review")
    st.divider()
    st.caption("Built by Rutwik Satish")
    st.caption("github.com/rutwik · streamlit")

# ─────────────────────────────────────────
#  TABS
# ─────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 Dashboard", "💲 CPQ Configurator", "🧪 UAT Validator", "📋 Quote Manager", "🔍 Audit Log", "🗂️ Data Preview"
])

# ═══════════════════════════════════════════
#  TAB 1 — DASHBOARD
# ═══════════════════════════════════════════
with tab1:
    st.markdown("## Pricing Operations Dashboard")
    st.caption(f"Nexus Semiconductor · Q2 2026 · {len(prods_df)} SKUs · {len(quotes_df)} Active Quotes")
    st.divider()

    # KPIs
    k1, k2, k3, k4 = st.columns(4)
    avg_margin = quotes_df["Gross Margin %"].mean()
    total_pipeline = quotes_df["Net Price"].sum()
    compliance_rate = len(quotes_df[quotes_df["Status"] == "Approved"]) / len(quotes_df) * 100

    k1.metric("Active SKUs",         f"{len(prods_df)}",         "4 categories")
    k2.metric("Pipeline Value",      f"${total_pipeline/1e6:.2f}M", "Live quotes")
    k3.metric("Avg Gross Margin",    f"{avg_margin:.1f}%",       "Across all quotes")
    k4.metric("Policy Compliance",   f"{compliance_rate:.0f}%",  f"{violations} violations", delta_color="inverse")

    st.divider()
    col_l, col_r = st.columns(2)

    with col_l:
        st.markdown("#### Pipeline by Partner Tier")
        tier_pipeline = quotes_df.groupby("Tier")["Net Price"].sum().reset_index()
        tier_order = ["Platinum", "Gold", "Silver", "Registered"]
        tier_pipeline["Tier"] = pd.Categorical(tier_pipeline["Tier"], categories=tier_order, ordered=True)
        tier_pipeline = tier_pipeline.sort_values("Tier")
        colors = {"Platinum": "#6366f1", "Gold": "#f59e0b", "Silver": "#64748b", "Registered": "#94a3b8"}
        fig_tier = go.Figure(go.Bar(
            x=tier_pipeline["Tier"],
            y=tier_pipeline["Net Price"],
            marker_color=[colors[t] for t in tier_pipeline["Tier"]],
            text=[f"${v/1000:.0f}K" for v in tier_pipeline["Net Price"]],
            textposition="outside",
        ))
        fig_tier.update_layout(
            paper_bgcolor="white", plot_bgcolor="white", font_color="#0f172a",
            yaxis=dict(showgrid=True, gridcolor="#f1f5f9", tickprefix="$"),
            xaxis=dict(showgrid=False),
            margin=dict(l=10, r=10, t=10, b=10), height=260, showlegend=False,
        )
        st.plotly_chart(fig_tier, use_container_width=True)

    with col_r:
        st.markdown("#### Quote Status Distribution")
        status_counts = quotes_df["Status"].value_counts().reset_index()
        status_counts.columns = ["Status", "Count"]
        s_colors = {"Approved": "#16a34a", "Pending Review": "#d97706", "Policy Violation": "#dc2626"}
        fig_status = go.Figure(go.Pie(
            labels=status_counts["Status"],
            values=status_counts["Count"],
            hole=0.55,
            marker_colors=[s_colors.get(s, "#94a3b8") for s in status_counts["Status"]],
            textinfo="label+percent",
            textfont_size=11,
        ))
        fig_status.update_layout(
            paper_bgcolor="white", font_color="#0f172a",
            margin=dict(l=10, r=10, t=10, b=10), height=260, showlegend=False,
        )
        st.plotly_chart(fig_status, use_container_width=True)

    # Margin by category
    st.markdown("#### Gross Margin % by Product Category")
    cat_margin = quotes_df.merge(
        prods_df[["sku","category"]].rename(columns={"sku":"SKU","category":"Category"}),
        how="left", left_on="Quote ID", right_on="SKU"
    )
    # simplified: use segment as proxy
    seg_margin = quotes_df.groupby("Segment")["Gross Margin %"].mean().reset_index()
    seg_colors = ["#3b82f6", "#6366f1", "#f59e0b"]
    fig_margin = go.Figure(go.Bar(
        x=seg_margin["Segment"], y=seg_margin["Gross Margin %"],
        marker_color=seg_colors,
        text=[f"{v:.1f}%" for v in seg_margin["Gross Margin %"]],
        textposition="outside",
    ))
    fig_margin.update_layout(
        paper_bgcolor="white", plot_bgcolor="white", font_color="#0f172a",
        yaxis=dict(showgrid=True, gridcolor="#f1f5f9", ticksuffix="%", range=[0, 55]),
        xaxis=dict(showgrid=False),
        margin=dict(l=10, r=10, t=10, b=10), height=220, showlegend=False,
    )
    st.plotly_chart(fig_margin, use_container_width=True)

    # Policy violations callout
    if violations > 0:
        st.error(f"⚠️ **{violations} Policy Violation(s) Detected** — quotes exceeding maximum discount thresholds. Review required before submission.")
        viol_df = quotes_df[quotes_df["Status"] == "Policy Violation"][["Quote ID","Partner","Tier","Discount %","Net Price","Status"]]
        st.dataframe(viol_df, use_container_width=True)

# ═══════════════════════════════════════════
#  TAB 2 — CPQ CONFIGURATOR
# ═══════════════════════════════════════════
with tab2:
    st.markdown("## CPQ Quote Configurator")
    st.caption("Configure products, apply partner discount tiers, validate pricing policy compliance")
    st.divider()

    col_cfg, col_out = st.columns([1, 1])

    with col_cfg:
        st.markdown("#### 1. Partner & Program Setup")
        partner_name = st.text_input("Partner / Account Name", value="TechNova Solutions")
        partner_tier = st.selectbox("Partner Program Tier", list(PARTNER_TIERS.keys()))
        region       = st.selectbox("Region", REGIONS)
        segment      = st.selectbox("Customer Segment", SEGMENTS)

        tier_info = PARTNER_TIERS[partner_tier]
        st.info(f"**{partner_tier} Tier:** Base discount {tier_info['base_disc']*100:.0f}% · "
                f"Vol bonus {tier_info['vol_disc']*100:.0f}% (>{tier_info['vol_threshold']:,}) · "
                f"Max allowed {tier_info['max_disc']*100:.0f}%")

        st.markdown("#### 2. Product Selection")
        selected_skus = st.multiselect(
            "Add SKUs to Quote",
            options=[f"{p['sku']} — {p['name']}" for p in PRODUCTS],
            default=[f"{PRODUCTS[0]['sku']} — {PRODUCTS[0]['name']}",
                     f"{PRODUCTS[2]['sku']} — {PRODUCTS[2]['name']}"],
        )

        qtys = {}
        overrides = {}
        if selected_skus:
            st.markdown("#### 3. Quantities & Override Discounts")
            for sku_str in selected_skus:
                sku_code = sku_str.split(" — ")[0]
                prod = next(p for p in PRODUCTS if p["sku"] == sku_code)
                c1, c2 = st.columns([2, 1])
                with c1:
                    qtys[sku_code] = st.number_input(
                        f"Qty: {prod['name'][:30]}", min_value=1, max_value=500,
                        value=1, key=f"qty_{sku_code}"
                    )
                with c2:
                    overrides[sku_code] = st.number_input(
                        "Override %", min_value=0.0, max_value=50.0,
                        value=float(tier_info["base_disc"] * 100),
                        step=0.5, key=f"ovr_{sku_code}"
                    )

        manual_disc = st.slider("Additional Deal Discount (%)", 0.0, 10.0, 0.0, 0.5)

    with col_out:
        st.markdown("#### Quote Summary & Compliance Output")

        if not selected_skus:
            st.info("Select products on the left to generate a quote.")
        else:
            rows = []
            total_list = 0
            total_cost = 0
            violations_found = []

            for sku_str in selected_skus:
                sku_code = sku_str.split(" — ")[0]
                prod = next(p for p in PRODUCTS if p["sku"] == sku_code)
                qty  = qtys.get(sku_code, 1)
                ovr  = overrides.get(sku_code, tier_info["base_disc"] * 100) / 100
                line_list = prod["list_price"] * qty
                line_cost = prod["cost"] * qty
                total_list += line_list
                total_cost += line_cost

                # volume bonus
                vol_bonus = tier_info["vol_disc"] if total_list >= tier_info["vol_threshold"] else 0
                effective_disc = min(ovr + manual_disc / 100 + vol_bonus, 0.50)
                net_unit = prod["list_price"] * (1 - effective_disc)
                net_line = net_unit * qty
                margin   = (net_line - line_cost) / net_line * 100 if net_line > 0 else 0

                # policy check
                policy_ok = effective_disc <= tier_info["max_disc"]
                if not policy_ok:
                    violations_found.append(f"{sku_code}: {effective_disc*100:.1f}% exceeds max {tier_info['max_disc']*100:.0f}%")

                rows.append({
                    "SKU": sku_code, "Product": prod["name"][:28],
                    "Qty": qty, "List Unit": f"${prod['list_price']:,}",
                    "Disc %": f"{effective_disc*100:.1f}%",
                    "Net Unit": f"${net_unit:,.0f}",
                    "Net Line": f"${net_line:,.0f}",
                    "Margin %": f"{margin:.1f}%",
                    "Policy": "✅ Pass" if policy_ok else "❌ Fail",
                })

            quote_df = pd.DataFrame(rows)
            st.dataframe(quote_df, use_container_width=True, height=200)

            # Totals
            vol_bonus_total = tier_info["vol_disc"] if total_list >= tier_info["vol_threshold"] else 0
            eff_disc_total  = min(tier_info["base_disc"] + manual_disc / 100 + vol_bonus_total, 0.50)
            net_total       = total_list * (1 - eff_disc_total)
            gross_margin    = (net_total - total_cost) / net_total * 100 if net_total > 0 else 0

            m1, m2, m3 = st.columns(3)
            m1.metric("List Total",    f"${total_list:,.0f}")
            m2.metric("Net Price",     f"${net_total:,.0f}",  f"-{eff_disc_total*100:.1f}%")
            m3.metric("Gross Margin",  f"{gross_margin:.1f}%")

            st.divider()
            # Compliance result
            if violations_found:
                st.error("❌ **Policy Violation Detected** — Quote cannot be submitted.")
                for v in violations_found:
                    st.markdown(f"- {v}")
                st.markdown("*Required action: Reduce discount or submit for manager approval.*")
            elif gross_margin < 15:
                st.warning(f"⚠️ **Margin Warning** — Gross margin ({gross_margin:.1f}%) is below the 15% floor. Finance approval required.")
            else:
                st.success("✅ **Policy Compliant** — Quote is within approved discount and margin thresholds.")

            if st.button("💾 Save Quote to Pipeline"):
                new_q = {
                    "Quote ID": f"Q-2026-{1010 + len(st.session_state.quotes)}",
                    "Partner": partner_name, "Tier": partner_tier,
                    "Segment": segment, "Region": region,
                    "Items": len(selected_skus), "List Total": total_list,
                    "Discount %": round(eff_disc_total * 100, 1),
                    "Net Price": round(net_total),
                    "Gross Margin %": round(gross_margin, 1),
                    "Status": "Policy Violation" if violations_found else ("Pending Review" if gross_margin < 15 else "Approved"),
                    "Created": date.today().strftime("%b %d, %Y"),
                }
                st.session_state.quotes = pd.concat(
                    [st.session_state.quotes, pd.DataFrame([new_q])], ignore_index=True
                )
                st.success(f"✅ Quote {new_q['Quote ID']} saved to pipeline.")
                st.rerun()

# ═══════════════════════════════════════════
#  TAB 3 — UAT VALIDATOR
# ═══════════════════════════════════════════
with tab3:
    st.markdown("## UAT Pricing Validator")
    st.caption("Run structured test cases to validate pricing rules, policy alignment, and system configuration across business units")
    st.divider()

    BUILT_IN_TESTS = [
        {
            "id": "TC-001", "name": "Platinum partner base discount applied correctly",
            "bu": "North America Sales", "category": "Discount Logic",
            "input": {"tier": "Platinum", "list_price": 10000, "qty": 1, "override_disc": 0.28},
            "expected": {"net_price": 7200, "policy": "Pass"},
        },
        {
            "id": "TC-002", "name": "Volume bonus triggers above threshold",
            "bu": "EMEA Sales", "category": "Volume Pricing",
            "input": {"tier": "Gold", "list_price": 250000, "qty": 1, "override_disc": 0.20},
            "expected": {"vol_bonus_applied": True, "policy": "Pass"},
        },
        {
            "id": "TC-003", "name": "Discount exceeding Platinum max flagged as violation",
            "bu": "Finance & Compliance", "category": "Policy Enforcement",
            "input": {"tier": "Platinum", "list_price": 10000, "qty": 1, "override_disc": 0.45},
            "expected": {"policy": "Fail"},
        },
        {
            "id": "TC-004", "name": "Silver partner below volume threshold — no bonus",
            "bu": "SMB Sales", "category": "Volume Pricing",
            "input": {"tier": "Silver", "list_price": 50000, "qty": 1, "override_disc": 0.13},
            "expected": {"vol_bonus_applied": False, "policy": "Pass"},
        },
        {
            "id": "TC-005", "name": "Registered partner max discount boundary",
            "bu": "Channel Operations", "category": "Policy Enforcement",
            "input": {"tier": "Registered", "list_price": 5000, "qty": 1, "override_disc": 0.12},
            "expected": {"net_price": 4400, "policy": "Pass"},
        },
        {
            "id": "TC-006", "name": "Gross margin floor violation triggers warning",
            "bu": "Finance & Compliance", "category": "Margin Floors",
            "input": {"tier": "Platinum", "list_price": 5000, "cost": 4700, "qty": 1, "override_disc": 0.35},
            "expected": {"margin_warning": True},
        },
        {
            "id": "TC-007", "name": "New SKU price list ingestion — list price populated",
            "bu": "Product Management", "category": "Product Setup",
            "input": {"sku": "DC-GPU-001", "expected_list": 29900},
            "expected": {"price_match": True},
        },
        {
            "id": "TC-008", "name": "Quote ID format compliance",
            "bu": "Sales Operations", "category": "Data Integrity",
            "input": {"quote_id": "Q-2026-1000"},
            "expected": {"format_valid": True},
        },
    ]

    def run_test(tc):
        inp = tc["input"]
        exp = tc["expected"]
        result = {"id": tc["id"], "name": tc["name"], "bu": tc["bu"], "category": tc["category"]}
        try:
            if "policy" in exp:
                tier_data = PARTNER_TIERS.get(inp.get("tier","Gold"), PARTNER_TIERS["Gold"])
                disc = inp.get("override_disc", tier_data["base_disc"])
                lp   = inp.get("list_price", 10000)
                qty  = inp.get("qty", 1)
                net  = lp * qty * (1 - disc)
                policy_pass = disc <= tier_data["max_disc"]
                actual_policy = "Pass" if policy_pass else "Fail"
                status = "PASS" if actual_policy == exp["policy"] else "FAIL"
                if "net_price" in exp:
                    status = "PASS" if abs(net - exp["net_price"]) < 1 and actual_policy == exp["policy"] else "FAIL"
                result.update({"status": status, "actual": f"Policy={actual_policy}, Net=${net:,.0f}", "expected": str(exp)})

            elif "vol_bonus_applied" in exp:
                tier_data = PARTNER_TIERS[inp["tier"]]
                applied = inp["list_price"] >= tier_data["vol_threshold"]
                status = "PASS" if applied == exp["vol_bonus_applied"] else "FAIL"
                result.update({"status": status, "actual": f"Vol bonus applied={applied}", "expected": str(exp)})

            elif "price_match" in exp:
                prod = next((p for p in PRODUCTS if p["sku"] == inp.get("sku","")), None)
                match = prod is not None and prod["list_price"] == inp["expected_list"]
                status = "PASS" if match == exp["price_match"] else "FAIL"
                result.update({"status": status, "actual": f"List price=${prod['list_price'] if prod else 'NOT FOUND'}", "expected": str(exp)})

            elif "format_valid" in exp:
                import re
                valid = bool(re.match(r"Q-\d{4}-\d{4}", inp["quote_id"]))
                status = "PASS" if valid == exp["format_valid"] else "FAIL"
                result.update({"status": status, "actual": f"Format valid={valid}", "expected": str(exp)})

            elif "margin_warning" in exp:
                tier_data = PARTNER_TIERS[inp["tier"]]
                disc = inp["override_disc"]
                lp, cost, qty = inp["list_price"], inp.get("cost", inp["list_price"]*0.6), inp["qty"]
                net = lp * qty * (1 - disc)
                margin = (net - cost * qty) / net * 100
                warn = margin < 15
                status = "PASS" if warn == exp["margin_warning"] else "FAIL"
                result.update({"status": status, "actual": f"Margin={margin:.1f}%, Warning={warn}", "expected": str(exp)})
            else:
                result.update({"status": "SKIP", "actual": "No matching logic", "expected": str(exp)})
        except Exception as e:
            result.update({"status": "ERROR", "actual": str(e), "expected": str(exp)})
        return result

    # Filter controls
    uf1, uf2, uf3 = st.columns([2, 2, 2])
    with uf1:
        bu_filter = st.selectbox("Business Unit", ["All"] + list({t["bu"] for t in BUILT_IN_TESTS}))
    with uf2:
        cat_filter = st.selectbox("Test Category", ["All"] + list({t["category"] for t in BUILT_IN_TESTS}))
    with uf3:
        st.markdown("<div style='margin-top:28px;'></div>", unsafe_allow_html=True)
        run_all = st.button("▶ Run All Test Cases")

    filtered_tests = [t for t in BUILT_IN_TESTS
                      if (bu_filter == "All" or t["bu"] == bu_filter)
                      and (cat_filter == "All" or t["category"] == cat_filter)]

    if run_all or st.session_state.uat_results:
        if run_all:
            st.session_state.uat_results = [run_test(t) for t in filtered_tests]

        results = st.session_state.uat_results
        passed  = sum(1 for r in results if r["status"] == "PASS")
        failed  = sum(1 for r in results if r["status"] == "FAIL")
        total_r = len(results)
        pass_rate = passed / total_r * 100 if total_r > 0 else 0

        r1, r2, r3, r4 = st.columns(4)
        r1.metric("Test Cases Run",  total_r)
        r2.metric("Passed",          passed,  f"{pass_rate:.0f}% pass rate")
        r3.metric("Failed",          failed,  delta_color="inverse")
        r4.metric("Defect Escape Rate", f"{(failed/total_r*100):.0f}%" if total_r > 0 else "0%", delta_color="inverse")

        st.divider()

        def style_uat(val):
            if val == "PASS":  return "color:#16a34a;font-weight:700;"
            if val == "FAIL":  return "color:#dc2626;font-weight:700;"
            if val == "ERROR": return "color:#d97706;font-weight:700;"
            return ""

        results_df = pd.DataFrame(results)[["id","name","bu","category","status","actual","expected"]]
        results_df.columns = ["Test ID","Test Name","Business Unit","Category","Result","Actual Output","Expected"]
        styled_r = results_df.style.applymap(style_uat, subset=["Result"])
        st.dataframe(styled_r, use_container_width=True, height=340)

        if failed == 0:
            st.success("✅ All test cases passed. Pricing configuration is compliant across all business units.")
        else:
            st.error(f"❌ {failed} test case(s) failed. Review pricing rules before deployment to production systems.")

        # Download report
        csv_uat = results_df.to_csv(index=False)
        st.download_button("⬇ Export UAT Report (CSV)", data=csv_uat,
                           file_name=f"PriceOps_UAT_Report_{date.today()}.csv", mime="text/csv")
    else:
        st.info("Click **Run All Test Cases** to validate pricing rules across business units.")

        # Preview test cases
        preview_df = pd.DataFrame([{
            "Test ID": t["id"], "Test Name": t["name"],
            "Business Unit": t["bu"], "Category": t["category"]
        } for t in filtered_tests])
        st.dataframe(preview_df, use_container_width=True)

# ═══════════════════════════════════════════
#  TAB 4 — QUOTE MANAGER
# ═══════════════════════════════════════════
with tab4:
    st.markdown("## Quote Pipeline Manager")
    st.caption("Review, filter and manage all active quotes across partner accounts")
    st.divider()

    qf1, qf2, qf3, qf4 = st.columns([2, 2, 2, 3])
    with qf1: q_status  = st.selectbox("Status",  ["All"] + list(quotes_df["Status"].unique()))
    with qf2: q_tier    = st.selectbox("Tier",    ["All"] + list(PARTNER_TIERS.keys()))
    with qf3: q_region  = st.selectbox("Region",  ["All"] + REGIONS)
    with qf4: q_search  = st.text_input("Search partner...", placeholder="Partner name")

    filt = quotes_df.copy()
    if q_status != "All": filt = filt[filt["Status"] == q_status]
    if q_tier   != "All": filt = filt[filt["Tier"]   == q_tier]
    if q_region != "All": filt = filt[filt["Region"] == q_region]
    if q_search:          filt = filt[filt["Partner"].str.lower().str.contains(q_search.lower())]

    st.caption(f"Showing {len(filt)} of {len(quotes_df)} quotes  |  "
               f"Pipeline: ${filt['Net Price'].sum():,.0f}  |  "
               f"Avg Margin: {filt['Gross Margin %'].mean():.1f}%")

    def style_quote_status(val):
        return {"Approved": "color:#16a34a;font-weight:700;",
                "Pending Review": "color:#d97706;font-weight:700;",
                "Policy Violation": "color:#dc2626;font-weight:700;"}.get(val, "")

    def style_margin(val):
        try:
            v = float(val)
            if v < 15: return "color:#dc2626;"
            if v < 25: return "color:#d97706;"
            return "color:#16a34a;"
        except: return ""

    display_q = filt[["Quote ID","Partner","Tier","Segment","Region","Items",
                       "Discount %","Net Price","Gross Margin %","Status","Created"]].copy()
    display_q["Net Price"] = display_q["Net Price"].apply(lambda x: f"${x:,}")

    styled_q = display_q.style \
        .applymap(style_quote_status, subset=["Status"]) \
        .applymap(style_margin, subset=["Gross Margin %"])
    st.dataframe(styled_q, use_container_width=True, height=400)

    dl1, dl2 = st.columns([2, 7])
    with dl1:
        csv_q = filt.to_csv(index=False)
        st.download_button("⬇ Export Quotes CSV", data=csv_q,
                           file_name="PriceOps_QuotePipeline.csv", mime="text/csv")

# ═══════════════════════════════════════════
#  TAB 5 — AUDIT LOG
# ═══════════════════════════════════════════
with tab5:
    st.markdown("## Pricing Data Audit Log")
    st.caption("Track all pricing changes, discount overrides, and system updates for compliance and governance")
    st.divider()

    # Summary
    a1, a2, a3 = st.columns(3)
    a1.metric("Total Changes (30d)", len(st.session_state.audit_log))
    flagged = sum(1 for r in st.session_state.audit_log if r["Status"] == "Flagged")
    a2.metric("Flagged Overrides",   flagged, delta_color="inverse")
    a3.metric("Last Updated",        "Today 09:14")

    st.divider()

    def style_audit(val):
        if val == "Flagged":  return "color:#dc2626;font-weight:700;"
        if val == "Approved": return "color:#16a34a;font-weight:700;"
        return ""

    audit_df = pd.DataFrame(st.session_state.audit_log)
    styled_audit = audit_df.style.applymap(style_audit, subset=["Status"])
    st.dataframe(styled_audit, use_container_width=True)

    st.divider()
    st.markdown("#### Log New Pricing Change")
    lc1, lc2 = st.columns(2)
    with lc1:
        log_action    = st.selectbox("Action Type", ["Price updated","Discount override","New SKU added","Tier changed","Policy exception"])
        log_sku       = st.text_input("SKU (if applicable)", placeholder="e.g. DC-GPU-001")
    with lc2:
        log_old       = st.text_input("Old Value", placeholder="e.g. $28,500")
        log_new       = st.text_input("New Value",  placeholder="e.g. $29,900")

    if st.button("➕ Log Change"):
        if log_action and log_new:
            flag = "Flagged" if log_action == "Discount override" else "Approved"
            st.session_state.audit_log.insert(0, {
                "Timestamp": datetime.now().strftime("%b %d, %Y %H:%M"),
                "User": "rsatish", "Action": log_action,
                "SKU": log_sku or "—", "Old Value": log_old or "—",
                "New Value": log_new, "Status": flag,
            })
            st.success(f"✅ Change logged. Status: **{flag}**")
            st.rerun()
        else:
            st.warning("Please fill in Action Type and New Value.")

    csv_audit = pd.DataFrame(st.session_state.audit_log).to_csv(index=False)
    st.download_button("⬇ Export Full Audit Log", data=csv_audit,
                       file_name=f"PriceOps_AuditLog_{date.today()}.csv", mime="text/csv")

# ═══════════════════════════════════════════
#  TAB 6 — DATA PREVIEW
# ═══════════════════════════════════════════
with tab6:
    st.markdown("## Demo Data Preview")
    st.caption("Structured datasets powering PriceOps — product catalog, partner tiers, quote pipeline, and UAT test cases")
    st.divider()

    ds = st.radio("Select Dataset", [
        "📦 Product Catalog",
        "🤝 Partner Program Tiers",
        "📋 Quote Pipeline",
        "🧪 UAT Test Cases",
        "🔍 Audit Log"
    ], horizontal=True)

    st.divider()

    # ── PRODUCT CATALOG ──────────────────────
    if ds == "📦 Product Catalog":
        st.markdown("#### Product Catalog — 15 Datacenter & Workstation SKUs")
        st.caption("Source: Simulated Nexus Semiconductor internal price list. Covers CPUs, GPUs, Memory, Storage, Networking, and Systems across Enterprise, Mid-Market, and SMB segments.")

        cat_df = prods_df.copy()
        cat_df["List Price"]  = cat_df["list_price"].apply(lambda x: f"${x:,}")
        cat_df["Cost"]        = cat_df["cost"].apply(lambda x: f"${x:,}")
        cat_df["Gross Margin"]= ((cat_df["list_price"] - cat_df["cost"]) / cat_df["list_price"] * 100).round(1).astype(str) + "%"
        cat_df = cat_df.rename(columns={"sku":"SKU","name":"Product Name","category":"Category","segment":"Segment"})
        display_cat = cat_df[["SKU","Product Name","Category","Segment","List Price","Cost","Gross Margin"]]

        def style_seg(val):
            return {"Enterprise":"color:#6366f1;font-weight:700;",
                    "Mid-Market":"color:#3b82f6;font-weight:700;",
                    "SMB":       "color:#16a34a;font-weight:700;"}.get(val,"")
        st.dataframe(display_cat.style.applymap(style_seg, subset=["Segment"]),
                     use_container_width=True, height=460)

        # Category breakdown chart
        st.markdown("#### SKU Count by Category")
        cat_counts = prods_df["category"].value_counts().reset_index()
        cat_counts.columns = ["Category","Count"]
        fig_cat = px.bar(cat_counts, x="Count", y="Category", orientation="h",
                         color="Count", color_continuous_scale="Blues",
                         text="Count")
        fig_cat.update_layout(paper_bgcolor="white", plot_bgcolor="white",
                              font_color="#0f172a", margin=dict(l=10,r=10,t=10,b=10),
                              height=280, showlegend=False, coloraxis_showscale=False)
        fig_cat.update_traces(textposition="outside")
        st.plotly_chart(fig_cat, use_container_width=True)

        csv_p = display_cat.to_csv(index=False)
        st.download_button("⬇ Export Product Catalog CSV", data=csv_p,
                           file_name="PriceOps_ProductCatalog.csv", mime="text/csv")

    # ── PARTNER TIERS ────────────────────────
    elif ds == "🤝 Partner Program Tiers":
        st.markdown("#### Partner Program Discount Tier Structure")
        st.caption("Defines base discounts, volume bonus thresholds, MDF (Marketing Development Funds), and maximum allowable discounts per tier. Used by the CPQ Configurator and UAT Validator to enforce policy compliance.")

        tier_rows = []
        for tier, vals in PARTNER_TIERS.items():
            tier_rows.append({
                "Tier":                tier,
                "Base Discount":       f"{vals['base_disc']*100:.0f}%",
                "Volume Threshold":    f"${vals['vol_threshold']:,}",
                "Volume Bonus":        f"+{vals['vol_disc']*100:.0f}%",
                "MDF Rebate":          f"{vals['mdf']*100:.0f}%",
                "Max Allowed Disc":    f"{vals['max_disc']*100:.0f}%",
                "Effective Max Net":   f"{(1-vals['max_disc'])*100:.0f}% of list",
            })
        tier_df = pd.DataFrame(tier_rows)

        def style_tier(val):
            return {"Platinum":"color:#6366f1;font-weight:800;",
                    "Gold":    "color:#f59e0b;font-weight:800;",
                    "Silver":  "color:#64748b;font-weight:800;",
                    "Registered":"color:#94a3b8;font-weight:700;"}.get(val,"")
        st.dataframe(tier_df.style.applymap(style_tier, subset=["Tier"]),
                     use_container_width=True, height=200)

        # Visual comparison
        st.markdown("#### Tier Comparison — Base vs Max Discount")
        tiers_list_viz = list(PARTNER_TIERS.keys())
        base_discs = [PARTNER_TIERS[t]["base_disc"]*100 for t in tiers_list_viz]
        max_discs  = [PARTNER_TIERS[t]["max_disc"]*100  for t in tiers_list_viz]
        fig_tiers = go.Figure()
        fig_tiers.add_trace(go.Bar(name="Base Discount", x=tiers_list_viz, y=base_discs,
                                   marker_color="#3b82f6", text=[f"{v:.0f}%" for v in base_discs],
                                   textposition="outside"))
        fig_tiers.add_trace(go.Bar(name="Max Allowed", x=tiers_list_viz, y=max_discs,
                                   marker_color="#6366f1", text=[f"{v:.0f}%" for v in max_discs],
                                   textposition="outside"))
        fig_tiers.update_layout(barmode="group", paper_bgcolor="white", plot_bgcolor="white",
                                font_color="#0f172a", yaxis=dict(ticksuffix="%", range=[0,55]),
                                margin=dict(l=10,r=10,t=10,b=10), height=280,
                                legend=dict(orientation="h", y=1.1))
        st.plotly_chart(fig_tiers, use_container_width=True)

        # Policy rules
        st.markdown("#### Pricing Policy Rules")
        rules = [
            {"Rule ID":"PR-001","Rule":"Base discount applied on all transactions per tier","Enforced By":"CPQ Configurator"},
            {"Rule ID":"PR-002","Rule":"Volume bonus applied when quote exceeds tier threshold","Enforced By":"CPQ Configurator"},
            {"Rule ID":"PR-003","Rule":"Discount exceeding tier maximum triggers Policy Violation","Enforced By":"CPQ + UAT Validator"},
            {"Rule ID":"PR-004","Rule":"Gross margin below 15% floor triggers Finance approval","Enforced By":"CPQ Configurator"},
            {"Rule ID":"PR-005","Rule":"Discount overrides must be logged in Audit Log","Enforced By":"Audit Log"},
            {"Rule ID":"PR-006","Rule":"MDF rebate paid quarterly on approved partner invoices","Enforced By":"Finance System"},
        ]
        st.dataframe(pd.DataFrame(rules), use_container_width=True, height=240)

        csv_t = tier_df.to_csv(index=False)
        st.download_button("⬇ Export Tier Structure CSV", data=csv_t,
                           file_name="PriceOps_PartnerTiers.csv", mime="text/csv")

    # ── QUOTE PIPELINE ───────────────────────
    elif ds == "📋 Quote Pipeline":
        st.markdown("#### Quote Pipeline — 10 Simulated Partner Accounts")
        st.caption("Simulated pipeline of quotes across 10 partner accounts, 4 regions, and 3 customer segments. Includes list totals, applied discounts, net prices, gross margins, and compliance status.")

        def style_q_status(val):
            return {"Approved":        "color:#16a34a;font-weight:700;",
                    "Pending Review":  "color:#d97706;font-weight:700;",
                    "Policy Violation":"color:#dc2626;font-weight:700;"}.get(val,"")
        def style_q_margin(val):
            try:
                v = float(val)
                if v < 15: return "color:#dc2626;"
                if v < 25: return "color:#d97706;"
                return "color:#16a34a;"
            except: return ""
        def style_q_tier(val):
            return {"Platinum":"color:#6366f1;font-weight:700;",
                    "Gold":    "color:#f59e0b;font-weight:700;",
                    "Silver":  "color:#64748b;",
                    "Registered":"color:#94a3b8;"}.get(val,"")

        disp_q = quotes_df.copy()
        disp_q["Net Price"]   = disp_q["Net Price"].apply(lambda x: f"${x:,}")
        disp_q["List Total"]  = disp_q["List Total"].apply(lambda x: f"${x:,}")
        disp_q["Discount %"]  = disp_q["Discount %"].astype(str) + "%"
        disp_q["Gross Margin %"] = disp_q["Gross Margin %"].astype(str) + "%"

        styled_q2 = disp_q.style \
            .applymap(style_q_status, subset=["Status"]) \
            .applymap(style_q_tier,   subset=["Tier"])
        st.dataframe(styled_q2, use_container_width=True, height=400)

        # Stats
        st.markdown("#### Pipeline Statistics")
        ps1, ps2, ps3, ps4 = st.columns(4)
        ps1.metric("Total Pipeline",    f"${quotes_df['Net Price'].sum():,.0f}")
        ps2.metric("Avg Discount",      f"{quotes_df['Discount %'].mean():.1f}%")
        ps3.metric("Avg Gross Margin",  f"{quotes_df['Gross Margin %'].mean():.1f}%")
        ps4.metric("Policy Violations", len(quotes_df[quotes_df["Status"]=="Policy Violation"]))

        csv_qp = disp_q.to_csv(index=False)
        st.download_button("⬇ Export Quote Pipeline CSV", data=csv_qp,
                           file_name="PriceOps_QuotePipeline_Demo.csv", mime="text/csv")

    # ── UAT TEST CASES ───────────────────────
    elif ds == "🧪 UAT Test Cases":
        st.markdown("#### UAT Test Case Library — 8 Structured Tests")
        st.caption("Covers discount logic, volume pricing, policy enforcement, margin floors, product setup, and data integrity across 5 business units. Designed to mirror real CPQ and SAP UAT validation workflows.")

        uat_rows = []
        for tc in BUILT_IN_TESTS:
            uat_rows.append({
                "Test ID":      tc["id"],
                "Test Name":    tc["name"],
                "Business Unit":tc["bu"],
                "Category":     tc["category"],
                "Input Data":   str(tc["input"]),
                "Expected":     str(tc["expected"]),
            })
        uat_df = pd.DataFrame(uat_rows)

        def style_cat(val):
            return {"Discount Logic":    "color:#3b82f6;font-weight:700;",
                    "Volume Pricing":    "color:#6366f1;font-weight:700;",
                    "Policy Enforcement":"color:#dc2626;font-weight:700;",
                    "Margin Floors":     "color:#d97706;font-weight:700;",
                    "Product Setup":     "color:#16a34a;font-weight:700;",
                    "Data Integrity":    "color:#64748b;font-weight:700;"}.get(val,"")
        st.dataframe(uat_df.style.applymap(style_cat, subset=["Category"]),
                     use_container_width=True, height=320)

        # Category breakdown
        st.markdown("#### Test Coverage by Category")
        cat_counts_uat = uat_df["Category"].value_counts().reset_index()
        cat_counts_uat.columns = ["Category","Count"]
        fig_uat = px.pie(cat_counts_uat, names="Category", values="Count",
                         hole=0.5, color_discrete_sequence=px.colors.qualitative.Set2)
        fig_uat.update_layout(paper_bgcolor="white", font_color="#0f172a",
                              margin=dict(l=10,r=10,t=10,b=10), height=260)
        st.plotly_chart(fig_uat, use_container_width=True)

        csv_uat2 = uat_df.to_csv(index=False)
        st.download_button("⬇ Export UAT Test Library CSV", data=csv_uat2,
                           file_name="PriceOps_UATTestCases.csv", mime="text/csv")

    # ── AUDIT LOG ────────────────────────────
    elif ds == "🔍 Audit Log":
        st.markdown("#### Pricing Change Audit Log")
        st.caption("Tracks all pricing updates, discount overrides, SKU additions, and tier changes. Discount overrides are auto-flagged for compliance review. Designed to mirror SAP and Salesforce change tracking workflows.")

        al_df = pd.DataFrame(st.session_state.audit_log)

        def style_al(val):
            return {"Flagged": "color:#dc2626;font-weight:700;",
                    "Approved":"color:#16a34a;font-weight:700;"}.get(val,"")
        def style_action(val):
            return {"Discount override":"color:#dc2626;",
                    "Price updated":    "color:#3b82f6;",
                    "New SKU added":    "color:#16a34a;",
                    "Tier changed":     "color:#6366f1;"}.get(val,"")

        st.dataframe(al_df.style
                     .applymap(style_al,     subset=["Status"])
                     .applymap(style_action, subset=["Action"]),
                     use_container_width=True, height=260)

        # Action type breakdown
        st.markdown("#### Changes by Action Type")
        action_counts = al_df["Action"].value_counts().reset_index()
        action_counts.columns = ["Action","Count"]
        fig_al = px.bar(action_counts, x="Action", y="Count",
                        color="Count", color_continuous_scale="Blues", text="Count")
        fig_al.update_layout(paper_bgcolor="white", plot_bgcolor="white",
                             font_color="#0f172a", showlegend=False,
                             coloraxis_showscale=False,
                             margin=dict(l=10,r=10,t=10,b=10), height=240)
        fig_al.update_traces(textposition="outside")
        st.plotly_chart(fig_al, use_container_width=True)

        csv_al2 = al_df.to_csv(index=False)
        st.download_button("⬇ Export Audit Log CSV", data=csv_al2,
                           file_name="PriceOps_AuditLog_Demo.csv", mime="text/csv")
