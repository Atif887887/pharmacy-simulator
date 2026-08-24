import streamlit as st
import google.generativeai as genai
import json

st.set_page_config(page_title="Virtual Pharmacy Clinic", page_icon="💊", layout="centered")

# --- HIGH-CONTRAST NEON STYLING ---
st.markdown("""
<style>
.stApp {
    background-color: #080c10;
    color: #f1f5f9;
    font-family: 'Inter', sans-serif;
}
/* Glowing Header Title */
h1 {
    color: #38bdf8;
    text-shadow: 0 0 10px rgba(56, 189, 248, 0.4);
}
/* Interactive Medicine Cards */
div.stButton > button:first-child {
    background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
    color: #38bdf8;
    border: 2px solid #0284c7;
    border-radius: 12px;
    padding: 12px 20px;
    font-size: 16px;
    font-weight: 700;
    box-shadow: 0 4px 12px rgba(2, 132, 199, 0.3);
    transition: all 0.2s ease-in-out;
}
div.stButton > button:first-child:hover {
    background: #0284c7;
    color: #ffffff;
    border-color: #38bdf8;
    box-shadow: 0 0 20px rgba(56, 189, 248, 0.7);
    transform: translateY(-2px);
}
/* Card Containers for Patient Profile */
div.element-container {
    color: #f1f5f9;
}
.stTextInput > div > div > input {
    background-color: #1e293b;
    color: #ffffff;
    border: 1px solid #0284c7;
    border-radius: 8px;
}
div[data-testid="stMetricValue"] {
    color: #34d399 !important;
    font-weight: 800;
}
</style>
""", unsafe_allow_html=True)

if 'score' not in st.session_state:
    st.session_state.score = 500
if 'treated' not in st.session_state:
    st.session_state.treated = 0
if 'patient' not in st.session_state:
    st.session_state.patient = None
if 'selected_drug' not in st.session_state:
    st.session_state.selected_drug = "None selected"

with st.sidebar:
    st.header("⚙️ Clinic Settings")
    api_key = st.text_input("Gemini API Key", type="password", placeholder="Paste key here...")
    st.markdown("---")
    st.header("🏆 Career Stats")
    st.metric(label="In-Game Funds", value=f"${st.session_state.score}")
    st.metric(label="Patients Treated", value=st.session_state.treated)
    st.markdown("---")
    category = st.selectbox("Shift Category", ["Antibiotics", "Analgesics/Antipyretics", "ANS", "CNS", "Cardiovascular", "Gastrointestinal"])

st.title("💊 Virtual Pharmacy Clinic")

if not api_key:
    st.warning("👈 Please enter your Gemini API Key in the sidebar to open your clinic doors.")
    st.stop()

genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-3.6-flash')

def generate_patient():
    prompt = f"""
    Act as a clinical pharmacy professor. Create a complex patient case for category: {category}.
    Write the symptoms, patient explanation, and doctor's diagnostic reasoning strictly in ROMAN URDU (Urdu written in English alphabets, like 'patient ko bukhar hai'), while keeping medical terms, drug names, and lab values in English.
    Output ONLY valid JSON with this exact structure:
    {{
      "name": "string",
      "age": 34,
      "bp": "string",
      "pulse": "string",
      "temp": "string",
      "allergies": "string",
      "symptoms": "string in Roman Urdu with English medical terms",
      "labs": "string",
      "diagnosisApproach": "string in Roman Urdu with English medical terms",
      "imageType": "xray", 
      "shelfDrugs": ["Drug 1", "Drug 2", "Drug 3", "Drug 4"],
      "correctDrug": "string",
      "correctDose": "string"
    }}
    (Note: imageType can be 'xray', 'skin', 'blood', or 'general')
    """
    try:
        response = model.generate_content(prompt)
        text = response.text
        start = text.find('{')
        end = text.rfind('}') + 1
        st.session_state.patient = json.loads(text[start:end])
        st.session_state.selected_drug = "None selected"
    except Exception as e:
        st.error(f"System Error: {str(e)}")

if st.button("Call Next Patient 🩺", use_container_width=True):
    generate_patient()

