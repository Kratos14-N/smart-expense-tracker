import sqlite3
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="Smart Expense Tracker", page_icon="💰", layout="wide")

SCRIPT_DIR = Path(__file__).resolve().parent
DB_PATH = SCRIPT_DIR / "expenses.db"
CATEGORIES = ["Food", "Rent", "Entertainment", "Utilities", "Transport", "Shopping", "Health", "Other"]
CATEGORY_COLORS = {
    "Food": "#f59e0b",
    "Rent": "#8b5cf6",
    "Entertainment": "#ec4899",
    "Utilities": "#0ea5e9",
    "Transport": "#22c55e",
    "Shopping": "#f97316",
    "Health": "#10b981",
    "Other": "#64748b",
}
CURRENCY_OPTIONS = {
    "INR": {"symbol": "₹", "rate_to_inr": 1.0},
    "USD": {"symbol": "$", "rate_to_inr": 0.012},
    "EUR": {"symbol": "€", "rate_to_inr": 0.011},
    "GBP": {"symbol": "£", "rate_to_inr": 0.0098},
    "JPY": {"symbol": "¥", "rate_to_inr": 1.64},
}
THEME_PALETTES = {
    "Light": {
        "page": "#345c55", "sidebar": "#294b45", "surface": "#afcfc4",
        "control": "#b4d2c9", "control_text": "#183b35", "text": "#f1f5ef",
        "surface_text": "#183b35", "muted_text": "#315850", "border": "#83aa9e",
        "button": "#34786e", "button_text": "#ffffff", "track": "#28443e",
        "progress": "#ff9f5a", "chart": "#345c55", "chart_text": "#f1f5ef",
        "bar": "#ffd166", "bar_muted": "#79b7a4", "line": "#f2a65a",
        "alert": "#294b45", "placeholder": "#526b64",
    },
    "Dark": {
        "page": "#15232a", "sidebar": "#0d1a20", "surface": "#1c2d33",
        "control": "#263940", "control_text": "#eef4f1", "text": "#e8f0ec",
        "surface_text": "#e8f0ec", "muted_text": "#b7c8c2", "border": "#39545a",
        "button": "#178578", "button_text": "#ffffff", "track": "#263941",
        "progress": "#53cde6", "chart": "#1b2c32", "chart_text": "#e8f0ec",
        "bar": "#46d6b0", "bar_muted": "#3e827a", "line": "#f2c363",
        "alert": "#20383a", "placeholder": "#b7c8c2",
    },
    "Luxury Dark": {
        "page": "#1c1714", "sidebar": "#100d0b", "surface": "#29211c",
        "control": "#30251f", "control_text": "#f5eadb", "text": "#f5eadb",
        "surface_text": "#f5eadb", "muted_text": "#d0bda7", "border": "#5a4536",
        "button": "#9a6035", "button_text": "#fff7ec", "track": "#3b2e25",
        "progress": "#f0bd63", "chart": "#241c18", "chart_text": "#f5eadb",
        "bar": "#e5ad59", "bar_muted": "#806044", "line": "#f3d18d",
        "alert": "#35281f", "placeholder": "#d0bda7",
    },
}


