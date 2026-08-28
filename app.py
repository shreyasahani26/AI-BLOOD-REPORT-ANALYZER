import streamlit as st
import random
import smtplib
import re
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from io import BytesIO

from pypdf import PdfReader
from groq import Groq


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="AI Blood Report Analyzer",
    page_icon="🩸",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# SESSION STATE
# ============================================================

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "user_email" not in st.session_state:
    st.session_state.user_email = ""

if "generated_otp" not in st.session_state:
    st.session_state.generated_otp = None

if "otp_email" not in st.session_state:
    st.session_state.otp_email = ""

if "otp_expiry" not in st.session_state:
    st.session_state.otp_expiry = None

if "theme" not in st.session_state:
    st.session_state.theme = "Dark"


# ============================================================
# CUSTOM THEME
# ============================================================

def apply_theme():

    if st.session_state.theme == "Dark":

        background = "#0e1117"
        card = "#161b22"
        text = "#f5f5f5"
        secondary = "#b8c0cc"
        border = "#30363d"
        input_bg = "#21262d"

    else:

        background = "#f5f7fb"
        card = "#ffffff"
        text = "#1f2937"
        secondary = "#5b6472"
        border = "#d9dee7"
        input_bg = "#ffffff"

    st.markdown(
        f"""
        <style>

        /* MAIN APPLICATION */

        .stApp {{
            background-color: {background};
            color: {text};
        }}

        /* MAIN TEXT */

        .stApp p,
        .stApp label,
        .stApp span,
        .stApp div {{
            color: {text};
        }}

        /* SIDEBAR */

        section[data-testid="stSidebar"] {{
            background-color: {card};
            border-right: 1px solid {border};
        }}

        /* INPUT BOXES */

        .stTextInput input,
        .stTextArea textarea {{
            background-color: {input_bg};
            color: {text};
            border: 1px solid {border};
        }}

        /* FILE UPLOADER */

        section[data-testid="stFileUploader"] {{
            background-color: {card};
            border: 1px solid {border};
            border-radius: 12px;
            padding: 10px;
        }}

        /* CARDS */

        .custom-card {{
            background-color: {card};
            border: 1px solid {border};
            border-radius: 18px;
            padding: 25px;
            margin-bottom: 20px;
        }}

        /* WELCOME */

        .welcome-title {{
            font-size: 42px;
            font-weight: 800;
            text-align: center;
            margin-bottom: 5px;
        }}

        .welcome-subtitle {{
            text-align: center;
            font-size: 18px;
            color: {secondary};
            margin-bottom: 30px;
        }}

        /* PORTAL TITLE */

        .portal-title {{
            font-size: 38px;
            font-weight: 800;
            text-align: center;
            margin-bottom: 8px;
        }}

        .portal-subtitle {{
            text-align: center;
            font-size: 17px;
            color: {secondary};
            margin-bottom: 30px;
        }}

        /* RESULT CARD */

        .result-card {{
            background-color: {card};
            border: 1px solid {border};
            border-radius: 16px;
            padding: 22px;
            margin-top: 15px;
        }}

        /* DISCLAIMER */

        .disclaimer {{
            background-color: {card};
            border-left: 5px solid #ff4b4b;
            border-radius: 10px;
            padding: 15px;
            margin-top: 20px;
        }}

        /* THANK YOU */

        .thank-you {{
            text-align: center;
            font-size: 28px;
            font-weight: 700;
            margin-top: 30px;
            padding: 25px;
        }}

        </style>
        """,
        unsafe_allow_html=True
    )


apply_theme()


# ============================================================
# EMAIL VALIDATION
# ============================================================

def is_valid_email(email):

    pattern = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"

    return re.fullmatch(
        pattern,
        email.strip()
    ) is not None


# ============================================================
# SEND OTP EMAIL
# ============================================================

