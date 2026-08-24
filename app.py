import streamlit as st
import google.generativeai as genai
import json

st.set_page_config(page_title="Virtual Pharmacy Clinic", page_icon="💊", layout="centered")

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
model = genai.GenerativeModel('gemini-3.1-pro-preview')# Bypassing strict medical safety filters for clinical simulation
safety = [
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"}
]

def generate_patient():
    prompt = f"""
    Act as a clinical pharmacy professor. Create a complex patient case for the category: {category}. 
    Align with the Pharm-D Pakistan 2010 syllabus. Output ONLY valid JSON with this exact structure:
    {{
      "name": "string",
      "age": 34,
      "bp": "string",
      "pulse": "string",
      "temp": "string",
      "allergies": "string",
      "symptoms": "string",
      "labs": "string",
      "diagnosisApproach": "string",
      "shelfDrugs": ["Drug 1", "Drug 2", "Drug 3", "Drug 4"],
      "correctDrug": "string",
      "correctDose": "string"
    }}
    """
    try:
        response = model.generate_content(prompt, safety_settings=safety)
        
        # Bulletproof JSON extraction
        text = response.text
        start = text.find('{')
        end = text.rfind('}') + 1
        clean_text = text[start:end]
        
        st.session_state.patient = json.loads(clean_text)
        st.session_state.selected_drug = "None selected"
    except Exception as e:
        st.error(f"System Error: {str(e)}")

if st.button("Call Next Patient", use_container_width=True):
    generate_patient()

if st.session_state.patient:
    p = st.session_state.patient
    
    st.markdown("### 👤 Patient Profile")
    with st.container():
        st.markdown(f"**Name:** {p.get('name', 'N/A')} | **Age:** {p.get('age', 'N/A')}")
        if str(p.get('allergies', 'none')).lower() != "none":
            st.error(f"⚠️ **ALLERGY ALERT:** {p.get('allergies', 'None')}")
        else:
            st.success("✅ **Allergies:** None reported")
            
        c1, c2, c3 = st.columns(3)
        c1.metric("BP", p.get('bp', '--'))
        c2.metric("Pulse", p.get('pulse', '--'))
        c3.metric("Temp", p.get('temp', '--'))
        
        st.write(f"**Symptoms:** {p.get('symptoms', '--')}")
        st.write(f"**Lab Tests:** {p.get('labs', '--')}")
        
        with st.expander("🩺 View Doctor's Diagnostic Reasoning", expanded=True):
            st.info(p.get('diagnosisApproach', '--'))

    st.markdown("---")
    st.markdown("### 🛒 Dispensing Counter")
    st.write("**Medication Shelf (Tap to Select):**")
    
    shelf = p.get('shelfDrugs', [])
    if shelf:
        cols = st.columns(len(shelf))
        for idx, drug in enumerate(shelf):
            with cols[idx]:
                if st.button(drug, key=f"drug_{idx}", use_container_width=True):
                    st.session_state.selected_drug = drug

    st.markdown(f"**Selected Drug on Counter:** `💊 {st.session_state.selected_drug}`")
    
    dosage_input = st.text_input("Prescribed Dosage (e.g. 500mg OD)")
    pharma_input = st.text_input("Pharmacognosy Alternative (Herbal Source & Active Constituent)")
    
    if st.button("Administer Treatment", use_container_width=True):
        if st.session_state.selected_drug == "None selected":
            st.warning("Please select a medication from the shelf first!")
        else:
            with st.spinner("Senior Pharmacist is reviewing your prescription..."):
                grading_prompt = f"""
                Grade this Pharm-D student's clinical treatment.
                Patient Case: {json.dumps(p)}
                Student's Choices -> Drug: {st.session_state.selected_drug}, Dosage: {dosage_input}, Pharmacognosy: {pharma_input}.
                Check for correctness, proper dosing, and fatal allergy contraindications.
                Output ONLY valid JSON: 
                {{
                  "isCorrect": boolean,
                  "fatalError": boolean,
                  "points": number,
                  "feedback": "string explanation"
                }}
                """
                try:
                    eval_res = model.generate_content(grading_prompt, safety_settings=safety)
                    
                    text = eval_res.text
                    start = text.find('{')
                    end = text.rfind('}') + 1
                    clean_eval = text[start:end]
                    grading = json.loads(clean_eval)
                    
                    st.session_state.score += grading.get('points', 0)
                    
                    if grading.get('fatalError', False):
                        st.error(f"🚨 **FATAL ERROR:** {grading.get('feedback', '')}")
                    elif grading.get('isCorrect', False):
                        st.session_state.treated += 1
                        st.success(f"✅ **SUCCESS:** {grading.get('feedback', '')}")
                    else:
                        st.warning(f"⚠️ **INCORRECT:** {grading.get('feedback', '')}")
                        
                except Exception as e:
                    st.error(f"Grading Error: {str(e)}")
else:
    st.info("👆 Click **'Call Next Patient'** above to open your first case file.")