if st.session_state.patient:
    p = st.session_state.patient
    
    st.markdown("### 👤 Patient Profile")
    with st.container():
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown(f"**Naam:** {p.get('name', 'N/A')} | **Umar:** {p.get('age', 'N/A')} saal")
            if str(p.get('allergies', 'none')).lower() != "none":
                st.error(f"⚠️ **ALLERGY ALERT:** {p.get('allergies', 'None')}")
            else:
                st.success("✅ **Allergies:** Koi nahi hai")
                
            c1, c2, c3 = st.columns(3)
            c1.metric("BP", p.get('bp', '--'))
            c2.metric("Pulse", p.get('pulse', '--'))
            c3.metric("Temp", p.get('temp', '--'))
            
            st.write(f"**Symptoms (Halat):** {p.get('symptoms', '--')}")
            st.write(f"**Lab Tests:** {p.get('labs', '--')}")
            
        with col2:
            st.markdown("**Visual Clinical Aid**")
            img_type = p.get('imageType', 'general')
            if img_type == 'xray':
                img_url = "https://images.unsplash.com/photo-1516549655169-df83a0774514?w=400&q=80" # Chest Xray
            elif img_type == 'skin':
                img_url = "https://images.unsplash.com/photo-1584515979956-d9f6e5d09982?w=400&q=80" # Rash/Skin
            elif img_type == 'blood':
                img_url = "https://images.unsplash.com/photo-1579165466741-7f35e4755660?w=400&q=80" # Microscope/Blood
            else:
                img_url = "https://images.unsplash.com/photo-1584515979956-d9f6e5d09982?w=400&q=80"
                
            st.image(img_url, width="stretch")
            st.caption("Clinical Scan Report")

        with st.expander("🩺 Doctor Ki Diagnostic Reasoning (Roman Urdu)", expanded=True):
            st.info(p.get('diagnosisApproach', '--'))

    st.markdown("---")
    st.markdown("### 💊 Medicine Counter (Select Tablet/Capsule)")
    
    shelf = p.get('shelfDrugs', [])
    if shelf:
        cols = st.columns(len(shelf))
        for idx, drug in enumerate(shelf):
            with cols[idx]:
                if st.button(f"💊 {drug}", key=f"drug_{idx}", use_container_width=True):
                    st.session_state.selected_drug = drug

    st.markdown(f"**Aap ki Selected Medicine:** `✨ {st.session_state.selected_drug}`")
    
    dosage_input = st.text_input("Prescribed Dosage (e.g. 500mg TDS)")
    pharma_input = st.text_input("Pharmacognosy Alternative (Herbal Source & Active Constituent)")
    
    if st.button("Administer Treatment 🚀", use_container_width=True):
        if st.session_state.selected_drug == "None selected":
            st.warning("Pehle shelf me se koi medicine select karein!")
        else:
            with st.spinner("Senior Pharmacist prescription check kar rahe hain..."):
                grading_prompt = f"""
                Grade this Pharm-D student's clinical treatment.
                Patient Case: {json.dumps(p)}
                Student's Choices -> Drug: {st.session_state.selected_drug}, Dosage: {dosage_input}, Pharmacognosy: {pharna_input if 'pharna_input' in locals() else pharma_input}.
                Check for correctness, proper dosing, and fatal allergy contraindications.
                Output ONLY valid JSON: 
                {{
                  "isCorrect": boolean,
                  "fatalError": boolean,
                  "points": number,
                  "feedback": "string explaining in Roman Urdu why it is correct or wrong"
                }}
                """
                try:
                    eval_res = model.generate_content(grading_prompt)
                    text = eval_res.text
                    grading = json.loads(text[text.find('{'):text.rfind('}')+1])
                    
                    st.session_state.score += grading.get('points', 0)
                    
                    if grading.get('fatalError', False):
                        st.error(f"🚨 **FATAL ERROR:** {grading.get('feedback', '')}")
                    elif grading.get('isCorrect', False):
                        st.session_state.treated += 1
                        st.success(f"✅ **BOHOT ACHAY (SUCCESS):** {grading.get('feedback', '')}")
                    else:
                        st.warning(f"⚠️ **GHALAT (INCORRECT):** {grading.get('feedback', '')}")
                        
                except Exception as e:
                    st.error(f"Grading Error: {str(e)}")
else:
    st.info("👆 Upar **'Call Next Patient 🩺'** button daba kar apna pehla case shuru karein!")
