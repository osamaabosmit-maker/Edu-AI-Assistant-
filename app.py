import streamlit as st
import fitz  # PyMuPDF
from docx import Document
import random
import arabic_reshaper
from bidi.algorithm import get_display
import re
import qrcode
from PIL import Image
import io

# --- 1. إعدادات الصفحة ---
st.set_page_config(page_title="Edu-AI | مساعد التقييم الذكي", page_icon="💻", layout="wide")

# --- 2. كود CSS المطور (تنسيق الواجهة وإجبار المحاذاة لليمن) ---
st.markdown("""
    <style>
    /* إجبار المحتوى العام على اليمين */
    [data-testid="stAppViewContainer"] {
        direction: rtl !important;
        text-align: right !important;
    }

    /* نقل القائمة الجانبية لليمين */
    [data-testid="stSidebar"] {
        position: fixed;
        right: 0 !important;
        left: auto !important;
        direction: rtl !important;
    }

    /* تنسيق العنوان الرئيسي */
    .main-header {
        text-align: center;
        color: #1E3A8A;
        font-family: 'Arial';
    }

    /* محاذاة "سؤال رقم" لليمين تماماً */
    .right-title {
        text-align: right !important;
        font-size: 26px;
        font-weight: bold;
        color: #333;
        margin-top: 20px;
    }

    /* تنسيق الزر الأحمر (التوجل) بمسافة كبيرة */
    div[data-testid="stCheckbox"] > label {
        display: flex !important;
        flex-direction: row-reverse !important; 
        justify-content: space-between !important;
        width: 400px !important; 
        background: #f9f9f9;
        padding: 10px 20px;
        border-radius: 15px;
        border: 1px solid #ddd;
    }

    /* لون الزر عند التفعيل */
    div[data-testid="stCheckbox"] > label > div[role="switch"][aria-checked="true"] {
        background-color: #ff4b4b !important;
    }

    /* صناديق السؤال والإجابة الملونة مع إجبار الـ RTL */
    .q-container { 
        background-color: #e3f2fd; 
        border-right: 12px solid #1565c0; 
        padding: 25px; 
        border-radius: 10px; 
        color: #0d47a1; 
        font-weight: bold; 
        margin-bottom: 10px;
        direction: rtl !important;
        text-align: right !important;
    }
    .a-container { 
        background-color: #f1f8e9; 
        border-right: 12px solid #2e7d32; 
        padding: 20px; 
        border-radius: 10px; 
        color: #1b5e20; 
        margin-bottom: 20px;
        direction: rtl !important;
        text-align: right !important;
    }

    /* تنسيق أزرار القائمة الجانبية */
    .stButton>button {
        width: 100%;
        border-radius: 20px;
        background-color: #2E7D32;
        color: white;
    }

    /* إصلاح اتجاه مربعات النصوص */
    textarea { direction: rtl !important; text-align: right !important; }
    </style>
    """, unsafe_allow_html=True)


# --- 3. وظائف المعالجة ---
def fix_visuals(text, is_rev):
    if not text: return ""
    try:
        reshaped = arabic_reshaper.reshape(text)
        if is_rev:
            return get_display(reshaped)
        return reshaped
    except:
        return text


def clean_for_match(text):
    if not text: return ""
    text = text.lower()
    text = re.sub(r'[\u064B-\u0652]', '', text)
    text = re.sub(r'[أإآ]', 'ا', text)
    text = re.sub(r'ة', 'ه', text)
    text = re.sub(r'ى', 'ي', text)
    text = re.sub(r'[^\w\s]', ' ', text)
    return text.strip()


def get_file_content(file):
    text = ""
    if file.name.endswith('.pdf'):
        with fitz.open(stream=file.read(), filetype="pdf") as doc:
            for page in doc: text += page.get_text() + " "
    else:
        doc = Document(file)
        text = "\n".join([p.text for p in doc.paragraphs])
    return text


# --- 4. تهيئة البيانات ---
if 'qa_pairs' not in st.session_state: st.session_state['qa_pairs'] = []
if 'student_answers' not in st.session_state: st.session_state['student_answers'] = {}

# --- 5. الهيدر ---
st.markdown("<h1 class='main-header'>🏆 مبادرة Edu-AI: مساعد التقييم الذكي</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>قسم الحاسوب - كلية التربية</p>", unsafe_allow_html=True)
st.divider()

