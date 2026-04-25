"""
TEACHER ADMIN — Management Dashboard
========================================
Password-protected admin panel for the teacher.
- Add / remove / refresh students
- Upload teaching content
- Rebuild the knowledge base
- View usage stats

Accessible at: your-app-url/Teacher_Admin
"""

import json
import os
import secrets
import string
import shutil
import subprocess
from pathlib import Path

import streamlit as st

STUDENTS_FILE = "students.json"
CONTENT_DIR = "teacher_content"
ADMIN_PASSWORD_ENV = "ADMIN_PASSWORD"
DEFAULT_QUOTA = 5

# ── Page Config ──
st.set_page_config(
    page_title="KnowledgeHub Buddy — Teacher Admin",
    page_icon="logo.png",
    layout="centered",
)

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


# ══════════════════════════════════════════════════════════════
#  ADMIN LOGIN
# ══════════════════════════════════════════════════════════════

def check_admin_password():
    """Verify teacher's admin password."""
    #admin_pw = os.environ.get(ADMIN_PASSWORD_ENV, "teacher123")
   
    try:
        admin_pw = st.secrets.get("ADMIN_PASSWORD", "teacher123")
    except Exception:
        admin_pw = os.environ.get(ADMIN_PASSWORD_ENV, "teacher123")
    

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
        st.caption("Default password is `teacher123`. Change it by setting the ADMIN_PASSWORD environment variable.")

        pw = st.text_input("Password", type="password", label_visibility="collapsed")
        if st.button("Log in", type="primary"):
            if pw == admin_pw:
                st.session_state.admin_authenticated = True
                st.rerun()
            else:
                st.error("❌ Wrong password.")
        st.stop()


check_admin_password()


# ══════════════════════════════════════════════════════════════
#  HELPER FUNCTIONS
# ══════════════════════════════════════════════════════════════

def load_students():
    if os.path.exists(STUDENTS_FILE):
        with open(STUDENTS_FILE, "r") as f:
            return json.load(f)
    return {}


def save_students(students):
    with open(STUDENTS_FILE, "w") as f:
        json.dump(students, f, indent=2)


def generate_code(length=6):
    letters = ''.join(secrets.choice(string.ascii_uppercase) for _ in range(3))
    numbers = ''.join(secrets.choice(string.digits) for _ in range(3))
    return letters + numbers


# ══════════════════════════════════════════════════════════════
#  ADMIN DASHBOARD
# ══════════════════════════════════════════════════════════════

col_l1, col_l2, col_l3 = st.columns([1, 1, 1])
with col_l2:
    st.image("logo.png", width=120)

st.markdown("""
<div class="admin-header">
    <h1>KnowledgeHub Buddy — Admin</h1>
</div>
""", unsafe_allow_html=True)

students = load_students()

# ── Stats overview ──
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

# ── Tabs ──
tab1, tab2, tab3, tab4 = st.tabs([
    "👥 Manage Students", "📤 Upload Content", "🔄 Rebuild Index", "🚪 Logout"
])

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  TAB 1: MANAGE STUDENTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

with tab1:
    # ── Add student(s) ──
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
                # Check duplicate
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

    # ── Student list ──
    st.markdown("#### Current students")

    if not students:
        st.info("No students registered yet. Add some above!")
    else:
        # Refresh all button
        col_r1, col_r2 = st.columns([3, 1])
        with col_r2:
            if st.button("🔄 Refresh all quotas", use_container_width=True):
                for code in students:
                    students[code]["used"] = 0
                save_students(students)
                st.success("✅ All quotas refreshed!")
                st.rerun()

        # Student table
        for code, info in sorted(students.items(), key=lambda x: x[1]["name"]):
            remaining = info["quota"] - info["used"]
            if remaining <= 0:
                status_icon = "🔴"
            elif remaining <= 2:
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
                    if st.button("🔄 Refresh quota", key=f"ref_{code}", use_container_width=True):
                        students[code]["used"] = 0
                        save_students(students)
                        st.success(f"Refreshed! {info['name']} has {info['quota']} questions again.")
                        st.rerun()

                with col3:
                    if st.button("🗑️ Remove", key=f"del_{code}", use_container_width=True):
                        del students[code]
                        save_students(students)
                        st.success(f"Removed {info['name']}.")
                        st.rerun()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  TAB 2: UPLOAD CONTENT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

with tab2:
    st.markdown("#### Upload teaching materials")
    st.caption("Upload PDFs, Word docs, or text files. These will be used to answer student questions.")

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
            st.success(f"✅ Uploaded {len(uploaded_files)} file(s) to teacher_content/")
            st.info("Now go to the **Rebuild Index** tab to update the knowledge base.")

    st.divider()

    # Show current files
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


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  TAB 3: REBUILD INDEX
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

with tab3:
    st.markdown("#### Rebuild knowledge base")
    st.caption(
        "After uploading new content, rebuild the index so Doubt Buddy "
        "can find answers from the new materials."
    )

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
                        # Clear the cached query engine so it reloads
                        st.cache_resource.clear()
                    else:
                        st.error("❌ Error rebuilding knowledge base:")
                        st.code(result.stderr, language="text")
                except subprocess.TimeoutExpired:
                    st.error("❌ Rebuild timed out. Try with fewer/smaller files.")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  TAB 4: LOGOUT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

with tab4:
    st.markdown("#### Admin session")
    if st.button("🚪 Log out of admin panel", type="primary"):
        st.session_state.admin_authenticated = False
        st.rerun()