def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                description TEXT,
                date TEXT NOT NULL
            )
            """
        )
        conn.commit()


def fetch_expenses():
    with sqlite3.connect(DB_PATH) as conn:
        df = pd.read_sql_query("SELECT * FROM expenses ORDER BY date DESC, id DESC", conn)

    if df.empty:
        return df

    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    return df


def add_expense(amount, category, description, expense_date, currency="INR"):
    amount = float(amount)
    if amount <= 0:
        raise ValueError("Amount must be greater than 0.")

    converted_amount = amount / CURRENCY_OPTIONS[currency]["rate_to_inr"]

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT INTO expenses (amount, category, description, date) VALUES (?, ?, ?, ?)",
            (converted_amount, category, description, expense_date.isoformat()),
        )
        conn.commit()


def delete_expense(expense_id):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
        conn.commit()


def clear_all_expenses():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM expenses")
        conn.commit()


def format_currency(value, currency):
    symbol = CURRENCY_OPTIONS[currency]["symbol"]
    return f"{symbol}{value:,.2f}"


def convert_to_currency(amount, currency):
    exchange_rate = CURRENCY_OPTIONS[currency]["rate_to_inr"]
    return amount * exchange_rate


def render_pie_chart(category_totals, currency, palette):
    values = category_totals.tolist()
    labels = category_totals.index.tolist()
    colors = [CATEGORY_COLORS.get(category, "#64748b") for category in labels]
    fig = go.Figure()

    if values:
        fig.add_trace(go.Pie(
            labels=labels,
            values=values,
            hole=0.7,
            sort=False,
            direction="clockwise",
            rotation=90,
            pull=[0.035 if value == max(values) else 0 for value in values],
            marker={"colors": colors, "line": {"color": palette["chart"], "width": 2}},
            textinfo="percent",
            textposition="inside",
            insidetextfont={"color": "#ffffff", "size": 11},
            customdata=[format_currency(value, currency) for value in values],
            hovertemplate="<b>%{label}</b><br>%{customdata}<br>%{percent}<extra></extra>",
            showlegend=False,
        ))
        fig.add_annotation(
            x=0.5, y=0.5, xref="paper", yref="paper", showarrow=False,
            text=f"TOTAL SPEND<br><b>{format_currency(sum(values), currency)}</b>",
            font={"family": "Source Sans, sans-serif", "size": 12, "color": palette["chart_text"]},
            align="center",
        )
    else:
        fig.add_annotation(
            x=0.5, y=0.5, xref="paper", yref="paper", showarrow=False,
            text="No matching expenses", font={"size": 12, "color": palette["chart_text"]},
        )

    fig.update_layout(
        height=290,
        margin={"l": 8, "r": 8, "t": 8, "b": 8},
        paper_bgcolor=palette["chart"],
        plot_bgcolor=palette["chart"],
        font={"family": "Source Sans, sans-serif", "color": palette["chart_text"]},
        hoverlabel={"bgcolor": palette["surface"], "bordercolor": palette["border"], "font": {"color": palette["surface_text"]}},
        uniformtext={"minsize": 9, "mode": "hide"},
    )
    return fig


def render_monthly_chart(monthly_totals, currency, monthly_limit, palette):
    months = monthly_totals["Month"].tolist()
    amounts = monthly_totals["Total Amount"].tolist()
    current_month = pd.Timestamp.today().strftime("%Y-%m")
    highlight_index = months.index(current_month) if current_month in months else len(months) - 1
    bar_colors = [palette["bar_muted"]] * len(months)
    if bar_colors:
        bar_colors[highlight_index] = palette["bar"]

    currency_symbol = CURRENCY_OPTIONS[currency]["symbol"]
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=months,
        y=amounts,
        marker={"color": bar_colors, "line": {"color": palette["chart"], "width": 1.5}},
        text=[format_currency(value, currency) for value in amounts],
        textposition="outside",
        textfont={"color": palette["chart_text"], "size": 11},
        customdata=[format_currency(value, currency) for value in amounts],
        hovertemplate="<b>%{x}</b><br>Spent: %{customdata}<extra></extra>",
        cliponaxis=False,
    ))

    if monthly_limit > 0:
        fig.add_hline(
            y=monthly_limit,
            line_color=palette["progress"],
            line_dash="dot",
            line_width=2,
            annotation_text=f"Monthly limit {format_currency(monthly_limit, currency)}",
            annotation_position="top right",
            annotation_font_color=palette["chart_text"],
            annotation_bgcolor=palette["chart"],
        )

    upper_value = max(max(amounts, default=0), monthly_limit if monthly_limit > 0 else 0)
    fig.update_layout(
        height=380,
        margin={"l": 58, "r": 24, "t": 40, "b": 52},
        paper_bgcolor=palette["chart"],
        plot_bgcolor=palette["chart"],
        font={"family": "Source Sans, sans-serif", "color": palette["chart_text"]},
        hovermode="x",
        hoverlabel={"bgcolor": palette["surface"], "bordercolor": palette["border"], "font": {"color": palette["surface_text"]}},
        showlegend=False,
        bargap=0.42,
    )
    fig.update_xaxes(
        type="category",
        categoryorder="array",
        categoryarray=months,
        tickangle=-25,
        showgrid=False,
        showline=True,
        linecolor=palette["border"],
        tickfont={"color": palette["chart_text"]},
    )
    fig.update_yaxes(
        title_text=f"Amount ({currency_symbol})",
        range=[0, upper_value * 1.2 if upper_value > 0 else 1],
        tickprefix=currency_symbol,
        separatethousands=True,
        showgrid=True,
        gridcolor="rgba(255,255,255,0.12)",
        zeroline=False,
    )
    return fig


def render_category_legend(category_totals, currency, palette):
    if category_totals.empty:
        return

    total = category_totals.sum()
    for category, amount in category_totals.items():
        color = CATEGORY_COLORS.get(category, "#64748b")
        st.markdown(
            f"""
            <div style="display:grid; grid-template-columns:12px minmax(0,1fr) auto; align-items:center; gap:8px;
                padding:7px 3px; border-bottom:1px solid {palette['border']}; color:{palette['text']};">
                <span style="width:10px; height:10px; border-radius:50%; background:{color};"></span>
                <span style="min-width:0; display:flex; justify-content:space-between; gap:8px; font-size:0.8rem;">
                    <span style="overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">{category}</span>
                    <span style="color:{palette['muted_text']};">{amount / total:.0%}</span>
                </span>
                <strong style="font-size:0.78rem; white-space:nowrap; color:{palette['text']};">{format_currency(amount, currency)}</strong>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_stat_card(title, value, accent):
    st.markdown(
        f"""
        <div style="
            background: {accent};
            border-radius: 14px; padding: 16px 18px; border: 1px solid rgba(255,255,255,0.65);
            box-shadow: 0 10px 20px rgba(123, 97, 255, 0.10); margin-bottom: 14px;
            min-height: 112px; box-sizing: border-box;
        ">
            <div style="font-size: 0.75rem; letter-spacing: 0.08em; text-transform: uppercase; color: #475569; font-weight: 700;">{title}</div>
            <div style="font-size: 1.45rem; line-height: 1.25; font-weight: 800; color: #0f172a; margin-top: 8px; overflow-wrap: anywhere;">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_transaction_card(row, palette):
    tag_color = CATEGORY_COLORS.get(row["Category"], "#64748b")
    st.markdown(
        f"""
        <div style="
            background: {palette['surface']};
            border: 1px solid {palette['border']}; border-radius: 14px; padding: 14px 16px;
            box-shadow: 0 5px 15px rgba(148, 163, 184, 0.12); margin-bottom: 10px;
        ">
            <div style="display:flex; justify-content:space-between; align-items:center; gap:12px;">
                <div style="flex:1; min-width:0;">
                    <div style="font-size: 0.7rem; letter-spacing: 0.08em; text-transform: uppercase; color:{palette['muted_text']}; font-weight:700; margin-bottom:5px;">{row['Date']}</div>
                    <div style="display:flex; align-items:center; gap:8px; flex-wrap:wrap;">
                        <span style="display:inline-block; background:{tag_color}; color:#fff; border-radius:999px; padding:5px 10px; font-size:0.72rem; font-weight:700;">{row['Category']}</span>
                    </div>
                    <div style="font-size: 0.88rem; color:{palette['muted_text']}; margin-top: 6px;">{row['Description']}</div>
                </div>
                <div style="display:flex; align-items:center; gap:12px;">
                    <div style="font-size:1.05rem; font-weight:800; color:{palette['surface_text']}; white-space:nowrap;">{row['Amount']}</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def apply_theme(mode):
    palette = THEME_PALETTES.get(mode, THEME_PALETTES["Light"])
    return f"""
    <style>
        .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"], .main {{
            background: {palette['page']} !important;
            color: {palette['text']} !important;
        }}
        .block-container {{ padding-top: 2rem; padding-bottom: 2rem; }}
        h1, h2, h3, .stCaption, [data-testid="stWidgetLabel"], [data-testid="stWidgetLabel"] *,
        [data-testid="stMetricLabel"], [data-testid="stMetricLabel"] * {{ color: {palette['text']} !important; }}
        div[data-testid="stMetricValue"] {{ font-size: 1.5rem; color: {palette['text']} !important; }}
        [data-testid="stSidebar"] {{ background: {palette['sidebar']} !important; }}
        [data-testid="stSidebar"] h2, [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] [data-testid="stWidgetLabel"],
        [data-testid="stSidebar"] [data-testid="stWidgetLabel"] * {{ color: {palette['text']} !important; }}
        [data-baseweb="select"] > div, [data-baseweb="input"] > div,
        [data-baseweb="textarea"] > div {{ background: {palette['control']} !important; }}
        input, textarea, [data-baseweb="select"] div {{ color: {palette['control_text']} !important; }}
        input, textarea {{ background: {palette['control']} !important; }}
        input::placeholder, textarea::placeholder {{ color: {palette['placeholder']} !important; opacity: 1; }}
        .stButton > button {{ border-radius: 10px; font-weight: 650; border-color: {palette['button']}; background: {palette['button']}; color: {palette['button_text']}; }}
        .stButton > button:hover {{ filter: brightness(1.12); border-color: {palette['button']}; color: {palette['button_text']}; }}
        .stAlert {{ border-radius: 12px; background: {palette['alert']}; color: {palette['text']}; }}
        .stDataFrame {{ background: {palette['surface']}; }}
    </style>
    """


init_db()

st.title("💰 Smart Expense Tracker")
st.caption("Track spending, review trends, and stay in control of your budget.")

with st.sidebar:
    st.header("Add New Expense")
    theme_mode = st.selectbox("Theme", ["Light", "Dark", "Luxury Dark"], index=0)
    st.markdown(apply_theme(theme_mode), unsafe_allow_html=True)

    entry_currency = st.selectbox("Entry Currency:", list(CURRENCY_OPTIONS.keys()), index=0, key="entry_currency")
    entry_symbol = CURRENCY_OPTIONS[entry_currency]["symbol"]
    amount = st.number_input(f"Amount ({entry_symbol}):", min_value=0.01, value=250.0, step=1.0, format="%.2f")
    category = st.selectbox("Category:", CATEGORIES)
    description = st.text_input("Description:", placeholder="Dinner with friends")
    expense_date = st.date_input("Date:", value=pd.Timestamp.today().date())

    if st.button("Log Expense", width="stretch", type="primary"):
        try:
            add_expense(amount, category, description.strip() or "No description", expense_date, currency=entry_currency)
            st.success("Expense logged successfully!")
            st.rerun()
        except ValueError as exc:
            st.error(str(exc))

    st.divider()

    monthly_limit = st.number_input(
        "Monthly Spending Limit:",
        min_value=0.0,
        value=5000.0,
        step=100.0,
        format="%.2f",
        help="Set a monthly cap and track remaining available budget.",
    )

    if st.button("Delete All Data", width="stretch", type="secondary"):
        clear_all_expenses()
        st.warning("All expenses were deleted.")
        st.rerun()


df = fetch_expenses()

if df.empty:
    st.info("No expenses logged yet. Use the sidebar to add your first expense.")
    st.stop()

display_currency = st.selectbox("Display Currency:", list(CURRENCY_OPTIONS.keys()), index=0, key="display_currency")
theme_palette = THEME_PALETTES[theme_mode]

converted_df = df.copy()
converted_df["amount"] = converted_df["amount"].apply(lambda value: convert_to_currency(value, display_currency))

monthly_total = converted_df["amount"].sum()
average_expense = converted_df["amount"].mean()
transaction_count = len(converted_df)
most_expensive = converted_df.loc[converted_df["amount"].idxmax()]

col1, col2, col3, col4 = st.columns(4)
with col1:
    render_stat_card("Total Spent", format_currency(monthly_total, display_currency), "linear-gradient(135deg, #70b29f 0%, #a4cdbd 100%)")
with col2:
    render_stat_card("Average", format_currency(average_expense, display_currency), "linear-gradient(135deg, #d3944f 0%, #e8bd7e 100%)")
with col3:
    render_stat_card("Transactions", str(transaction_count), "linear-gradient(135deg, #689eb5 0%, #9fc5d1 100%)")
with col4:
    render_stat_card("Largest", format_currency(most_expensive["amount"], display_currency), "linear-gradient(135deg, #c67361 0%, #dfa18b 100%)")

current_month = pd.Timestamp.today().to_period("M")
current_month_expenses = converted_df[converted_df["date"].dt.to_period("M") == current_month]
monthly_budget_spend = current_month_expenses["amount"].sum()
remaining_budget = monthly_limit - monthly_budget_spend
budget_progress = min(max(monthly_budget_spend / monthly_limit, 0.0), 1.0) if monthly_limit > 0 else 0.0

st.subheader("Monthly Budget")
if monthly_limit > 0:
    budget_percent = budget_progress * 100
    st.markdown(
        f"""
        <div role="progressbar" aria-label="Monthly budget used" aria-valuemin="0" aria-valuemax="100"
            aria-valuenow="{budget_percent:.1f}"
            aria-valuetext="{format_currency(monthly_budget_spend, display_currency)} spent of {format_currency(monthly_limit, display_currency)}"
            style="width:100%; height:14px; overflow:hidden; background:{theme_palette['track']}; border:1px solid {theme_palette['border']}; border-radius:999px; box-sizing:border-box;">
            <div style="height:100%; width:{budget_percent:.2f}%; background:{theme_palette['progress']}; border-radius:inherit; transition:width 0.45s ease;"></div>
        </div>
        <div style="display:flex; justify-content:space-between; gap:12px; flex-wrap:wrap; margin-top:8px; color:{theme_palette['muted_text']}; font-size:0.88rem;">
            <span>{format_currency(monthly_budget_spend, display_currency)} spent of {format_currency(monthly_limit, display_currency)}</span>
            <strong style="color:{theme_palette['text']};">{budget_percent:.0f}% used</strong>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if remaining_budget >= 0:
        st.success(f"You have {format_currency(remaining_budget, display_currency)} remaining for {current_month.strftime('%B %Y')}.")
    else:
        st.warning(f"You are {format_currency(abs(remaining_budget), display_currency)} over your monthly limit for {current_month.strftime('%B %Y')}.")
else:
    st.info("Set a monthly spending limit to track your budget progress.")

st.subheader("Expense Overview")
filter_col, _ = st.columns([1, 3])
with filter_col:
    selected_category = st.selectbox("Filter by category", ["All", *CATEGORIES])

if selected_category != "All":
    filtered_df = converted_df[converted_df["category"] == selected_category].copy()
else:
    filtered_df = converted_df.copy()

filtered_df = filtered_df.sort_values("date", ascending=False).reset_index(drop=True)
filtered_df["date"] = filtered_df["date"].dt.strftime("%Y-%m-%d")

chart_col, table_col = st.columns([1.1, 1.9])

with chart_col:
    category_totals = filtered_df.groupby("category")["amount"].sum().sort_values(ascending=False)
    st.subheader("Spending by Category")
    st.plotly_chart(
        render_pie_chart(category_totals, display_currency, theme_palette),
        width="stretch",
        theme=None,
        config={"displaylogo": False, "responsive": True},
        key="category-spend-donut",
    )
    render_category_legend(category_totals, display_currency, theme_palette)

with table_col:
    st.subheader("Recent Transactions")
    display_df = filtered_df[["date", "category", "amount", "description", "id"]].copy()
    display_df.columns = ["Date", "Category", "Amount", "Description", "id"]
    display_df["Amount"] = display_df["Amount"].map(lambda value: format_currency(value, display_currency))

    if display_df.empty:
        st.info("No transactions match the current filter.")
    else:
        for _, row in display_df.iterrows():
            card_col, delete_col = st.columns([4.5, 1.1])
            with card_col:
                render_transaction_card(row, theme_palette)
            with delete_col:
                if st.button("Delete", key=f"delete_{row['id']}", type="secondary", use_container_width=True):
                    delete_expense(int(row["id"]))
                    st.success("Transaction deleted.")
                    st.rerun()
            st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

st.subheader("Monthly Spending Trend")
monthly_df = converted_df.copy()
monthly_df["month"] = monthly_df["date"].dt.to_period("M").astype(str)
monthly_totals = monthly_df.groupby("month", as_index=False)["amount"].sum()
monthly_totals.columns = ["Month", "Total Amount"]
st.plotly_chart(
    render_monthly_chart(monthly_totals, display_currency, monthly_limit, theme_palette),
    width="stretch",
    theme=None,
    config={"displaylogo": False, "responsive": True},
    key="monthly-spending-chart",
)

st.subheader("Budget Snapshot")
category_summary = converted_df.groupby("category")["amount"].sum().sort_values(ascending=False)
summary_df = pd.DataFrame({
    "Category": category_summary.index,
    "Total": category_summary.values,
})
summary_df["Total"] = summary_df["Total"].map(lambda value: format_currency(value, display_currency))
st.dataframe(summary_df, hide_index=True, width="stretch")
