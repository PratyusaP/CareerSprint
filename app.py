import streamlit as st
import io
import time
from rag.generator import ask_career_agent
from rag.pdf_processor import process_uploaded_resume
from rag.retriever import retrieve
import google.generativeai as genai

try:
    
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
except (FileNotFoundError, KeyError):
    #  Fall back to your local config file
    from config.settings import GEMINI_API_KEY

st.set_page_config(page_title="CareerSprint", page_icon="🚀", layout="centered")
genai.configure(api_key=GEMINI_API_KEY)


st.markdown(
    """
    <script>
    const el = window.parent.document.querySelector(".stChatFloatingInputContainer");
    if (el) {
        el.scrollIntoView({ behavior: "smooth", block: "end" });
    }
    </script>
    """,
    unsafe_allow_html=True
)

def stream_text(text_to_print):
    for word in text_to_print.split(" "):
        yield word + " "
        time.sleep(0.02)

# 1. INITIALIZE MEMORY 


welcome_text = """👋 **Welcome to your personal Career Assistant!**

I am your AI Engineering Mentor, here to help you land your next big role. Here is what we can do together:
* 📊 **Analyze your resume** to see if it matches your target job.
* 🎤 **Conduct Mock Interviews** with dynamic, adaptive questions.
* 💡 **Answer general career questions** or help you prep for specific companies.

To get started, attach your resume using the + icon below, or just say hi!"""

if "messages" not in st.session_state: 
    st.session_state.messages = [{"role": "assistant", "content": welcome_text}]

if "workflow" not in st.session_state: st.session_state.workflow = "none"
if "current_questions" not in st.session_state: st.session_state.current_questions = ""
if "processed_file_sig" not in st.session_state: st.session_state.processed_file_sig = None
if "analyze_clicked" not in st.session_state: st.session_state.analyze_clicked = False
if "interview_active" not in st.session_state: st.session_state.interview_active = False
if "interview_messages" not in st.session_state: st.session_state.interview_messages = []
if "target_role" not in st.session_state: st.session_state.target_role = ""
if "past_sessions" not in st.session_state: st.session_state.past_sessions = []
if "session_counter" not in st.session_state: st.session_state.session_counter = 1
if "interviewer_persona" not in st.session_state: st.session_state.interviewer_persona = "Encouraging Mentor"

if "messages" not in st.session_state: 
    welcome_text = """👋 **Welcome to your personal Career Assistant!**

I am your AI Engineering Mentor, here to help you land your next big role. Here is what we can do together:
* 📊 **Analyze your resume** to see if it matches your target job.
* 🎤 **Conduct Mock Interviews** with dynamic, adaptive questions.
* 💡 **Answer general career questions** or help you prep for specific companies.

To get started, attach your resume using the 📎 icon below, or just say hi!"""
    st.session_state.messages = [{"role": "assistant", "content": welcome_text}]

if "workflow" not in st.session_state: st.session_state.workflow = "none"
if "current_questions" not in st.session_state: st.session_state.current_questions = ""
if "processed_file_sig" not in st.session_state: st.session_state.processed_file_sig = None
if "analyze_clicked" not in st.session_state: st.session_state.analyze_clicked = False
if "interview_active" not in st.session_state: st.session_state.interview_active = False
if "interview_messages" not in st.session_state: st.session_state.interview_messages = []
if "target_role" not in st.session_state: st.session_state.target_role = ""
if "past_sessions" not in st.session_state: st.session_state.past_sessions = []
if "session_counter" not in st.session_state: st.session_state.session_counter = 1
if "interviewer_persona" not in st.session_state: st.session_state.interviewer_persona = "Encouraging Mentor"

# Cache the model so we don't rebuild the API connection every time
@st.cache_resource
def get_audio_model():
    return genai.GenerativeModel("gemini-2.5-flash")

def process_audio(prompt_audio):
    with st.spinner("🎙️ Transcribing over network..."):
        try:
            audio_data = prompt_audio.read()
            model = get_audio_model()
            response = model.generate_content([
                {"mime_type": "audio/wav", "data": audio_data},
                "Convert this audio to text. Output only the transcription."
            ])
            return response.text.strip()
        except Exception as e:
            st.error(f"Voice Transcription Failed: {e}")
            return None

st.title("🚀 CareerSprint")
st.markdown("**Your Agentic RAG-Driven Career Assistant**")

# 📄 THE SIDEBAR

