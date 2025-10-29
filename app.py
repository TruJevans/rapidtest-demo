# app.py — RapidTest.ai Demo (fully working + About section)

import streamlit as st
import numpy as np, pandas as pd, matplotlib.pyplot as plt
from io import BytesIO
from zipfile import ZipFile
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors

# ---------- PAGE CONFIG ----------
st.set_page_config(page_title="RapidTest.ai Demo", layout="wide", page_icon="📈")

st.markdown("""
<style>
/* --- Page base colors --- */
.stApp, .block-container {
    background-color: #ffffff !important;
    color: #1f3b70 !important;
}

/* --- Form labels --- */
[data-testid="stForm"] label,
[data-testid="stForm"] [data-testid="stSliderLabel"],
[data-testid="stForm"] [data-testid="stNumberInputLabel"],
[data-testid="stForm"] [data-testid="stSelectboxLabel"],
[data-testid="stForm"] div.row-widget.stRadio label {
    color: #1f3b70 !important;
    font-weight: 600 !important;
    font-size: 0.95rem !important;
}

/* --- Sliders --- */
[data-baseweb="slider"] div[role="slider"],
[data-baseweb="slider"] div[role="slider"]::before {
    background-color: #1f3b70 !important;
}
[data-baseweb="slider"] span[data-testid="stThumbValue"] {
    background-color: #1f3b70 !important;
    color: white !important;
    border-radius: 4px !important;
}

/* --- Widget spacing --- */
.stSlider, .stNumberInput, .stSelectbox {
    margin-bottom: 1.4rem !important;
}

/* --- About section --- */
.about-box {
    background-color: #f4f7fb;
    border-radius: 12px;
    padding: 20px 25px;
    margin-top: 30px;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
}
.about-box h2 {
    color: #1f3b70;
    margin-bottom: 0.5em;
}
.about-box p, .about-box li {
    color: #1f3b70;
    font-size: 0.95rem;
    line-height: 1.55;
}
</style>
""", unsafe_allow_html=True)

# ---------- HEADER ----------
st.markdown("## Hybrid SaaS Forecast Simulator")

# ---------- ABOUT SECTION ----------
st.markdown("""
<div class="about-box">
<h2>💡 About RapidTest.ai</h2>
<p><b>RapidTest.ai</b> helps SaaS companies that sell tools to small and mid-size e-commerce brands.</p>
<p>Instead of producing a single marketing video, RapidTest.ai provides an ongoing <b>rapid-testing content service</b> that:</p>
<ul>
<li>Creates multiple short demo variants showing how software fixes common e-commerce pain points.</li>
<li>Tracks engagement (watch time, clicks, trial sign-ups) and automatically iterates weekly.</li>
<li>Turns each SaaS contract into a pipeline of many SMB customers via co-branded clips.</li>
</ul>
</div>
""", unsafe_allow_html=True)

# ---------- USER INPUT FORM ----------
with st.form("forecast_form"):
    col1, col2, col3 = st.columns(3)
    start_clients = col1.number_input("Starting SaaS Clients", min_value=1, step=1)
    months = col2.slider("Months to Forecast", 3, 24, 12)
    subscription_price = col3.number_input("Subscription Price per Client ($/mo)", min_value=0.0, step=100.0)
    merchants_per = col1.number_input("Merchants per Client", min_value=0, step=10)
    upsell = col2.number_input("Upsell per Merchant ($/mo)", min_value=0.0, step=5.0)
    growth = col3.slider("Monthly Growth Rate (%)", 0.0, 50.0, 15.0)
    churn = col1.slider("Monthly Churn Rate (%)", 0.0, 20.0, 6.0)
    sensitivity = col2.slider("Engagement Sensitivity (+/- per 10%)", 0.0, 0.1, 0.03)
    sims = col3.slider("Monte Carlo Simulations", 100, 2000, 1000, step=100)
    submitted = st.form_submit_button("Run Forecast")