def send_otp_email(receiver_email, otp):

    try:

        sender_email = st.secrets["email"]["sender"]
        app_password = st.secrets["email"]["app_password"]

        message = MIMEMultipart()

        message["From"] = sender_email
        message["To"] = receiver_email
        message["Subject"] = "OTP - AI Blood Report Analyzer"

        body = f"""
Namaste 🙏

Welcome to the AI Blood Report Analyzer Portal.

Your One-Time Password (OTP) is:

{otp}

Please enter this OTP on the portal to complete your login.

This OTP is valid for 5 minutes.

If you did not request this OTP, please ignore this email.

Thank you,
AI Blood Report Analyzer
"""

        message.attach(
            MIMEText(body, "plain")
        )

        server = smtplib.SMTP(
            "smtp.gmail.com",
            587,
            timeout=30
        )

        server.starttls()

        server.login(
            sender_email,
            app_password
        )

        server.sendmail(
            sender_email,
            receiver_email,
            message.as_string()
        )

        server.quit()

        return True, "OTP sent successfully."

    except KeyError:

        return False, (
            "Email configuration is missing. "
            "Please check .streamlit/secrets.toml."
        )

    except smtplib.SMTPAuthenticationError:

        return False, (
            "Gmail authentication failed. "
            "Please check your Gmail address and App Password."
        )

    except smtplib.SMTPException as e:

        return False, f"Gmail error: {e}"

    except Exception as e:

        return False, f"Unexpected error: {e}"


# ============================================================
# LOGIN PAGE
# ============================================================

def login_page():

    # --------------------------------------------------------
    # THEME SECTION
    # --------------------------------------------------------

    col1, col2, col3 = st.columns(
        [1, 2, 1]
    )

    with col2:

        theme = st.radio(
            "🎨 Theme",
            ["Dark", "Light"],
            horizontal=True,
            index=0 if st.session_state.theme == "Dark" else 1
        )

        if theme != st.session_state.theme:

            st.session_state.theme = theme

            st.rerun()

    st.write("")

    # --------------------------------------------------------
    # WELCOME
    # --------------------------------------------------------

    st.markdown(
        """
        <div class="custom-card">

        <div class="welcome-title">
        🙏 Namaste 🙏
        </div>

        <div class="welcome-subtitle">
        Welcome to the AI Blood Report Analyzer Portal
        </div>

        </div>
        """,
        unsafe_allow_html=True
    )

    # --------------------------------------------------------
    # LOGIN CARD
    # --------------------------------------------------------

    st.markdown(
        """
        <div class="custom-card">

        <h2>🔐 Secure Login</h2>

        <p>
        Enter your email address and receive a
        one-time password to access the portal.
        </p>

        </div>
        """,
        unsafe_allow_html=True
    )

    # ========================================================
    # EMAIL + OTP IN ONE SECTION
    # ========================================================

    with st.container(border=True):

        st.subheader(
            "📧 Email Verification"
        )

        email = st.text_input(
            "Email Address",
            placeholder="example@gmail.com"
        )

        col1, col2 = st.columns(
            [1, 1]
        )

        # ----------------------------------------------------
        # SEND OTP
        # ----------------------------------------------------

        with col1:

            if st.button(
                "📩 Send OTP",
                use_container_width=True
            ):

                email = email.strip()

                if not email:

                    st.error(
                        "Please enter your email address."
                    )

                elif not is_valid_email(email):

                    st.error(
                        "Please enter a valid email address."
                    )

                else:

                    otp = str(
                        random.randint(
                            100000,
                            999999
                        )
                    )

                    with st.spinner(
                        "Sending OTP..."
                    ):

                        success, message = send_otp_email(
                            email,
                            otp
                        )

                    if success:

                        st.session_state.generated_otp = otp

                        st.session_state.otp_email = email

                        st.session_state.otp_expiry = (
                            datetime.now()
                            + timedelta(minutes=5)
                        )

                        st.success(
                            f"✅ OTP sent to {email}"
                        )

                        st.info(
                            "Please check your inbox or spam folder."
                        )

                    else:

                        st.error(
                            message
                        )

        # ----------------------------------------------------
        # OTP INPUT
        # ----------------------------------------------------

        entered_otp = st.text_input(
            "🔢 Enter OTP",
            max_chars=6,
            placeholder="Enter 6-digit OTP"
        )

        # ----------------------------------------------------
        # VERIFY OTP
        # ----------------------------------------------------

        with col2:

            if st.button(
                "✅ Verify & Login",
                use_container_width=True
            ):

                entered_otp = entered_otp.strip()

                if st.session_state.generated_otp is None:

                    st.error(
                        "Please request an OTP first."
                    )

                elif not entered_otp:

                    st.error(
                        "Please enter the OTP."
                    )

                elif st.session_state.otp_expiry is not None and \
                        datetime.now() > st.session_state.otp_expiry:

                    st.error(
                        "⏰ OTP has expired. Please request a new OTP."
                    )

                    st.session_state.generated_otp = None

                elif (
                    entered_otp
                    != st.session_state.generated_otp
                ):

                    st.error(
                        "❌ Incorrect OTP."
                    )

                else:

                    st.session_state.logged_in = True

                    st.session_state.user_email = (
                        st.session_state.otp_email
                    )

                    st.session_state.generated_otp = None

                    st.session_state.otp_expiry = None

                    st.success(
                        "🎉 Login successful!"
                    )

                    st.rerun()

    # --------------------------------------------------------
    # FOOTER
    # --------------------------------------------------------

    st.markdown(
        """
        <div class="thank-you">
        🩸 Your health, explained simply. 🙏
        </div>
        """,
        unsafe_allow_html=True
    )


