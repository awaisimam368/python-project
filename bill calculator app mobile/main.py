import streamlit as st
import time
from google import genai

# ==================== CONFIGURATION ====================
GEMINI_API_KEY = st.secrets["AQ.Ab8RN6IgNSeq-PP5he6PF-djj9zvD0zFknXmzsdToKwkCrFbrQ"]
# =======================================================

def calculate_bill_pkr(total_units):
    slabs = [
        (100, 22.44), (100, 28.91), (100, 33.10), (100, 36.46),
        (100, 38.95), (100, 40.22), (100, 41.85), (float('inf'), 47.20)
    ]
    bill = 0
    remaining_units = total_units
    for limit, rate in slabs:
        if remaining_units > 0:
            units_in_slab = min(remaining_units, limit)
            bill += units_in_slab * rate
            remaining_units -= units_in_slab
    return bill + (bill * 0.18) + 500

# App Layout Configuration
st.set_page_config(page_title="WAPDA Smart Calculator", page_icon="⚡", layout="centered")

st.title("⚡ WAPDA AI Bill Auditor")
st.caption("Enter your household appliances below to audit your consumption:")

appliances = {
    "AC Inverter (1.5 Ton)": 1500,
    "AC Inverter (1.0 Ton)": 1000,
    "Air Cooler (Room Cooler)": 300,
    "Water Cooler / Dispenser": 400,
    "Microwave Oven": 1200,
    "Refrigerator / Fridge": 250,
    "Water Pump (Motor)": 750,
    "Ceiling Fan": 80,
    "LED Light Bulbs / Tubes": 18,
    "LED TV": 100,
    "Mobile Chargers": 15
}

# Generate UI inputs dynamically inside a clean form
ui_entries = {}
with st.form("appliance_form"):
    for app, watts in appliances.items():
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.write(f"**{app}** ({watts}W)")
        with col2:
            qty = st.number_input("Qty", min_value=0, value=0, key=f"qty_{app}", step=1)
        with col3:
            hours = st.number_input("Hrs/Day", min_value=0.0, max_value=24.0, value=0.0, key=f"hrs_{app}", step=0.5)
        ui_entries[app] = (qty, hours, watts)
        
    submit_btn = st.form_submit_button("Calculate & Run AI Audit")

# Form logic processing
if submit_btn:
    total_daily_kwh = 0
    summary_items = []
    
    for app, (qty, hours, watts) in ui_entries.items():
        if qty > 0 and hours > 0:
            daily_kwh = (watts / 1000) * hours * qty
            total_daily_kwh += daily_kwh
            summary_items.append(f"{app} (x{qty} @ {hours}hrs)")
            
    total_monthly_units = total_daily_kwh * 30
    final_bill = calculate_bill_pkr(total_monthly_units)
    
    # Render Math Results Card
    st.success(f"### Total Monthly Units: {total_monthly_units:.2f} kWh  \n### Estimated Bill: Rs. {final_bill:,.2f}")
    
    # Fetch AI Breakdown with Anti-Crash Retry Engine
    if total_monthly_units > 0:
        max_retries = 3
        ai_success = False
        
        # We place a single status container so updates happen cleanly on one line
        status_placeholder = st.empty()
        
        for attempt in range(max_retries):
            status_placeholder.info(f"⏳ Connecting to Gemini AI (Attempt {attempt + 1}/{max_retries})...")
            try:
                client = genai.Client(api_key=GEMINI_API_KEY)
                prompt = f"""
                Analyze this Pakistani home setup: {', '.join(summary_items)}. 
                Monthly units: {total_monthly_units:.2f}, Bill: Rs. {final_bill}. 
                Give 3 short, localized energy saving tips for a Pakistani household. No fluff.
                """
                response = client.models.generate_content(model="gemini-1.5-flash", contents=prompt)
                
                # Clear the loading text and print the response
                status_placeholder.empty()
                st.info(f"💡 **AI Audit Suggestions:**\n\n{response.text.strip()}")
                ai_success = True
                break  # Exit retry loop immediately on successful execution
                
            except Exception as ex:
                # If it's a 503 or network issue, wait 2 seconds before the next loop iteration
                if attempt < max_retries - 1:
                    time.sleep(2)
                else:
                    status_placeholder.empty()
                    st.error(f"❌ The AI server is heavily overloaded right now. Please try clicking the button again in a few seconds. (Error details: {ex})")
    else:
        st.warning("No active appliances found to audit.")
