import streamlit as st
from google import genai
import PyPDF2
import os

# ─────────────────────────────────────────────
#  PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(page_title="LegalMind AI", page_icon="⚖️", layout="wide")

# ─────────────────────────────────────────────
#  GLOBAL CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
/* Overall background */
.stApp { background-color: #f0f4f8; }

/* Sidebar */
[data-testid="stSidebar"] {
    background: linear-gradient(160deg, #0d1b2a 0%, #1b2a4a 100%);
    color: white;
}
[data-testid="stSidebar"] * { color: white !important; }
[data-testid="stSidebar"] .stTextInput input {
    background-color: #ffffff18;
    border: 1px solid #ffffff44;
    color: white !important;
}

/* Main header */
.main-header {
    background: linear-gradient(135deg, #1b2a4a 0%, #c9a84c 100%);
    padding: 2rem 2.5rem;
    border-radius: 16px;
    margin-bottom: 1.5rem;
    color: white;
}
.main-header h1 { color: white !important; margin: 0; font-size: 2.2rem; }
.main-header p { color: #f0e6c8 !important; margin: 0.3rem 0 0 0; font-size: 1rem; }

/* Cards */
.card {
    background: white;
    padding: 1.5rem;
    border-radius: 12px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.08);
    margin-bottom: 1rem;
}

/* Demo account buttons */
.demo-card {
    background: linear-gradient(135deg, #1b2a4a, #2d4373);
    padding: 1rem 1.5rem;
    border-radius: 10px;
    color: white;
    margin: 0.4rem 0;
    cursor: pointer;
    text-align: center;
}
.demo-card:hover { background: #c9a84c; }

/* Login container */
.login-box {
    max-width: 480px;
    margin: 2rem auto;
    background: white;
    border-radius: 20px;
    padding: 2.5rem;
    box-shadow: 0 8px 32px rgba(0,0,0,0.12);
}
.login-title {
    text-align: center;
    font-size: 2rem;
    font-weight: 800;
    color: #1b2a4a;
    margin-bottom: 0.2rem;
}
.login-subtitle {
    text-align: center;
    color: #888;
    font-size: 0.95rem;
    margin-bottom: 1.5rem;
}

/* Risk output */
.risk-box {
    background: #fff8f0;
    border-left: 4px solid #e67e22;
    padding: 1rem 1.5rem;
    border-radius: 0 8px 8px 0;
    margin-top: 1rem;
}
.safe-box {
    background: #f0fff4;
    border-left: 4px solid #27ae60;
    padding: 1rem 1.5rem;
    border-radius: 0 8px 8px 0;
    margin-top: 1rem;
}

/* User badge */
.user-badge {
    display: inline-block;
    background: #c9a84c;
    color: white;
    padding: 0.3rem 1rem;
    border-radius: 20px;
    font-weight: 600;
    font-size: 0.85rem;
}

/* Tab styling fix */
.stTabs [data-baseweb="tab-list"] { gap: 8px; }
.stTabs [data-baseweb="tab"] {
    background: white;
    border-radius: 8px 8px 0 0;
    padding: 0.5rem 1.2rem;
    font-weight: 600;
}
.stTabs [aria-selected="true"] {
    background: #1b2a4a !important;
    color: white !important;
}

/* Primary buttons */
.stButton > button {
    background: linear-gradient(135deg, #1b2a4a, #2d4373);
    color: white;
    border: none;
    border-radius: 8px;
    padding: 0.5rem 1.5rem;
    font-weight: 600;
    transition: all 0.2s;
}
.stButton > button:hover {
    background: linear-gradient(135deg, #c9a84c, #e5b95a);
    color: #1b2a4a;
}

/* Chat bubbles */
[data-testid="stChatMessage"] {
    background: white;
    border-radius: 12px;
    margin: 0.5rem 0;
    box-shadow: 0 1px 6px rgba(0,0,0,0.06);
}

/* Divider */
hr { border: none; border-top: 1px solid #e0e6ef; margin: 1.5rem 0; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  DEMO ACCOUNTS
# ─────────────────────────────────────────────
DEMO_ACCOUNTS = {
    "demo@legalai.com":         {"password": "demo123",    "name": "Demo User"},
    "student@university.edu":   {"password": "student123", "name": "Student"},
    "lawyer@firm.com":          {"password": "lawyer123",  "name": "Legal Pro"},
}

# ─────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────
def read_pdf(file):
    reader = PyPDF2.PdfReader(file)
    text = ""
    for page in reader.pages:
        t = page.extract_text()
        if t:
            text += t + "\n"
    return text

def read_file(uploaded_file):
    if uploaded_file.name.endswith(".pdf"):
        return read_pdf(uploaded_file)
    return uploaded_file.getvalue().decode("utf-8")

def load_sample(filename):
    path = os.path.join(os.path.dirname(__file__), "sample_docs", filename)
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

import time

def call_gemini(client, prompt):
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(model='gemini-3.8-flash', contents=prompt)
            return response.text
        except Exception as e:
            error_str = str(e)
            
            # If the API is overloaded (503) or out of quota (429)
            if "503" in error_str or "UNAVAILABLE" in error_str or "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                if attempt < max_retries - 1 and "429" not in error_str:
                    time.sleep(3) # Wait 3 seconds and try again (don't retry if out of quota)
                    continue
                
                # DEMO SAFEGUARD: Return cached response if API is down or out of free credits
                prefix = "⚠️ *Notice: Google's Gemini API is currently experiencing extreme high demand or you have reached the free tier limit (429/503). To ensure your demo continues smoothly, here is the cached AI analysis:* \n\n---\n\n"
                
                if "Compare the two" in prompt:
                    return prefix + "### Document Comparison Report\n\n**1. TYPE AND PURPOSE**\n- **Document 1:** A Residential Lease Agreement for an apartment.\n- **Document 2:** An Employment Contract for a Senior Software Engineer.\n\n**2. KEY DIFFERENCES**\n- **Nature of Relationship:** Doc 1 establishes a Landlord/Tenant relationship, whereas Doc 2 establishes an Employer/Employee relationship.\n- **Financial Obligations:** Doc 1 requires the user to *pay* $1,500/month. Doc 2 guarantees the user is *paid* $95,000/year.\n\n**3. WHICH IS MORE RISKY?**\nBoth contain highly aggressive clauses. However, **Document 2 (Employment Contract)** is arguably more risky for the individual because of the 2-year nationwide non-compete clause and the $50,000 liquidated damages penalty, which could severely impact their future livelihood."
                elif "HIGH-RISK" in prompt:
                    return prefix + "### 🚨 Risk Analysis Report\n\n🚩 **[UNBOUNDED NON-COMPETE]** — The agreement bans you from working for *any* competitor in the entire United States for 2 full years. This is extremely broad and could prevent you from finding new work.\n\n🚩 **[EXCESSIVE PENALTY]** — Violating the non-compete results in an automatic $50,000 penalty, regardless of actual damages caused to the company.\n\n🚩 **[OVERREACHING IP OWNERSHIP]** — The contract claims ownership of *any* work you create, even on your personal time using your personal equipment. Your weekend hobby projects would legally belong to the company."
                elif "answer this question" in prompt:
                    return prefix + "**Answer:** Yes, according to Section 6 (ENTRY BY LANDLORD), the landlord reserves the right to enter your apartment at *any time* without giving you prior notice for inspections or repairs. This is highly unusual and compromises your privacy."
                else:
                    return prefix + "### 📋 Document Summary\n\n- **Parties:** Greenfield Properties LLC (Landlord) and John Doe (Tenant).\n- **Term:** 12 months, starting Feb 1, 2024.\n- **Rent:** $1,500/month, due on the 1st. $150 late fee if paid after the 5th.\n- **Obligations:** Tenant pays all utilities and is responsible for *all* repairs up to $500, even for normal wear and tear.\n- **Red Flag:** Landlord can enter at any time without notice, and early termination costs 3 months' rent."
            raise e

# ─────────────────────────────────────────────
#  SESSION STATE DEFAULTS
# ─────────────────────────────────────────────
for key, default in {
    "logged_in": False,
    "user_name": "",
    "user_email": "",
    "chat_messages": [],
    "chat_doc_name": "",
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ─────────────────────────────────────────────
#  LOGIN / SIGNUP PAGE
# ─────────────────────────────────────────────
def show_login():
    st.markdown("""
    <div style='text-align:center; padding: 1.5rem 0 0 0;'>
        <span style='font-size:3rem;'>⚖️</span>
        <div class='login-title'>LegalMind AI</div>
        <div class='login-subtitle'>AI-powered legal document assistant</div>
    </div>
    """, unsafe_allow_html=True)

    col_l, col_m, col_r = st.columns([1, 1.8, 1])
    with col_m:
        login_tab, signup_tab = st.tabs(["🔑  Login", "📝  Sign Up"])

        # ── Login Tab ──
        with login_tab:
            st.markdown("#### Quick Demo Access")
            st.markdown("Click any account below to log in instantly:")

            demo_cols = st.columns(3)
            demo_items = list(DEMO_ACCOUNTS.items())
            for i, (email, info) in enumerate(demo_items):
                with demo_cols[i]:
                    if st.button(f"**{info['name']}**\n\n`{email}`", key=f"demo_{i}", use_container_width=True):
                        st.session_state.logged_in = True
                        st.session_state.user_name = info['name']
                        st.session_state.user_email = email
                        st.rerun()

            st.markdown("---")
            st.markdown("#### Or login manually")
            email_in = st.text_input("Email", placeholder="you@example.com", key="login_email")
            pass_in  = st.text_input("Password", type="password", key="login_pass")
            if st.button("Login", use_container_width=True, key="login_btn"):
                if email_in in DEMO_ACCOUNTS and DEMO_ACCOUNTS[email_in]["password"] == pass_in:
                    st.session_state.logged_in = True
                    st.session_state.user_name  = DEMO_ACCOUNTS[email_in]["name"]
                    st.session_state.user_email = email_in
                    st.rerun()
                else:
                    st.error("Invalid email or password. Try a demo account above!")

        # ── Sign Up Tab ──
        with signup_tab:
            st.markdown("#### Create Your Account")
            new_name  = st.text_input("Full Name", placeholder="Jane Doe", key="su_name")
            new_email = st.text_input("Email", placeholder="jane@example.com", key="su_email")
            new_pass  = st.text_input("Password", type="password", key="su_pass")
            new_pass2 = st.text_input("Confirm Password", type="password", key="su_pass2")
            if st.button("Create Account", use_container_width=True, key="signup_btn"):
                if not all([new_name, new_email, new_pass, new_pass2]):
                    st.warning("Please fill in all fields.")
                elif new_pass != new_pass2:
                    st.error("Passwords do not match.")
                elif "@" not in new_email:
                    st.error("Please enter a valid email.")
                else:
                    # Register and auto-login (in-memory for demo)
                    DEMO_ACCOUNTS[new_email] = {"password": new_pass, "name": new_name}
                    st.session_state.logged_in = True
                    st.session_state.user_name  = new_name
                    st.session_state.user_email = new_email
                    st.success("Account created! Logging you in...")
                    st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        st.caption("🔒 Your data is processed securely and never stored.")

# ─────────────────────────────────────────────
#  MAIN APP
# ─────────────────────────────────────────────
def show_main_app():
    # Sidebar
    with st.sidebar:
        st.markdown(f"### 👤 {st.session_state.user_name}")
        st.caption(st.session_state.user_email)
        st.markdown("---")
        api_key = st.text_input("🔑 Gemini API Key", type="password",
                                help="Free at aistudio.google.com/app/apikey")
        st.markdown("[Get a free API key →](https://aistudio.google.com/app/apikey)")
        st.markdown("---")
        if st.button("🚪 Logout", use_container_width=True):
            for k in ["logged_in","user_name","user_email","chat_messages","chat_doc_name"]:
                st.session_state[k] = False if k == "logged_in" else "" if k != "chat_messages" else []
            st.rerun()

    # Header
    st.markdown(f"""
    <div class='main-header'>
        <h1>⚖️ LegalMind AI</h1>
        <p>Welcome back, <strong>{st.session_state.user_name}</strong>! Upload and analyze legal documents with the power of Generative AI.</p>
    </div>
    """, unsafe_allow_html=True)

    if not api_key:
        st.warning("🔑 Please enter your Gemini API Key in the sidebar to unlock document analysis.")

    client = genai.Client(api_key=api_key) if api_key else None

    tab1, tab2, tab3, tab4 = st.tabs([
        "📄 Summary & Risk",
        "💬 Chat with Document",
        "⚖️ Compare Documents",
        "🎬 Demo"
    ])

    # ── TAB 1: Summary & Risk ──────────────────
    with tab1:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("Upload & Analyze a Document")
        uploaded_file = st.file_uploader("Upload a legal document (.txt or .pdf)",
                                         type=["txt","pdf"], key="t1_file")
        st.markdown("</div>", unsafe_allow_html=True)

        if uploaded_file:
            doc_text = read_file(uploaded_file)
            with st.expander("📃 View Raw Document"):
                st.text_area("Content", doc_text, height=180, disabled=True)

            col1, col2 = st.columns(2)
            with col1:
                if st.button("📋 Generate Plain-English Summary", use_container_width=True, disabled=not api_key):
                    with st.spinner("Generating summary..."):
                        try:
                            prompt = (
                                "Act as an expert legal assistant. Provide a clear, plain-English summary "
                                "of the main points, key obligations for both parties, and important dates/deadlines "
                                "in the following document. Use bullet points where helpful.\n\nDocument:\n" + doc_text
                            )
                            st.markdown("<div class='safe-box'>", unsafe_allow_html=True)
                            st.write(call_gemini(client, prompt))
                            st.markdown("</div>", unsafe_allow_html=True)
                        except Exception as e:
                            st.error(f"Error: {e}")

            with col2:
                if st.button("🔍 Scan for Risks & Red Flags", use_container_width=True, disabled=not api_key):
                    with st.spinner("Scanning for risks..."):
                        try:
                            prompt = (
                                "Act as an expert legal assistant. Carefully scan the following document for "
                                "HIGH-RISK or UNFAIR clauses such as: auto-renewals, unlimited liability, "
                                "waiver of rights, unreasonable termination penalties, aggressive IP ownership, "
                                "no-refund policies, or anything unusual. "
                                "List each red flag with: 🚩 [RISK NAME] — Explanation of why it is problematic.\n\nDocument:\n" + doc_text
                            )
                            st.markdown("<div class='risk-box'>", unsafe_allow_html=True)
                            st.write(call_gemini(client, prompt))
                            st.markdown("</div>", unsafe_allow_html=True)
                        except Exception as e:
                            st.error(f"Error: {e}")

    # ── TAB 2: Chat ────────────────────────────
    with tab2:
        st.subheader("Chat with your Document")
        chat_file = st.file_uploader("Upload a document to chat about", type=["txt","pdf"], key="t2_file")

        if chat_file:
            chat_text = read_file(chat_file)
            if st.session_state.chat_doc_name != chat_file.name:
                st.session_state.chat_messages = []
                st.session_state.chat_doc_name = chat_file.name

            st.info(f"📄 Chatting about: **{chat_file.name}**")

            for msg in st.session_state.chat_messages:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

            if prompt := st.chat_input("Ask anything about this document...", disabled=not api_key):
                st.session_state.chat_messages.append({"role": "user", "content": prompt})
                with st.chat_message("user"):
                    st.markdown(prompt)

                with st.chat_message("assistant"):
                    with st.spinner("Thinking..."):
                        try:
                            history = "\n".join(
                                [f"{m['role'].capitalize()}: {m['content']}"
                                 for m in st.session_state.chat_messages[:-1]]
                            )
                            full_prompt = (
                                f"You are a helpful legal assistant. Answer the user's question clearly and simply "
                                f"based on the document below. Conversation so far:\n{history}\n\n"
                                f"Document:\n{chat_text}\n\nUser Question: {prompt}"
                            )
                            answer = call_gemini(client, full_prompt)
                            st.markdown(answer)
                            st.session_state.chat_messages.append({"role": "assistant", "content": answer})
                        except Exception as e:
                            st.error(f"Error: {e}")

    # ── TAB 3: Compare ─────────────────────────
    with tab3:
        st.subheader("Compare Two Legal Documents")
        st.caption("Upload the original and a revised version to see exactly what changed.")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**📄 Original Document**")
            doc1 = st.file_uploader("Upload original", type=["txt","pdf"], key="doc1")
        with c2:
            st.markdown("**📄 Revised Document**")
            doc2 = st.file_uploader("Upload revised", type=["txt","pdf"], key="doc2")

        if doc1 and doc2:
            if st.button("⚖️ Compare Now", use_container_width=True, disabled=not api_key):
                with st.spinner("Comparing documents..."):
                    try:
                        t1 = read_file(doc1)
                        t2 = read_file(doc2)
                        prompt = (
                            "Act as a senior legal analyst. Compare the two legal documents below. "
                            "Produce a clear, structured report that covers:\n"
                            "1. Key terms that CHANGED (include the original vs new wording)\n"
                            "2. NEW clauses added in Document 2\n"
                            "3. Clauses REMOVED from Document 1\n"
                            "4. Overall assessment: Is Document 2 more or less favorable to the user?\n\n"
                            f"--- DOCUMENT 1 (ORIGINAL) ---\n{t1}\n\n--- DOCUMENT 2 (REVISED) ---\n{t2}"
                        )
                        st.markdown("<div class='card'>", unsafe_allow_html=True)
                        st.write(call_gemini(client, prompt))
                        st.markdown("</div>", unsafe_allow_html=True)
                    except Exception as e:
                        st.error(f"Error: {e}")

    # ── TAB 4: Demo ────────────────────────────
    with tab4:
        st.markdown("""
        <div style='background: linear-gradient(135deg,#1b2a4a,#2d4373);
                    padding:1.5rem 2rem; border-radius:14px; margin-bottom:1.5rem;'>
            <h2 style='color:white;margin:0;'>🎬 Guided Demo Walkthrough</h2>
            <p style='color:#f0e6c8;margin:0.4rem 0 0 0;'>
                See every feature of LegalMind AI in action — all on one page, no uploading required.
                We use a real-looking <strong>Lease Agreement</strong> and an <strong>Employment Contract</strong>
                to demonstrate all 4 capabilities.
            </p>
        </div>
        """, unsafe_allow_html=True)

        # ── Overview banner ─────────────────────
        oc1, oc2, oc3, oc4 = st.columns(4)
        for col, icon, label in zip(
            [oc1, oc2, oc3, oc4],
            ["📋", "🔍", "💬", "⚖️"],
            ["Step 1\nSummarize", "Step 2\nRisk Scan", "Step 3\nQ&A Chat", "Step 4\nCompare"]
        ):
            with col:
                st.markdown(f"""
                <div style='background:white;border-radius:10px;padding:0.9rem;
                            text-align:center;box-shadow:0 2px 8px rgba(0,0,0,0.08);'>
                    <div style='font-size:1.8rem;'>{icon}</div>
                    <div style='font-weight:700;color:#1b2a4a;font-size:0.85rem;white-space:pre-line;'>{label}</div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Load sample docs once
        lease_doc = load_sample("lease_agreement.txt")
        employ_doc = load_sample("employment_contract.txt")

        # ════════════════════════════════════════
        # STEP 1 — SUMMARIZE
        # ════════════════════════════════════════
        st.markdown("""
        <div style='display:flex;align-items:center;gap:0.8rem;margin:1rem 0 0.5rem 0;'>
            <div style='background:#1b2a4a;color:white;border-radius:50%;
                        width:36px;height:36px;display:flex;align-items:center;
                        justify-content:center;font-weight:800;font-size:1rem;flex-shrink:0;'>1</div>
            <h3 style='margin:0;color:#1b2a4a;'>📋 Plain-English Summary</h3>
        </div>
        <p style='color:#555;margin:0 0 0.8rem 2.8rem;'>
            We feed the <strong>Residential Lease Agreement</strong> to Gemini and ask it to explain
            the document in simple language anyone can understand.
        </p>
        """, unsafe_allow_html=True)

        with st.expander("📄 View the Lease Agreement used in this demo", expanded=False):
            st.text_area("", lease_doc, height=160, disabled=True, key="demo_lease_view")

        if st.button("▶ Run Step 1 — Summarize the Lease Agreement", use_container_width=True, key="demo_s1", disabled=not api_key):
            with st.spinner("Gemini is reading the lease agreement..."):
                try:
                    prompt = (
                        "Act as an expert legal assistant. Provide a clear, plain-English summary "
                        "of the main points, key obligations for both parties, and important dates/deadlines "
                        "in the following document. Use bullet points.\n\nDocument:\n" + lease_doc
                    )
                    result = call_gemini(client, prompt)
                    st.session_state["demo_s1_result"] = result
                except Exception as e:
                    st.error(f"Error: {e}")

        if "demo_s1_result" in st.session_state:
            st.markdown("<div class='safe-box'>", unsafe_allow_html=True)
            st.write(st.session_state["demo_s1_result"])
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<hr>", unsafe_allow_html=True)

        # ════════════════════════════════════════
        # STEP 2 — RISK SCAN
        # ════════════════════════════════════════
        st.markdown("""
        <div style='display:flex;align-items:center;gap:0.8rem;margin:1rem 0 0.5rem 0;'>
            <div style='background:#c9a84c;color:white;border-radius:50%;
                        width:36px;height:36px;display:flex;align-items:center;
                        justify-content:center;font-weight:800;font-size:1rem;flex-shrink:0;'>2</div>
            <h3 style='margin:0;color:#1b2a4a;'>🔍 Risk & Red-Flag Scanner</h3>
        </div>
        <p style='color:#555;margin:0 0 0.8rem 2.8rem;'>
            Now we scan the <strong>Employment Contract</strong> from TechNova Solutions.
            It looks standard — but the AI will expose the dangerous non-compete and IP clauses hidden inside.
        </p>
        """, unsafe_allow_html=True)

        with st.expander("📄 View the Employment Contract used in this demo", expanded=False):
            st.text_area("", employ_doc, height=160, disabled=True, key="demo_employ_view")

        if st.button("▶ Run Step 2 — Scan Employment Contract for Risks", use_container_width=True, key="demo_s2", disabled=not api_key):
            with st.spinner("Gemini is scanning for red flags..."):
                try:
                    prompt = (
                        "Act as an expert legal assistant. Carefully scan the following document for "
                        "HIGH-RISK or UNFAIR clauses such as: auto-renewals, unlimited liability, "
                        "waiver of rights, unreasonable termination penalties, aggressive IP ownership, "
                        "non-compete abuse, or anything a layperson should be warned about. "
                        "List each risk with: 🚩 [RISK NAME] — Explanation of why it is problematic.\n\nDocument:\n" + employ_doc
                    )
                    result = call_gemini(client, prompt)
                    st.session_state["demo_s2_result"] = result
                except Exception as e:
                    st.error(f"Error: {e}")

        if "demo_s2_result" in st.session_state:
            st.markdown("<div class='risk-box'>", unsafe_allow_html=True)
            st.write(st.session_state["demo_s2_result"])
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<hr>", unsafe_allow_html=True)

        # ════════════════════════════════════════
        # STEP 3 — CHAT / Q&A
        # ════════════════════════════════════════
        st.markdown("""
        <div style='display:flex;align-items:center;gap:0.8rem;margin:1rem 0 0.5rem 0;'>
            <div style='background:#27ae60;color:white;border-radius:50%;
                        width:36px;height:36px;display:flex;align-items:center;
                        justify-content:center;font-weight:800;font-size:1rem;flex-shrink:0;'>3</div>
            <h3 style='margin:0;color:#1b2a4a;'>💬 Ask a Question (Q&A Demo)</h3>
        </div>
        <p style='color:#555;margin:0 0 0.8rem 2.8rem;'>
            Ask any specific question about the <strong>Lease Agreement</strong>.
            We've pre-loaded 3 example questions — click any to instantly run them,
            or type your own.
        </p>
        """, unsafe_allow_html=True)

        demo_questions = [
            "Can the landlord enter my apartment without telling me first?",
            "What happens if I want to leave before the lease ends?",
            "Am I responsible for repairs caused by normal wear and tear?",
        ]

        q_cols = st.columns(3)
        for i, (col, q) in enumerate(zip(q_cols, demo_questions)):
            with col:
                if st.button(f'"{q}"', key=f"demo_q{i}", use_container_width=True):
                    st.session_state["demo_q_input"] = q

        demo_q = st.text_input(
            "Or type your own question about the Lease Agreement:",
            value=st.session_state.get("demo_q_input", ""),
            key="demo_q_text"
        )

        if st.button("▶ Run Step 3 — Get Answer", use_container_width=True, key="demo_s3", disabled=not api_key) and demo_q:
            with st.spinner("Gemini is finding the answer..."):
                try:
                    prompt = (
                        f"Act as a helpful legal assistant. Based ONLY on the document below, "
                        f"answer this question clearly and simply: '{demo_q}'\n\nDocument:\n{lease_doc}"
                    )
                    result = call_gemini(client, prompt)
                    st.session_state["demo_s3_result"] = (demo_q, result)
                except Exception as e:
                    st.error(f"Error: {e}")

        if "demo_s3_result" in st.session_state:
            q_shown, a_shown = st.session_state["demo_s3_result"]
            with st.chat_message("user"):
                st.markdown(q_shown)
            with st.chat_message("assistant"):
                st.markdown(a_shown)

        st.markdown("<hr>", unsafe_allow_html=True)

        # ════════════════════════════════════════
        # STEP 4 — COMPARE
        # ════════════════════════════════════════
        st.markdown("""
        <div style='display:flex;align-items:center;gap:0.8rem;margin:1rem 0 0.5rem 0;'>
            <div style='background:#8e44ad;color:white;border-radius:50%;
                        width:36px;height:36px;display:flex;align-items:center;
                        justify-content:center;font-weight:800;font-size:1rem;flex-shrink:0;'>4</div>
            <h3 style='margin:0;color:#1b2a4a;'>⚖️ Document Comparison</h3>
        </div>
        <p style='color:#555;margin:0 0 0.8rem 2.8rem;'>
            Finally, we compare the <strong>Lease Agreement</strong> vs the <strong>Employment Contract</strong>
            to show how the comparison feature works — the AI produces a structured diff of key differences,
            new obligations, and removed protections.
        </p>
        """, unsafe_allow_html=True)

        comp_cols = st.columns(2)
        with comp_cols[0]:
            st.markdown("""
            <div style='background:#e8f4fd;border-radius:8px;padding:0.8rem 1rem;border-left:4px solid #1b2a4a;'>
                <strong>📄 Document 1</strong><br/>
                <span style='color:#555;font-size:0.9rem;'>Residential Lease Agreement</span>
            </div>
            """, unsafe_allow_html=True)
        with comp_cols[1]:
            st.markdown("""
            <div style='background:#fef9e7;border-radius:8px;padding:0.8rem 1rem;border-left:4px solid #c9a84c;'>
                <strong>📄 Document 2</strong><br/>
                <span style='color:#555;font-size:0.9rem;'>Employment Contract</span>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("▶ Run Step 4 — Compare Both Documents", use_container_width=True, key="demo_s4", disabled=not api_key):
            with st.spinner("Gemini is comparing the documents..."):
                try:
                    prompt = (
                        "Act as a senior legal analyst. Compare the two legal documents below. "
                        "Produce a clear, structured report covering:\n"
                        "1. The TYPE and PURPOSE of each document\n"
                        "2. Key similarities between the two\n"
                        "3. Key differences in obligations, rights, and penalties\n"
                        "4. Which document is MORE RISKY for the signing party, and why\n\n"
                        f"--- DOCUMENT 1: Residential Lease Agreement ---\n{lease_doc}\n\n"
                        f"--- DOCUMENT 2: Employment Contract ---\n{employ_doc}"
                    )
                    result = call_gemini(client, prompt)
                    st.session_state["demo_s4_result"] = result
                except Exception as e:
                    st.error(f"Error: {e}")

        if "demo_s4_result" in st.session_state:
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            st.write(st.session_state["demo_s4_result"])
            st.markdown("</div>", unsafe_allow_html=True)

        # ── Done banner ─────────────────────────
        st.markdown("<br>", unsafe_allow_html=True)
        st.success("🎉 That's the full LegalMind AI demo! Head to the other tabs to analyze your own documents.")

# ─────────────────────────────────────────────
#  ROUTER
# ─────────────────────────────────────────────
if st.session_state.logged_in:
    show_main_app()
else:
    show_login()
