import streamlit as st
from io import BytesIO
import google.generativeai as genai

# Set page configuration
st.set_page_config(
    page_title="AI Question Generator",
    page_icon="📚",
    layout="wide"
)

# Simple CSS styling
st.markdown("""
<style>
    .main-header {
        font-size: 2rem;
        color: #1E3A8A;
        text-align: center;
        margin-bottom: 1rem;
    }
    .question-box {
        background-color: #EFF6FF;
        border-left: 5px solid #3B82F6;
        padding: 15px;
        margin-bottom: 15px;
        border-radius: 5px;
    }
    .stButton>button {
        background-color: #2563EB;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

def extract_text(file):
    try:
        if file.type == "text/plain":
            return file.getvalue().decode("utf-8")
        
        elif file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            from docx import Document
            doc = Document(BytesIO(file.read()))
            return "\n".join([para.text for para in doc.paragraphs])
        
        elif file.type == "application/vnd.openxmlformats-officedocument.presentationml.presentation":
            from pptx import Presentation
            prs = Presentation(BytesIO(file.read()))
            text = []
            for slide in prs.slides:
                for shape in slide.shapes:
                    if hasattr(shape, "text"):
                        text.append(shape.text)
            return "\n".join(text)
        
        else:
            st.error("Unsupported file type")
            return ""
    
    except Exception as e:
        st.error(f"Error processing file: {str(e)}")
        return ""

def generate_with_gemini(text, question_type, difficulty, api_key):
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-pro')
        
        prompt = f"""
        Generate 5 {difficulty.lower()} {question_type} questions based on this content.
        For each question include:
        - Clear question text
        - Correct answer
        {"- 3 incorrect options (for MCQ)" if question_type == "MCQ" else ""}
        - Brief explanation
        
        Content:
        {text[:10000]}  # Using first 10k chars to avoid token limits
        """
        
        response = model.generate_content(prompt)
        return response.text if response else "Failed to generate questions"
    
    except Exception as e:
        st.error(f"Gemini API error: {str(e)}")
        return None

def main():
    st.markdown('<h1 class="main-header">📚 AI Question Generator</h1>', unsafe_allow_html=True)
    
    with st.sidebar:
        st.markdown("### Settings")
        api_key = st.text_input("Gemini API Key", type="password", 
                              help="Get your key from Google AI Studio")
        
        st.markdown("### Upload Material")
        uploaded_file = st.file_uploader("Choose file", 
                                       type=["txt", "docx", "pptx"])
        
        if uploaded_file:
            question_type = st.selectbox("Question Type", 
                                       ["MCQ", "Fill-in-the-Blank", "Short Answer"])
            difficulty = st.selectbox("Difficulty", ["Easy", "Medium", "Hard"])
            
            if st.button("Generate Questions"):
                if not api_key:
                    st.error("Please enter your Gemini API key")
                else:
                    with st.spinner("Generating questions..."):
                        text = extract_text(uploaded_file)
                        if text:
                            questions = generate_with_gemini(text, question_type, difficulty, api_key)
                            if questions:
                                st.session_state.questions = questions

    if uploaded_file and 'questions' in st.session_state:
        st.markdown(f"## Generated {question_type} Questions")
        st.markdown(st.session_state.questions)
        
        st.download_button(
            label="Download Questions",
            data=BytesIO(st.session_state.questions.encode('utf-8')),
            file_name="generated_questions.txt",
            mime="text/plain"
        )

if __name__ == "__main__":
    main()
