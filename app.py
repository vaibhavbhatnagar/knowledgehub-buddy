"""
APP.PY — KnowledgeHub Buddy (Single File App)
=================================================
Student chat:   your-url.streamlit.app
Teacher admin:  your-url.streamlit.app/?admin=true

Students CANNOT see the admin panel. It's hidden behind a secret URL.

Launch with:
    streamlit run app.py
"""

import json
import os
import secrets
import string
import subprocess
from pathlib import Path
import streamlit as st

STUDENTS_FILE = "students.json"
CONTENT_DIR = "teacher_content"
DEFAULT_QUOTA = 5


# ══════════════════════════════════════════════════════════════
#  SHARED HELPERS
# ══════════════════════════════════════════════════════════════

def load_students():
    if os.path.exists(STUDENTS_FILE):
        with open(STUDENTS_FILE, "r") as f:
            return json.load(f)
    return {}


def save_students(students):
    with open(STUDENTS_FILE, "w") as f:
        json.dump(students, f, indent=2)


def get_secret(key, default=""):
    """Read from Streamlit secrets first, then env vars."""
    try:
        return st.secrets[key]
    except Exception:
        return os.environ.get(key, default)


def generate_code():
    letters = ''.join(secrets.choice(string.ascii_uppercase) for _ in range(3))
    numbers = ''.join(secrets.choice(string.digits) for _ in range(3))
    return letters + numbers


# ── Page Config ──
st.set_page_config(
    page_title="KnowledgeHub Buddy",
    page_icon="logo.png",
    layout="centered",
)

# ── Check if admin mode via URL parameter ──
query_params = st.query_params
is_admin_mode = query_params.get("admin", "false").lower() == "true"


# ══════════════════════════════════════════════════════════════
#  ADMIN PANEL (only if ?admin=true)
# ══════════════════════════════════════════════════════════════