# ============================================================
# SIDEBAR
# ============================================================

def sidebar():

    with st.sidebar:

        st.title(
            "⚙️ Dashboard Settings"
        )

        st.divider()

        st.write(
            "👤 Logged in as:"
        )

        st.success(
            st.session_state.user_email
        )

        st.divider()

        # ----------------------------------------------------
        # THEME
        # ----------------------------------------------------

        st.subheader(
            "🎨 Theme"
        )

        selected_theme = st.radio(
            "Choose appearance",
            [
                "Dark",
                "Light"
            ],
            index=(
                0
                if st.session_state.theme == "Dark"
                else 1
            )
        )

        if selected_theme != st.session_state.theme:

            st.session_state.theme = selected_theme

            st.rerun()

        st.divider()

        # ----------------------------------------------------
        # AI STATUS
        # ----------------------------------------------------

        st.subheader(
            "🤖 AI Status"
        )

        groq_key = get_groq_api_key()

        if groq_key:

            st.success(
                "AI Engine Connected"
            )

        else:

            st.error(
                "AI Engine Not Configured"
            )

        st.caption(
            "Groq API key is securely stored "
            "in Streamlit secrets."
        )

        st.divider()

        # ----------------------------------------------------
        # LOGOUT
        # ----------------------------------------------------

        if st.button(
            "🚪 Logout",
            use_container_width=True
        ):

            st.session_state.logged_in = False

            st.session_state.user_email = ""

            st.session_state.generated_otp = None

            st.session_state.otp_email = ""

            st.session_state.otp_expiry = None

            st.rerun()


# ============================================================
# GET GROQ API KEY
# ============================================================

def get_groq_api_key():

    try:

        api_key = st.secrets["groq"]["api_key"]

        if not api_key:

            return None

        return api_key.strip()

    except Exception:

        return None


# ============================================================
# EXTRACT PDF TEXT
# ============================================================

def extract_pdf_text(uploaded_file):

    try:

        pdf_bytes = uploaded_file.getvalue()

        pdf_file = BytesIO(
            pdf_bytes
        )

        reader = PdfReader(
            pdf_file
        )

        pages_text = []

        for page_number, page in enumerate(
            reader.pages,
            start=1
        ):

            text = page.extract_text()

            if text:

                pages_text.append(
                    f"--- Page {page_number} ---\n{text}"
                )

        final_text = "\n\n".join(
            pages_text
        )

        return final_text.strip()

    except Exception as e:

        st.error(
            f"❌ Could not read PDF: {e}"
        )

        return ""


# ============================================================
# CLEAN REPORT
# ============================================================

def clean_report_text(text):

    if not text:

        return ""

    text = re.sub(
        r"[ \t]+",
        " ",
        text
    )

    text = re.sub(
        r"\n\s*\n\s*\n+",
        "\n\n",
        text
    )

    return text.strip()


# ============================================================
# AI ANALYSIS
# ============================================================