# ---------- FORECAST ENGINE ----------
if submitted:
    with st.spinner("Running simulations..."):
        clients = [start_clients]
        mrr = []
        for _ in range(months):
            rev_per = subscription_price + merchants_per * upsell
            mrr.append(clients[-1] * rev_per)
            clients.append(clients[-1] * (1 + growth/100 - churn/100))
        det = pd.DataFrame({"Month": range(1, months+1), "MRR": mrr})
        det["Cumulative"] = det["MRR"].cumsum()

        stoch = []
        for _ in range(sims):
            c = [start_clients]; vals = []
            for _ in range(months):
                shock = np.random.uniform(-0.1, 0.1)
                adj = growth/100 + shock*sensitivity
                c.append(max(c[-1]*(1+adj - churn/100), 0))
                vals.append(c[-1]*(subscription_price + merchants_per*upsell))
            stoch.append(vals)
        arr = np.array(stoch)
        mean = arr.mean(axis=0)
        low, high = np.percentile(arr, [10, 90], axis=0)
        cum_mean = np.cumsum(mean)

    # ---------- CHARTS ----------
    with st.spinner("Building charts..."):
        fig1, ax1 = plt.subplots(figsize=(6,4))
        ax1.plot(det["Month"], det["MRR"], label="Deterministic", color="#2a6fd3", lw=2)
        ax1.plot(det["Month"], mean, label="Stochastic Mean", ls="--", color="#1f3b70")
        ax1.fill_between(det["Month"], low, high, color="#9cbcf2", alpha=0.3)
        ax1.set_title("Monthly Recurring Revenue", color="#1f3b70")
        ax1.set_xlabel("Month"); ax1.set_ylabel("MRR ($)")
        ax1.legend(); ax1.grid(alpha=.3)

        fig2, ax2 = plt.subplots(figsize=(6,4))
        ax2.plot(det["Month"], det["Cumulative"], label="Deterministic", color="#1f3b70", lw=2)
        ax2.plot(det["Month"], cum_mean, label="Stochastic Cumulative", ls="--", color="#4c8dd9")
        ax2.set_title("Cumulative Revenue", color="#1f3b70")
        ax2.set_xlabel("Month"); ax2.set_ylabel("Revenue ($)")
        ax2.legend(); ax2.grid(alpha=.3)

        colA, colB = st.columns(2)
        colA.pyplot(fig1, use_container_width=True)
        colB.pyplot(fig2, use_container_width=True)

    # ---------- AI SUMMARY ----------
    uplift = (cum_mean[-1]-det["Cumulative"].iloc[-1]) / det["Cumulative"].iloc[-1] * 100 if det["Cumulative"].iloc[-1] > 0 else 0
    insight = f"RapidTest.ai outperformed baseline projections by {uplift:,.1f}% through iterative engagement optimization."
    st.markdown(f"#### Insight\n{insight}")

    # ---------- PDF + ZIP GENERATION ----------
    with st.spinner("Generating Investor Deck..."):
        start, end = det["MRR"].iloc[0], det["MRR"].iloc[-1]
        arr_est = end * 12

        def make_pdf(path, title, desc, metrics):
            c = canvas.Canvas(path, pagesize=letter)
            w, h = letter
            c.setFillColorRGB(0.12, 0.23, 0.44)
            c.rect(0, h-80, w, 80, fill=True, stroke=False)
            c.setFillColor(colors.white)
            c.setFont("Helvetica-Bold", 22)
            c.drawString(50, h-55, title)
            c.setFont("Helvetica", 12)
            c.drawString(50, h-90, desc)
            c.setFillColor(colors.black)
            y = h - 120
            c.setFont("Helvetica", 11)
            for m in metrics:
                c.drawString(60, y, m)
                y -= 15
            c.save()

        make_pdf("investor_brief.pdf", "RapidTest.ai Forecast Summary",
                 "Forecast Summary — Hybrid SaaS Video Optimization",
                 [f"Starting MRR: ${start:,.0f}",
                  f"12-Month Projected MRR: ${end:,.0f}",
                  f"Annual Run-Rate: ${arr_est:,.0f}",
                  f"Stochastic Uplift: +{uplift:,.1f}%"])

        make_pdf("partner_sales_sheet.pdf", "Scale Your SaaS Clients with RapidTest.ai",
                 "We produce and test multiple video variants weekly using data-driven iteration.",
                 [f"Growth Rate: {growth:.1f}%",
                  f"Churn: {churn:.1f}%",
                  f"12-Month ARR: ${arr_est:,.0f}",
                  f"Engagement Uplift: +{uplift:,.1f}%"])

        buffer = BytesIO()
        with ZipFile(buffer, "w") as z:
            z.write("investor_brief.pdf")
            z.write("partner_sales_sheet.pdf")

        st.download_button(
            label="📁 Download Investor Deck (ZIP)",
            data=buffer.getvalue(),
            file_name="RapidTest_Forecast_Deck.zip",
            mime="application/zip"
        )
else:
    st.info("Adjust parameters and click **Run Forecast** to generate projections.")