with st.sidebar:
    st.header("⚙️ Session Controls")

    if st.button("🔄 Start New Conversation", use_container_width=True, type="primary"):
        if len(st.session_state.messages) > 1: 
            first_user_msg = next((m["content"] for m in st.session_state.messages if m["role"] == "user"), "General Chat")
            title = (first_user_msg[:25] + '...') if len(first_user_msg) > 25 else first_user_msg
            st.session_state.past_sessions.append({
                "title": f"Session {st.session_state.session_counter}: {title}",
                "messages": list(st.session_state.messages)
            })
            st.session_state.session_counter += 1

        st.session_state.messages = [{"role": "assistant", "content": welcome_text}]
        st.session_state.workflow = "none"
        st.session_state.processed_file_sig = None 
        st.session_state.analyze_clicked = False
        st.session_state.interview_active = False
        st.session_state.interview_messages = []
        st.session_state.target_role = ""
        st.rerun()

    st.divider()

    st.header("🕰️ Past Conversations")
    if not st.session_state.past_sessions:
        st.caption("No past conversations yet.")
    else:
        for session in reversed(st.session_state.past_sessions):
            with st.expander(session["title"]):
                for msg in session["messages"]:
                    role_icon = "👤" if msg["role"] == "user" else "🎓"
                    st.markdown(f"**{role_icon}:** {msg['content']}")


# 🟢 MODE A: THE LIVE INTERVIEW ROOM

if st.session_state.interview_active:

    head_col1, head_col2 = st.columns([3, 1])
    with head_col1:
        st.markdown("### 🔴 LIVE: Mock Interview Room")
        clean_vibe = st.session_state.interviewer_persona.replace("🤝", "").replace("🕴️", "").replace("🚀", "").strip()
        st.caption(f"**Target Role:** {st.session_state.target_role} | **Vibe:** {clean_vibe}")
    with head_col2:
        st.markdown("<p style='text-align: right; color: red; font-weight: bold;'>🎙️ Recording...</p>", unsafe_allow_html=True)

    chat_container = st.container(height=400, border=True)
    with chat_container:
        for msg in st.session_state.interview_messages:
            avatar_icon = "👤" if msg["role"] == "user" else "💼"
            with st.chat_message(msg["role"], avatar=avatar_icon):
                st.markdown(msg["content"])

    st.write("")
    btn_col1, btn_col2 = st.columns(2)
    skip_pressed = btn_col1.button("⏭️ Skip Question", use_container_width=True)
    end_pressed = btn_col2.button("🛑 End Interview & Get Score", use_container_width=True, type="primary")

    prompt = st.chat_input("Answer the Interviewer...", accept_audio=True)
    user_query = ""

    if skip_pressed: user_query = "SKIP_QUESTION"
    elif end_pressed: user_query = "END_INTERVIEW"
    elif prompt:
        if getattr(prompt, "audio", None): user_query = process_audio(prompt.audio)
        else: user_query = prompt.text

    if user_query:
        if st.session_state.processed_file_sig:
            resume_data = retrieve("skills experience projects education", k=10)
            resume_text = "\n\n".join(resume_data) if resume_data else "No resume found."
        else:
            resume_text = "No resume uploaded yet in this session."

        if user_query == "END_INTERVIEW":
            with st.spinner("📊 Analyzing your performance..."):
                st.session_state.interview_active = False
                st.session_state.messages.append({"role": "assistant", "content": f"### 🛑 Mock Interview Concluded\n**Role:** {st.session_state.target_role}\n*Here is the transcript from your session:*"})

                history_str = ""
                for m in st.session_state.interview_messages:
                    st.session_state.messages.append(m)
                    history_str += f"{m['role'].upper()}: {m['content']}\n"

                secret_query = f"""The mock interview for '{st.session_state.target_role}' has ended. Resume: {resume_text}\nTranscript: {history_str}
                Act as a professional engineering recruiter. Give an overall score out of 10. Highlight strengths and brutally honest areas for improvement. Ask if they want 'Ideal Answers'."""
                scorecard = ask_career_agent(secret_query)
                st.session_state.messages.append({"role": "assistant", "content": scorecard})
                st.session_state.workflow = "none"
                st.rerun()

        #Strict skip instructions preventing question repetition
        elif user_query == "SKIP_QUESTION":
            with st.spinner("⏩ Getting next question..."):
                st.session_state.interview_messages.append({"role": "user", "content": "*User skipped the question.*"})
                secret_query = f"""The user skipped this exact question: '{st.session_state.current_questions}'. 
                Target role: {st.session_state.target_role}. Resume: {resume_text}. Persona: {st.session_state.interviewer_persona}. 
                Generate a completely DIFFERENT, single interview question based on this persona. Do NOT ask anything related to the skipped question. Output ONLY the new question."""
                new_q = ask_career_agent(secret_query)
                st.session_state.current_questions = new_q
                st.session_state.interview_messages.append({"role": "assistant", "content": new_q})
                st.rerun()

        else:
            st.session_state.interview_messages.append({"role": "user", "content": user_query})
            with st.spinner("🤔 Interviewer is evaluating..."):
                history_str = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in st.session_state.interview_messages])
                secret_query = f"""We are in an active mock interview for '{st.session_state.target_role}'. Your Persona: {st.session_state.interviewer_persona}. Resume:\n{resume_text}\nTranscript:\n{history_str}\nThe user just answered. Based on your Persona, acknowledge their answer briefly, and then ask the NEXT interview question. Generate only one question."""
                next_q = ask_career_agent(secret_query)
                st.session_state.current_questions = next_q
                st.session_state.interview_messages.append({"role": "assistant", "content": next_q})
                st.rerun()


