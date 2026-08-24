import streamlit as st
import google.generativeai as genai
import json

# Page Configuration for Mobile Responsiveness
st.set_page_config(page_title="Virtual Pharmacy Clinic", page_icon="💊", layout="centered")

# Initialize Session States
if 'score' not in st.session_state:
    st.session_state.score = 500
if 'treated' not in st.session_state:
    st.session_state.treated = 0
if 'patient' not in st.session_state:
    st.session_state.patient = None
if 'selected_drug' not in st.session_state:
    st.session_state.selected_drug = "None selected"

# Sidebar Setup & Gamification
with st.sidebar:
    st.header("⚙️ Clinic Settings")
    api_key = st.text_input("Gemini API Key", type="password", placeholder="AIzaSy...")
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
model = genai.GenerativeModel('gemini-1.5-flash')

def generate_patient():
    prompt = f"""
    Act as a clinical pharmacy professor. Create a complex patient case for the category: {category}. 
    Align with the Pharm-D Pakistan 2010 syllabus. Output ONLY valid JSON with this exact structure:
    {{
      "name": "string",
      "age": number,
      "bp": "string",
      "pulse": "string",
      "temp": "string",
      "allergies": "string",
      "symptoms": "string",
      "labs": "string",
      "diagnosisApproach": "Detailed paragraph explaining how the doctor diagnosed this condition based on clinical findings.",
      "shelfDrugs": ["Drug 1", "Drug 2", "Drug 3", "Drug 4"],
      "correctDrug": "string",
      "correctDose": "string"
    }}
    """
    try:
        response = model.generate_content(prompt)
        clean_text = response.text.strip().replace('```json', '').replace('```', '')
        st.session_state.patient = json.loads(clean_text)
        st.session_state.selected_drug = "None selected"
    except Exception as e:
        st.error("Error connecting to Gemini. Please try clicking again.")

if st.button("Call Next Patient", use_container_width=True):
    generate_patient()

if st.session_state.patient:
    p = st.session_state.patient
    
    st.markdown("### 👤 Patient Profile")
    with st.container():
        st.markdown(f"**Name:** {p['name']} | **Age:** {p['age']}")
        if p['allergies'].lower() != "none":
            st.error(f"⚠️ **ALLERGY ALERT:** {p['allergies']}")
        else:
            st.success("✅ **Allergies:** None reported")
            
        c1, c2, c3 = st.columns(3)
        c1.metric("BP", p['bp'])
        c2.metric("Pulse", p['pulse'])
        c3.metric("Temp", p['temp'])
        
        st.write(f"**Symptoms:** {p['symptoms']}")
        st.write(f"**Lab Tests:** {p['labs']}")
        
        with st.expander("🩺 View Doctor's Diagnostic Reasoning", expanded=True):
            st.info(p['diagnosisApproach'])

    st.markdown("---")
    st.markdown("### 🛒 Dispensing Counter")
    st.write("**Medication Shelf (Tap to Select):**")
    
    cols = st.columns(len(p['shelfDrugs']))
    for idx, drug in enumerate(p['shelfDrugs']):
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
                    eval_res = model.generate_content(grading_prompt)
                    clean_eval = eval_res.text.strip().replace('```json', '').replace('```', '')
                    grading = json.loads(clean_eval)
                    
                    st.session_state.score += grading['points']
                    
                    if grading['fatalError']:
                        st.error(f"🚨 **FATAL ERROR:** {grading['feedback']}")
                    elif grading['isCorrect']:
                        st.session_state.treated += 1
                        st.success(f"✅ **SUCCESS:** {grading['feedback']}")
                    else:
                        st.warning(f"⚠️ **INCORRECT:** {grading['feedback']}")
                        
                    st.rerun()
                except Exception as e:
                    st.error("Grading evaluation error. Try submitting again.")
else:
    st.info("👆 Click **'Call Next Patient'** above to open your first case file.")