if is_admin_mode:

    st.markdown("""
    <style>
        .admin-header { text-align: center; padding: 1rem 0 0.5rem; }
        .admin-header h1 { font-size: 1.8rem; }
        .stat-card {
            padding: 1rem; border-radius: 10px; text-align: center;
            border: 1px solid #e0e0e0; margin: 0.3rem 0;
        }
        .stat-number { font-size: 1.8rem; font-weight: bold; }
        .stat-label { font-size: 0.85rem; color: #666; }
    </style>
    """, unsafe_allow_html=True)

    # ── Admin login ──
    admin_pw = get_secret("ADMIN_PASSWORD", "teacher123")

    if "admin_authenticated" not in st.session_state:
        st.session_state.admin_authenticated = False

    if not st.session_state.admin_authenticated:
        col_l1, col_l2, col_l3 = st.columns([1, 1, 1])
        with col_l2:
            st.image("logo.png", width=120)
        st.markdown("""
        <div class="admin-header">
            <h1>KnowledgeHub Buddy — Admin</h1>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("### Enter admin password")
        pw = st.text_input("Password", type="password", label_visibility="collapsed")
        if st.button("Log in", type="primary"):
            if pw == admin_pw:
                st.session_state.admin_authenticated = True
                st.rerun()
            else:
                st.error("❌ Wrong password.")
        st.stop()

    # ── Admin dashboard ──
    col_l1, col_l2, col_l3 = st.columns([1, 1, 1])
    with col_l2:
        st.image("logo.png", width=120)

    st.markdown("""
    <div class="admin-header">
        <h1>KnowledgeHub Buddy — Admin</h1>
    </div>
    """, unsafe_allow_html=True)

    students = load_students()

    # Stats
    total_students = len(students)
    total_questions_used = sum(s["used"] for s in students.values())
    exhausted = sum(1 for s in students.values() if s["used"] >= s["quota"])

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(
            f'<div class="stat-card"><div class="stat-number">{total_students}</div>'
            f'<div class="stat-label">Students</div></div>',
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            f'<div class="stat-card"><div class="stat-number">{total_questions_used}</div>'
            f'<div class="stat-label">Questions asked</div></div>',
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            f'<div class="stat-card"><div class="stat-number">{exhausted}</div>'
            f'<div class="stat-label">Quota exhausted</div></div>',
            unsafe_allow_html=True,
        )

    st.divider()

    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "👥 Manage Students", "📤 Upload Content", "🔄 Rebuild Index", "🚪 Logout"
    ])

    # ── TAB 1: MANAGE STUDENTS ──
    with tab1:
        st.markdown("#### Add students")

        add_mode = st.radio(
            "Add mode", ["Single student", "Multiple students"],
            horizontal=True, label_visibility="collapsed",
        )

        if add_mode == "Single student":
            col_a, col_b = st.columns([3, 1])
            with col_a:
                new_name = st.text_input("Student name", placeholder="e.g. Priya Sharma")
            with col_b:
                new_quota = st.number_input("Quota", min_value=1, max_value=100, value=DEFAULT_QUOTA)

            if st.button("Add student", type="primary"):
                if new_name.strip():
                    duplicate = any(
                        s["name"].lower() == new_name.strip().lower()
                        for s in students.values()
                    )
                    if duplicate:
                        st.error(f"❌ '{new_name.strip()}' already exists.")
                    else:
                        code = generate_code()
                        while code in students:
                            code = generate_code()
                        students[code] = {"name": new_name.strip(), "quota": new_quota, "used": 0}
                        save_students(students)
                        st.success(f"✅ Added **{new_name.strip()}** — Access code: **{code}**")
                        st.rerun()
                else:
                    st.error("Please enter a name.")

        else:
            st.caption("Enter one name per line")
            names_text = st.text_area("Student names", placeholder="Priya Sharma\nRahul Gupta\nAnanya Patel", height=120)
            bulk_quota = st.number_input("Quota for all", min_value=1, max_value=100, value=DEFAULT_QUOTA, key="bulk_q")

            if st.button("Add all students", type="primary"):
                names = [n.strip() for n in names_text.strip().split("\n") if n.strip()]
                if names:
                    added = []
                    for name in names:
                        duplicate = any(
                            s["name"].lower() == name.lower()
                            for s in students.values()
                        )
                        if not duplicate:
                            code = generate_code()
                            while code in students:
                                code = generate_code()
                            students[code] = {"name": name, "quota": bulk_quota, "used": 0}
                            added.append((name, code))

                    save_students(students)
                    if added:
                        st.success(f"✅ Added {len(added)} students!")
                        codes_display = "\n".join([f"**{name}** → `{code}`" for name, code in added])
                        st.markdown(codes_display)
                    st.rerun()
                else:
                    st.error("Please enter at least one name.")

        st.divider()

        st.markdown("#### Current students")

        if not students:
            st.info("No students registered yet. Add some above!")
        else:
            col_r1, col_r2 = st.columns([3, 1])
            with col_r2:
                if st.button("🔄 Refresh all quotas", use_container_width=True):
                    for code in students:
                        students[code]["used"] = 0
                    save_students(students)
                    st.success("✅ All quotas refreshed!")
                    st.rerun()

            for code, info in sorted(students.items(), key=lambda x: x[1]["name"]):
                remaining_q = info["quota"] - info["used"]
                if remaining_q <= 0:
                    status_icon = "🔴"
                elif remaining_q <= 2:
                    status_icon = "🟡"
                else:
                    status_icon = "🟢"

                with st.expander(f"{status_icon} **{info['name']}** — Code: `{code}` — {info['used']}/{info['quota']} used"):
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        new_q = st.number_input(
                            "New quota", min_value=1, max_value=100,
                            value=info["quota"], key=f"q_{code}",
                        )
                        if st.button("Update quota", key=f"uq_{code}"):
                            students[code]["quota"] = new_q
                            save_students(students)
                            st.success("Updated!")
                            st.rerun()

                    with col2:
                        if st.button("🔄 Refresh", key=f"ref_{code}", use_container_width=True):
                            students[code]["used"] = 0
                            save_students(students)
                            st.success(f"Refreshed!")
                            st.rerun()

                    with col3:
                        if st.button("🗑️ Remove", key=f"del_{code}", use_container_width=True):
                            del students[code]
                            save_students(students)
                            st.success(f"Removed {info['name']}.")
                            st.rerun()

    # ── TAB 2: UPLOAD CONTENT ──
    with tab2:
        st.markdown("#### Upload teaching materials")
        st.caption("Upload PDFs, Word docs, or text files.")

        os.makedirs(CONTENT_DIR, exist_ok=True)

        uploaded_files = st.file_uploader(
            "Choose files",
            type=["pdf", "docx", "txt", "md"],
            accept_multiple_files=True,
            label_visibility="collapsed",
        )

        if uploaded_files:
            if st.button("Upload files", type="primary"):
                for uploaded_file in uploaded_files:
                    file_path = os.path.join(CONTENT_DIR, uploaded_file.name)
                    with open(file_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                st.success(f"✅ Uploaded {len(uploaded_files)} file(s)!")
                st.info("Now go to the **Rebuild Index** tab to update the knowledge base.")

        st.divider()

        st.markdown("#### Current content files")
        content_files = list(Path(CONTENT_DIR).glob("*"))
        content_files = [f for f in content_files if f.is_file() and f.name != "PUT_FILES_HERE.txt"]

        if content_files:
            for f in sorted(content_files):
                size_kb = f.stat().st_size / 1024
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.text(f"📄 {f.name} ({size_kb:.1f} KB)")
                with col2:
                    if st.button("🗑️", key=f"delf_{f.name}"):
                        os.remove(f)
                        st.success(f"Deleted {f.name}")
                        st.rerun()
        else:
            st.info("No content files yet. Upload some above!")

    # ── TAB 3: REBUILD INDEX ──
    with tab3:
        st.markdown("#### Rebuild knowledge base")
        st.caption("After uploading new content, rebuild the index so KnowledgeHub Buddy can find answers.")

        content_files = list(Path(CONTENT_DIR).glob("*"))
        content_files = [f for f in content_files if f.is_file() and f.name != "PUT_FILES_HERE.txt"]

        if not content_files:
            st.warning("No content files found. Upload some in the **Upload Content** tab first.")
        else:
            st.info(f"📄 {len(content_files)} file(s) ready to index.")

            if st.button("🔨 Rebuild knowledge base", type="primary"):
                with st.spinner("Building knowledge base... This may take 1-2 minutes."):
                    try:
                        result = subprocess.run(
                            ["python", "ingest.py"],
                            capture_output=True, text=True, timeout=300,
                        )
                        if result.returncode == 0:
                            st.success("✅ Knowledge base rebuilt successfully!")
                            st.code(result.stdout, language="text")
                            st.cache_resource.clear()
                        else:
                            st.error("❌ Error rebuilding knowledge base:")
                            st.code(result.stderr, language="text")
                    except subprocess.TimeoutExpired:
                        st.error("❌ Rebuild timed out. Try with fewer/smaller files.")
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")

    # ── TAB 4: LOGOUT ──
    with tab4:
        st.markdown("#### Admin session")
        if st.button("🚪 Log out of admin panel", type="primary"):
            st.session_state.admin_authenticated = False
            st.rerun()

    st.stop()  # Don't show student UI below


# ══════════════════════════════════════════════════════════════
#  STUDENT INTERFACE (default — no ?admin parameter)
# ══════════════════════════════════════════════════════════════

from query_engine import get_query_engine, ask_doubt

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

# Logo + Header
col_logo1, col_logo2, col_logo3 = st.columns([1, 1, 1])
with col_logo2:
    st.image("logo.png", width=150)

st.markdown("""
<div class="main-header">
    <h1>KnowledgeHub Buddy</h1>
    <p>Ask any question about our English lessons — I'll find the answer from your class materials!</p>
</div>
""", unsafe_allow_html=True)


# ── Login gate ──

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


if not os.path.exists(STUDENTS_FILE) or len(load_students()) == 0:
    st.info("⚙️ **Setup in progress.** The teacher hasn't added students yet.")
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


# ── Logged in — Chat ──

student_code = st.session_state.student_code
student_name = st.session_state.student_name
remaining = get_remaining(student_code)

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