# MODE B: THE NORMAL DASHBOARD UI
else:
    for message in st.session_state.messages:
        avatar_icon = "👤" if message["role"] == "user" else "🎓"
        with st.chat_message(message["role"], avatar=avatar_icon):
            st.markdown(message["content"])

    st.write("")
    col1, col2 = st.columns(2)

    with col1:
        if st.button("📊 Analyze My Resume", use_container_width=True):
            st.session_state.analyze_clicked = True
            if st.session_state.target_role != "":
                st.session_state.workflow = "execute_analysis"
            else:
                st.session_state.workflow = "analyze_role"
                st.session_state.messages.append({"role": "assistant", "content": "📝 **Great! What specific role or job title are you applying for?**"})
            st.rerun()

    with col2:
        if st.button("🎤 Start Mock Interview", use_container_width=True):
            if st.session_state.target_role != "":
                st.session_state.workflow = "wait_for_interview_vibe"
                st.session_state.messages.append({"role": "assistant", "content": f"🎯 We are prepping for the **{st.session_state.target_role}** role. How would you like me to act during this interview? Select a vibe below:"})
            else:
                st.session_state.workflow = "wait_for_interview_role"
                st.session_state.messages.append({"role": "assistant", "content": "🎯 **What specific role or job title are we interviewing for today?**"})
            st.rerun()

    st.write("")
    chip_clicked = None

    if st.session_state.messages and st.session_state.messages[-1]["role"] == "assistant":
        if st.session_state.workflow == "wait_for_interview_vibe":
            suggestions = ["Encouraging Mentor 🤝", "Strict FAANG Manager 🕴️", "Curious Startup CTO 🚀"]
            chip_clicked = st.pills("Select your Interview Vibe:", suggestions, label_visibility="collapsed")
            
        elif st.session_state.workflow == "none":
            last_message = st.session_state.messages[-1]["content"].lower()
            if "role" not in last_message and "welcome" not in last_message:
                if "score" in last_message or "ideal answers" in last_message:
                    suggestions = ["Yes, show me the ideal answers 📝", "Ask me a harder technical question 🧠", "Give me a general interview tip ✨"]
                elif "resume" in last_message:
                    suggestions = ["What keywords am I missing? 🔍", "How can I improve my project descriptions? ✍️", "Review my education section 🎓"]
                else:
                    suggestions = ["What are common mistakes for this role? 🚫", "Give me a behavioral question 🤝", "Review my skills section 🛠️"]

                chip_clicked = st.pills("💡 Explore more:", suggestions, label_visibility="collapsed")

    prompt = st.chat_input("Message your Mentor...", accept_file=True, file_type=["pdf"], accept_audio=True)
    user_query = ""
    trigger_backend = False

    if st.session_state.workflow == "execute_analysis":
        user_query = st.session_state.target_role
        trigger_backend = True
    elif prompt or chip_clicked:
        trigger_backend = True
        if chip_clicked:
            user_query = chip_clicked
        else:
            if prompt.files:
                uploaded_file = prompt.files[0]
                file_sig = f"{uploaded_file.name}_{uploaded_file.size}"
                if st.session_state.processed_file_sig != file_sig:
                    with st.spinner("Processing attached document..."):
                        try:
                            process_uploaded_resume(uploaded_file)
                            st.cache_resource.clear() 
                            st.session_state.processed_file_sig = file_sig
                            st.session_state.messages.append({"role": "user", "content": f"📎 *Attached Document: {uploaded_file.name}*"})
                            st.session_state.messages.append({"role": "assistant", "content": f"✅ I have successfully read **{uploaded_file.name}**. How can I help you with it?"})
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error processing PDF: {e}")

            if getattr(prompt, "audio", None):
                user_query = process_audio(prompt.audio)
            elif prompt.text:
                user_query = prompt.text

    if trigger_backend and user_query:
        if st.session_state.workflow != "execute_analysis":
            with st.chat_message("user", avatar="👤"):
                st.markdown(user_query)
            st.session_state.messages.append({"role": "user", "content": user_query})

        short_query = user_query.lower()
        if len(short_query) < 40 and any(keyword in short_query for keyword in ["backend", "frontend", "developer", "engineer", "data", "manager"]):
            st.session_state.target_role = user_query.strip()

        with st.spinner("🤖 Mentor is thinking..."):
            if st.session_state.processed_file_sig:
                resume_data = retrieve("skills experience projects education", k=10)
                resume_text = "\n\n".join(resume_data) if resume_data else "No resume found."
            else:
                resume_text = "No resume uploaded yet in this session."
                
            recent_history = "\n".join([f"{msg['role']}: {msg['content']}" for msg in st.session_state.messages[-5:-1]])

            if st.session_state.workflow in ["analyze_role", "execute_analysis"]:
                if "told you" in user_query.lower() or "already" in user_query.lower():
                    st.session_state.target_role = st.session_state.target_role if st.session_state.target_role else "Software Engineer"
                elif st.session_state.workflow == "analyze_role":
                    st.session_state.target_role = user_query

                secret_query = f"""
                Recent Chat: {recent_history}
                User Input: '{user_query}'
                Target Role: '{st.session_state.target_role}'
                Resume Chunks: {resume_text}

                You are an AI Career Mentor analyzing the user's resume for their Target Role.
                CRITICAL INSTRUCTIONS:
                1. If Resume Chunks says 'No resume uploaded yet in this session.', politely ask them to upload a standard readable PDF.
                2. Do NOT act like a generic chatbot. Go straight into the analysis.
                3. Highlight 3 strong points from their resume, 2 areas to add detail, and 1 actionable tip.
                """
                answer = ask_career_agent(secret_query)
                st.session_state.workflow = "none"

            elif st.session_state.workflow == "wait_for_interview_role":
                if "told you" in user_query.lower() or "already" in user_query.lower():
                    user_query = st.session_state.target_role if st.session_state.target_role else "Software Engineer"
                
                st.session_state.target_role = user_query 
                st.session_state.workflow = "wait_for_interview_vibe"
                answer = f"✅ Got it! We are prepping for the **{user_query}** role.\n\nNow, how would you like me to act during this interview? Select a vibe below:"

            elif st.session_state.workflow == "wait_for_interview_vibe":
                st.session_state.interviewer_persona = user_query
                st.session_state.interview_active = True
                st.session_state.workflow = "interview_loop"

                secret_query = f"Start a mock interview for the role of '{st.session_state.target_role}'. Persona: {st.session_state.interviewer_persona}. User Resume:\n{resume_text}\nGenerate the FIRST technical or behavioral question based on their resume and your persona. Output ONLY the question."
                first_question = ask_career_agent(secret_query)

                st.session_state.current_questions = first_question
                st.session_state.interview_messages = [{"role": "assistant", "content": first_question}]
                st.rerun()

            else:
                # ✨ POLISH FIX 2 & 3: Strict Routing and Off-Topic Guardrails
                full_query = f"""
                Target Role: {st.session_state.target_role if st.session_state.target_role else "Unknown"}
                Recent Chat History: {recent_history}
                User Question: {user_query}
                Resume Context: {resume_text}

                Act as an Engineering Mentor.
                CRITICAL RULES:
                1. MOCK INTERVIEW REDIRECT: If the user explicitly asks you to "ask them an interview question", "test them", or "conduct an interview", DO NOT ask the question here in the chat. Politely tell them to click the '🎤 Start Mock Interview' button above to enter the dedicated interview room.
                2. OFF-TOPIC GUARDRAIL: If the user asks about completely unrelated topics (like movies, celebrity gossip, etc.), politely refuse, state that you are a dedicated Career Assistant, and redirect them to resume or interview prep. If it is slightly out of syllabus but related (like general tech or engineering concepts), answer briefly but gracefully guide them back to career prep.
                3. Always tailor your advice to their Target Role if it is known.
                4. If the user complains that they already told you their role, apologize, acknowledge their Target Role, and answer their core question.
                5. Keep answers concise and helpful based on their resume context.
                """
                answer = ask_career_agent(full_query)

        if st.session_state.workflow != "interview_loop":
            with st.chat_message("assistant", avatar="🎓"):
                st.write_stream(stream_text(answer))
            st.session_state.messages.append({"role": "assistant", "content": answer})
        st.rerun()