# --- 6. القائمة الجانبية (جهة اليمين) ---
with st.sidebar:
    st.markdown("<h2 style='text-align: center;'>⚙️ لوحة التحكم</h2>", unsafe_allow_html=True)
    f = st.file_uploader("ارفع ملف المنهج (PDF/Word)", type=['pdf', 'docx'])

    if f and st.button("استخراج الأسئلة ✨"):
        with st.spinner('جاري معالجة الملف...'):
            content = get_file_content(f)
            paragraphs = [p.strip() for p in content.split('.') if len(p.strip()) > 40]
            extracted = []
            for p in paragraphs:
                parts = p.split(":", 1)
                q_text = parts[0] if len(parts) > 1 else p[:50]
                a_text = parts[1] if len(parts) > 1 else p[50:]
                extracted.append({"q": q_text, "a": a_text})

            st.session_state['qa_pairs'] = random.sample(extracted, min(5, len(extracted)))
            st.session_state['student_answers'] = {}
            st.success("✅ تم توليد الأسئلة بنجاح!")

    st.divider()
    if st.button("🗑️ مسح الجلسة"):
        st.session_state['qa_pairs'] = []
        st.session_state['student_answers'] = {}
        st.rerun()

    # --- إضافة كود QR Code في نهاية القائمة الجانبية ---
    st.divider()
    st.markdown("<h3 style='text-align: center;'>📲 امسح لتجربة التطبيق</h3>", unsafe_allow_html=True)

    app_url = "https://6nf8bn7hpt8surrdagdchk.streamlit.app/"

    qr = qrcode.QRCode(version=1, box_size=10, border=2)
    qr.add_data(app_url)
    qr.make(fit=True)
    img_qr = qr.make_image(fill_color="#1E3A8A", back_color="white")  # لون أزرق ملكي متناسق

    buf = io.BytesIO()
    img_qr.save(buf, format="PNG")
    st.image(buf, use_container_width=True, caption="الركن التفاعلي Edu-AI")

# --- 7. عرض المحتوى ---
if not st.session_state['qa_pairs']:
    st.info("💡 يرجى رفع ملف المنهج من القائمة الجانبية للبدء.")
else:
    for i, item in enumerate(st.session_state['qa_pairs']):
        col_r, col_l = st.columns([2, 1])

        with col_r:
            st.markdown(f'<p class="right-title">❓ السؤال رقم ({i + 1})</p>', unsafe_allow_html=True)

        with col_l:
            is_rev = st.toggle("إصلاح اتجاه النص بصرياً", key=f"rev_{i}")

        st.markdown(f"<div class='q-container'>📖 السؤال: {fix_visuals(item['q'], is_rev)}</div>",
                    unsafe_allow_html=True)
        st.markdown(f"<div class='a-container'>📘 نموذج الإجابة الصحيحة: {fix_visuals(item['a'], is_rev)}</div>",
                    unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**✍️ تعديل النموذج:**")
            st.text_area("", value=item['a'], key=f"m_{i}", height=120, label_visibility="collapsed")
        with c2:
            st.markdown("**📝 إجابة الطالب:**")
            s_ans = st.text_area("", placeholder="أدخل إجابة الطالب هنا...", key=f"s_{i}", height=120,
                                 label_visibility="collapsed")
            st.session_state['student_answers'][i] = s_ans

        st.divider()

    # --- 8. التقرير النهائي ---
    if st.button("🚀 عرض التقرير النهائي"):
        st.header("📊 التقرير التفصيلي للأداء")
        total_score = 0
        num_q = len(st.session_state['qa_pairs'])

        for i, item in enumerate(st.session_state['qa_pairs']):
            student_ans = st.session_state['student_answers'].get(i, "").strip()
            model_ans = st.session_state.get(f"m_{i}", item['a'])

            st.subheader(f"تحليل السؤال ({i + 1}):")
            if student_ans:
                m_words = set(clean_for_match(model_ans).split())
                s_words = set(clean_for_match(student_ans).split())

                keywords = {w for w in m_words if len(w) > 2}
                found = s_words.intersection(keywords)
                score = int((len(found) / len(keywords)) * 100) if keywords else 0
                if score > 85: score = 100

                total_score += score
                st.write(f"🔹 **درجة المطابقة:** {score}%")
                if score >= 70:
                    st.success("✅ إجابة الطالب مطابقة للمعايير.")
                else:
                    st.warning("⚠️ إجابة تحتاج لتعزيز المفاهيم.")
            else:
                st.error("🚫 لم يتم إدخال إجابة لهذا السؤال.")
            st.write("---")

        avg = total_score / num_q
        st.metric("المعدل النهائي العام", f"{int(avg)}%")
        if avg >= 50: st.balloons()