def analyze_report(report_text):

    api_key = get_groq_api_key()

    if not api_key:

        return (
            "❌ Groq API key is not configured.\n\n"
            "Please add it to .streamlit/secrets.toml."
        )

    if not report_text:

        return (
            "❌ No blood report data was found."
        )

    try:

        client = Groq(
            api_key=api_key
        )

        # ----------------------------------------------------
        # AI PROMPT
        # ----------------------------------------------------

        prompt = f"""
You are an AI Blood Report Analysis Assistant.

You analyze laboratory blood reports and explain possible
health-related findings in simple and understandable language.

The user wants a focused report rather than a generic
parameter-by-parameter explanation.

IMPORTANT SAFETY REQUIREMENTS:

- Do NOT claim a confirmed diagnosis from laboratory
  values alone.
- Use phrases such as "may indicate", "could be associated
  with", or "possible finding".
- Do NOT prescribe medicines.
- Do NOT give medication dosage.
- Do NOT invent blood values.
- Do NOT invent reference ranges.
- Use reference ranges provided in the report whenever
  available.
- If the reference range is missing, clearly mention that.
- If there is insufficient information, say so.
- Do not assume that one abnormal value means a disease.
- Consider that laboratory interpretation depends on
  age, sex, symptoms, medical history and laboratory
  reference ranges.
- Encourage professional medical consultation when
  appropriate.

BLOOD REPORT:

{report_text}

============================================================

Give the final response ONLY in the following structure.

# 🩺 1. Possible Conditions / Deficiencies

Identify the most relevant possible conditions,
nutritional deficiencies, or health concerns that the
reported values MAY suggest.

For each finding provide:

**Possible Finding:**  
**Evidence from Report:**  
**Why it may indicate this:**  

Do not call it a confirmed diagnosis.

If everything appears within the provided ranges,
say that no obvious abnormality is identified from the
provided values.

============================================================

# ⚠️ 2. What May Be Low, High or Abnormal

List the important abnormal values.

For each:

**Parameter:**  
**Result:**  
**Reference Range:**  
**Status:** High / Low / Borderline / Normal / Unknown  
**Reason:**  

Only mention values actually present in the report.

============================================================

# 🔍 3. Symptoms That May Be Associated

For each possible condition or deficiency identified above,
list common symptoms that can sometimes be associated with it.

Clearly state that symptoms are not proof of the condition.

Example:

- Fatigue
- Weakness
- Dizziness

Explain briefly why the symptom can be associated.

============================================================

# 💡 4. Possible Reasons / Causes

Explain common reasons that could contribute to the
abnormal finding.

Consider general categories such as:

- Dietary factors
- Nutritional deficiency
- Lifestyle
- Dehydration
- Infection
- Medication effects
- Underlying health conditions

Do not claim that any one cause is definitely responsible.

============================================================

# 🧪 5. Suggested Diagnostic / Follow-up Tests

Suggest reasonable follow-up laboratory tests that a doctor
may consider based on the findings.

For each test:

**Test:**  
**Why it may be useful:**  

Do not order tests as a doctor.
Use language such as "a doctor may consider".

============================================================

# 🥗 6. Dietary Guidelines

Give practical general dietary guidance based on the
possible findings.

Include:

- Foods that may be useful
- Nutrients to focus on
- General hydration guidance
- Foods that may be reasonable to limit if relevant

Do NOT prescribe supplements or medication doses.

============================================================

# 👨‍⚕️ 7. When to Consult a Doctor

Explain when the user should discuss these findings
with a qualified healthcare professional.

Mention urgent medical attention only when the report
contains findings that could reasonably warrant it.

============================================================

# ⚠️ Medical Disclaimer

This AI-generated analysis is for educational and
informational purposes only. It is not a confirmed
medical diagnosis and does not replace evaluation by
a qualified healthcare professional.

============================================================

# 🙏 Thank You

End with:

"Thank you for using the AI Blood Report Analyzer Portal.
Stay informed, stay healthy. 🙏"
"""

        # ----------------------------------------------------
        # GROQ REQUEST
        # ----------------------------------------------------

        response = client.chat.completions.create(

            model="openai/gpt-oss-20b",

            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a careful, evidence-based "
                        "blood report explanation assistant. "
                        "Never provide a confirmed diagnosis "
                        "from laboratory values alone."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],

            temperature=0.2,

            max_completion_tokens=5000
        )

        result = response.choices[0].message.content

        if not result:

            return (
                "❌ The AI returned an empty response."
            )

        return result

    except Exception as e:

        return (
            "❌ An error occurred during AI analysis.\n\n"
            f"Error details:\n{e}\n\n"
            "Please check your Groq configuration and "
            "internet connection."
        )


# ============================================================
# DASHBOARD
# ============================================================

