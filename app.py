"""
APP.PY — Student Chat Interface (Home Page)
==============================================
Multi-page Streamlit app. This is the student-facing page.
Teacher admin panel is at pages/1_Teacher_Admin.py

Launch with:
    streamlit run app.py
"""

import json
import os
import streamlit as st
from query_engine import get_query_engine, ask_doubt

STUDENTS_FILE = "students.json"

# ── Helper functions ──

def load_students():
    if os.path.exists(STUDENTS_FILE):
        with open(STUDENTS_FILE, "r") as f:
            return json.load(f)
    return {}


def save_students(students):
    with open(STUDENTS_FILE, "w") as f:
        json.dump(students, f, indent=2)


def check_login(code):
    students = load_students()
    code = code.strip().upper()
    if code in students:
        return code, students[code]
    return None, None


def use_question(code):
    students = load_students()
    if code not in students:
        return False
    student = students[code]
    if student["used"] >= student["quota"]:
        return False
    student["used"] += 1
    save_students(students)
    return True


def get_remaining(code):
    students = load_students()
    if code not in students:
        return 0
    student = students[code]
    return max(0, student["quota"] - student["used"])


# ── Page Config ──
st.set_page_config(
    page_title="KnowledgeHub Buddy — English Class Assistant",
    page_icon="logo.png",
    layout="centered",
)

st.markdown("""
<style>
    .main-header { text-align: center; padding: 1rem 0; }
    .main-header h1 { font-size: 2.2rem; margin-bottom: 0.2rem; }
    .main-header p { color: #666; font-size: 1.1rem; }
    .quota-box {
        padding: 0.8rem 1rem; border-radius: 8px;
        margin: 0.5rem 0; font-size: 0.95rem;
    }
    .quota-ok { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
    .quota-low { background: #fff3cd; color: #856404; border: 1px solid #ffeeba; }
    .quota-empty { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
</style>
""", unsafe_allow_html=True)

# ── Logo + Header ──
col_logo1, col_logo2, col_logo3 = st.columns([1, 1, 1])
with col_logo2:
    st.image("logo.png", width=150)

st.markdown("""
<div class="main-header">
    <h1>KnowledgeHub Buddy</h1>
    <p>Ask any question about our English lessons — I'll find the answer from your class materials!</p>
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
#  LOGIN GATE
# ══════════════════════════════════════════════════════════════

if not os.path.exists(STUDENTS_FILE):
    st.info(
        "⚙️ **Setup in progress.** The teacher hasn't added students yet.\n\n"
        "If you're the teacher, go to the **Teacher Admin** page in the sidebar."
    )
    st.stop()

if "student_code" not in st.session_state:
    st.session_state.student_code = None
    st.session_state.student_name = None

if st.session_state.student_code is None:
    st.markdown("### Enter your access code")
    st.caption("Your teacher will give you a 6-character code to log in.")

    col1, col2 = st.columns([3, 1])
    with col1:
        code_input = st.text_input(
            "Access code", placeholder="e.g. ABC123",
            max_chars=6, label_visibility="collapsed",
        )
    with col2:
        login_clicked = st.button("Log in", use_container_width=True, type="primary")

    if login_clicked and code_input:
        code, student = check_login(code_input)
        if student:
            st.session_state.student_code = code
            st.session_state.student_name = student["name"]
            st.session_state.messages = []
            st.rerun()
        else:
            st.error("❌ Invalid code. Please check with your teacher.")

    st.stop()


# ══════════════════════════════════════════════════════════════
#  LOGGED IN — Chat with quota
# ══════════════════════════════════════════════════════════════

student_code = st.session_state.student_code
student_name = st.session_state.student_name
remaining = get_remaining(student_code)

# ── Sidebar ──
with st.sidebar:
    st.image("logo.png", width=80)
    st.markdown(f"### 👋 Hi, {student_name}!")

    if remaining > 2:
        quota_class = "quota-ok"
    elif remaining > 0:
        quota_class = "quota-low"
    else:
        quota_class = "quota-empty"

    st.markdown(
        f'<div class="quota-box {quota_class}">'
        f'Questions remaining: <strong>{remaining}</strong></div>',
        unsafe_allow_html=True,
    )

    st.divider()
    st.markdown("### 💡 Try Asking")
    sample_questions = [
        "What is the difference between since and for?",
        "When do I use will vs going to?",
        "Explain the second conditional with examples",
        "What are stative verbs?",
    ]
    for q in sample_questions:
        if st.button(q, key=q, use_container_width=True, disabled=(remaining <= 0)):
            st.session_state["sample_question"] = q

    st.divider()
    if st.button("🚪 Log out", use_container_width=True):
        st.session_state.student_code = None
        st.session_state.student_name = None
        st.session_state.messages = []
        st.rerun()


# ── Load query engine ──
@st.cache_resource(show_spinner="Loading your class materials...")
def load_engine():
    return get_query_engine()

try:
    query_engine = load_engine()
except FileNotFoundError:
    st.error("📚 Knowledge base not built yet. The teacher needs to upload content first.")
    st.stop()
except ValueError as e:
    st.error(str(e))
    st.stop()

# ── Chat ──
if "messages" not in st.session_state or len(st.session_state.messages) == 0:
    st.session_state.messages = [{
        "role": "assistant",
        "content": (
            f"Hi {student_name}! 👋 I'm **KnowledgeHub Buddy**, your English class assistant.\n\n"
            f"You have **{remaining} questions** available. Ask me anything about our lessons!\n\n"
            "I'll also give you a quick quiz to make sure the doubt is really cleared! 📝"
        ),
    }]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if remaining <= 0:
    st.warning("⛔ **You've used all your questions!** Please contact your teacher to refresh your quota.")
    st.chat_input("No questions remaining...", disabled=True)
    st.stop()

if "sample_question" in st.session_state:
    prompt = st.session_state.pop("sample_question")
else:
    prompt = st.chat_input(f"Type your question here... ({remaining} remaining)")

if prompt:
    remaining = get_remaining(student_code)
    if remaining <= 0:
        st.error("⛔ No questions remaining.")
        st.stop()

    use_question(student_code)
    new_remaining = get_remaining(student_code)

    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        with st.spinner("Searching your class materials..."):
            try:
                answer = ask_doubt(query_engine, prompt)
                if new_remaining == 0:
                    answer += "\n\n---\n⛔ **That was your last question.** Contact your teacher to refresh your quota."
                elif new_remaining <= 2:
                    answer += f"\n\n---\n⚠️ **{new_remaining} question(s) remaining.** Use them wisely!"
                st.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})
            except Exception as e:
                error_msg = f"Oops! Something went wrong. Please try again. Error: {str(e)}"
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