def dashboard():

    sidebar()

    # --------------------------------------------------------
    # HEADER
    # --------------------------------------------------------

    st.markdown(
        """
        <div class="custom-card">

        <div class="portal-title">
        🩸 AI Blood Report Analyzer
        </div>

        <div class="portal-subtitle">
        Intelligent laboratory report analysis powered by AI
        </div>

        </div>
        """,
        unsafe_allow_html=True
    )

    # --------------------------------------------------------
    # INPUT METHOD
    # --------------------------------------------------------

    st.subheader(
        "📄 Select Report Input"
    )

    input_method = st.radio(
        "Choose one:",
        [
            "📁 Upload PDF Report",
            "📝 Paste Raw Text"
        ],
        horizontal=True
    )

    report_text = ""

    # ========================================================
    # PDF
    # ========================================================

    if input_method == "📁 Upload PDF Report":

        st.markdown(
            """
            <div class="custom-card">

            <h2>📁 Upload Your Blood Report</h2>

            <p>
            Upload a laboratory blood report in PDF format.
            </p>

            </div>
            """,
            unsafe_allow_html=True
        )

        uploaded_file = st.file_uploader(
            "Select Blood Report PDF",
            type=["pdf"],
            accept_multiple_files=False
        )

        if uploaded_file is not None:

            st.success(
                f"✅ {uploaded_file.name} uploaded successfully."
            )

            file_size_kb = (
                uploaded_file.size / 1024
            )

            st.caption(
                f"File size: {file_size_kb:.2f} KB"
            )

            with st.spinner(
                "📖 Reading blood report..."
            ):

                report_text = extract_pdf_text(
                    uploaded_file
                )

            if report_text:

                st.success(
                    "✅ Blood report text extracted successfully."
                )

                with st.expander(
                    "👀 View Extracted Report"
                ):

                    st.text_area(
                        "Extracted report text",
                        report_text,
                        height=300
                    )

            else:

                st.warning(
                    "⚠️ No readable text was found in this PDF."
                )

                st.info(
                    "If this is a scanned/image-only PDF, "
                    "OCR will be required."
                )

    # ========================================================
    # RAW TEXT
    # ========================================================

    else:

        st.markdown(
            """
            <div class="custom-card">

            <h2>📝 Paste Blood Report</h2>

            <p>
            Paste laboratory values directly below.
            </p>

            </div>
            """,
            unsafe_allow_html=True
        )

        report_text = st.text_area(
            "Blood Report Values",
            placeholder="""Example:

Hemoglobin: 10.2 g/dL
RBC: 3.9 million/µL
WBC: 7,000 /µL
Platelets: 2.4 lakh/µL
Blood Sugar: 92 mg/dL
Cholesterol: 175 mg/dL
Creatinine: 0.8 mg/dL
TSH: 2.1 µIU/mL
Vitamin B12: 180 pg/mL
Vitamin D: 18 ng/mL
Ferritin: 15 ng/mL
""",
            height=320
        )

    # ========================================================
    # ANALYZE BUTTON
    # ========================================================

    st.divider()

    if st.button(
        "🔬 Analyze Blood Report",
        type="primary",
        use_container_width=True
    ):

        if not report_text.strip():

            st.error(
                "❌ Please upload a PDF or paste "
                "your blood report first."
            )

            return

        if not get_groq_api_key():

            st.error(
                "❌ Groq API key is not configured."
            )

            st.info(
                "Please check your .streamlit/secrets.toml file."
            )

            return

        cleaned_report = clean_report_text(
            report_text
        )

        with st.spinner(
            "🤖 AI is analyzing your blood report..."
        ):

            result = analyze_report(
                cleaned_report
            )

        # ----------------------------------------------------
        # OUTPUT
        # ----------------------------------------------------

        st.divider()

        st.header(
            "📋 Blood Report Analysis"
        )

        st.markdown(
            """
            <div class="result-card">
            """,
            unsafe_allow_html=True
        )

        st.markdown(
            result
        )

        st.markdown(
            "</div>",
            unsafe_allow_html=True
        )

        # ----------------------------------------------------
        # DISCLAIMER
        # ----------------------------------------------------

        st.markdown(
            """
            <div class="disclaimer">

            <b>⚠️ Important Medical Disclaimer</b>

            <br><br>

            This AI analysis is intended for educational and
            informational purposes only. It does not provide
            a confirmed medical diagnosis and should not be
            used as a substitute for consultation with a
            qualified healthcare professional.

            </div>
            """,
            unsafe_allow_html=True
        )


# ============================================================
# APPLICATION START
# ============================================================

if st.session_state.logged_in:

    dashboard()

else:

    login_page()