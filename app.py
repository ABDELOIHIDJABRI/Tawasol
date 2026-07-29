import streamlit as st
from supabase import create_client, Client
import pandas as pd

# ----------------- 1. إعداد الصفحة وتنسيق CSS العربي -----------------
st.set_page_config(
    page_title="منصة إدارة المراسلات الرقمية",
    layout="wide",
    page_icon="🏢",
    initial_sidebar_state="expanded"
)

# تطبيق تنسيقات CSS لجعل الواجهة احترافية، عربية (RTL)، وبألوان مريحة
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap');
    
    html, body, [class*="css"], div, span, button, input {
        font-family: 'Cairo', sans-serif !important;
        direction: rtl;
        text-align: right;
    }
    
    .stApp {
        background-color: #f8f9fa;
    }
    
    /* بطاقات الإحصائيات */
    .metric-card {
        background: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.04);
        border-right: 5px solid #1E88E5;
        margin-bottom: 15px;
    }
    .metric-title { font-size: 14px; color: #6c757d; font-weight: 600; }
    .metric-value { font-size: 28px; color: #212529; font-weight: 700; }
    
    /* تحسين شكل الأزرار */
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    /* Tabs التبويبات */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #e9ecef;
        padding: 6px;
        border-radius: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 45px;
        border-radius: 8px;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        background-color: #1E88E5 !important;
        color: white !important;
    }
</style>
""", unsafe_allow_all_unicode=True, unsafe_allow_html=True)

# ----------------- 2. الاتصال بـ Supabase -----------------
SUPABASE_URL = "https://incuyohdmwfoavsnyzgc.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImluY3V5b2hkbXdmb2F2c255emdjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODUzMzM5ODYsImV4cCI6MjEwMDkwOTk4Nn0.kDgDlTsPVxobmrrXBuQJI0hdOvRwJLBpPps0IQTclC4"

@st.cache_resource
def init_supabase():
    return create_client(SUPABASE_URL.strip(), SUPABASE_KEY.strip())

supabase = init_supabase()

if "user" not in st.session_state:
    st.session_state.user = None

# ----------------- 3. شاشة تسجيل الدخول -----------------
def show_login():
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown("""
        <div style="background: white; padding: 35px; border-radius: 15px; box-shadow: 0 10px 25px rgba(0,0,0,0.08); text-align: center;">
            <h2 style="color: #1E88E5; margin-bottom: 5px;">🏢 منصة المراسلات</h2>
            <p style="color: #6c757d; font-size: 14px;">تسجيل الدخول للنظام الإداري</p>
        </div>
        """, unsafe_allow_html=True)
        st.write("")
        email = st.text_input("📧 البريد الإلكتروني", placeholder="example@domain.com")
        password = st.text_input("🔒 كلمة المرور", type="password")
        st.write("")
        if st.button("ورود للنظام ➔", type="primary"):
            if not email or not password:
                st.warning("⚠️ يرجى إدخال جميع البيانات المطلوب.")
            else:
                try:
                    res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                    profile = supabase.table("profiles").select("*").eq("id", res.user.id).execute()
                    if not profile.data:
                        st.error("⚠️ خطأ: الملف الشخصي غير موجود.")
                    elif not profile.data[0].get('is_active', True):
                        st.error("🔒 هذا الحساب معطل حالياً من قبل الإدارة.")
                    else:
                        st.session_state.user = profile.data[0]
                        st.rerun()
                except Exception as e:
                    st.error("❌ بيانات الدخول غير صحيحة، أو الحساب غير محقق.")

# ----------------- 4. لوحة التحكم للمدير -----------------
def show_admin_dashboard():
    st.markdown("## ⚙️ لوحة قيادة مدير النظام")
    st.caption("إدارة كاملة للمستخدمين، المراسلات، الأقسام والإحصائيات")
    st.divider()

    # الإشعارات السريعة
    pending_docs = supabase.table("documents").select("*").eq("is_deleted_pending", True).execute().data or []
    if pending_docs:
        st.error(f"🚨 تنبيه: هناك **{len(pending_docs)}** طلبات حذف مستندات تنتظر قرارك!")

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 ملخص النظام", 
        "➕ إضافة مستخدم جديد", 
        "👥 إدارة الحسابات", 
        "📁 الأقسام والجهات", 
        "🗑️ طلبات الحذف"
    ])

    # Tab 1: الإحصائيات
    with tab1:
        st.subheader("📊 المؤشرات العامة")
        users = supabase.table("profiles").select("*").execute().data or []
        docs = supabase.table("documents").select("*").execute().data or []
        reads = supabase.table("document_reads").select("*").execute().data or []

        m1, m2, m3, m4 = st.columns(4)
        m1.markdown(f'<div class="metric-card"><div class="metric-title">👥 إجمالي المستخدمين</div><div class="metric-value">{len(users)}</div></div>', unsafe_allow_html=True)
        m2.markdown(f'<div class="metric-card"><div class="metric-title">📄 المراسلات المسجلة</div><div class="metric-value">{len(docs)}</div></div>', unsafe_allow_html=True)
        m3.markdown(f'<div class="metric-card"><div class="metric-title">👁️ عمليات الإطلاع</div><div class="metric-value">{len(reads)}</div></div>', unsafe_allow_html=True)
        m4.markdown(f'<div class="metric-card"><div class="metric-title">✅ الحسابات النشطة</div><div class="metric-value">{sum(1 for u in users if u.get("is_active", True))}</div></div>', unsafe_allow_html=True)

        st.subheader("📥 تصدير السجلات")
        if docs:
            df = pd.DataFrame(docs)
            st.download_button(
                label="💾 تحميل تقرير المراسلات (CSV)",
                data=df.to_csv(index=False).encode('utf-8-sig'),
                file_name="report_documents.csv",
                mime="text/csv"
            )

    # Tab 2: إضافة مستخدم جديد مباشرة
    with tab2:
        st.subheader("➕ إنشاء حساب مستخدم جديد")
        st.info("💡 يمكنك من هنا إنشاء حساب جديد فوراً لأي أستاذ أو مدير.")
        
        with st.form("create_user_form", clear_on_submit=True):
            col_a, col_b = st.columns(2)
            new_email = col_a.text_input("البريد الإلكتروني للجديد*")
            new_pass = col_b.text_input("كلمة المرور*", type="password")
            new_name = col_a.text_input("الاسم الكامل*")
            new_role = col_b.selectbox("الصلاحية", ["user", "admin"], format_func=lambda x: "أستاذ / مستخدم" if x=="user" else "مدير نظام")
            
            submit_create = st.form_submit_button("✨ إنشاء الحساب الآن", type="primary")
            
            if submit_create:
                if not new_email or not new_pass or not new_name:
                    st.warning("⚠️ الرجاء ملء جميع الحقول المطلوبة.")
                else:
                    try:
                        # إنشاء المستخدم في Supabase Auth
                        auth_res = supabase.auth.sign_up({"email": new_email, "password": new_pass})
                        if auth_res.user:
                            # إضافة البيانات في جدول الملفات الشخصية
                            supabase.table("profiles").upsert({
                                "id": auth_res.user.id,
                                "full_name": new_name,
                                "role": new_role,
                                "is_active": True
                            }).execute()
                            st.success(f"✅ تم إنشاء حساب {new_name} بنجاح!")
                    except Exception as err:
                        st.error(f"❌ تعذر إنشاء الحساب: {err}")

    # Tab 3: تعديل وإدارة الحسابات
    with tab3:
        st.subheader("👥 القائمة الكاملة للمستخدمين")
        users_list = supabase.table("profiles").select("*").execute().data or []
        
        for u in users_list:
            with st.container():
                c1, c2, c3, c4 = st.columns([3, 2, 2, 2])
                c1.write(f"👤 **{u.get('full_name')}**")
                
                # تغيير الرتبة
                current_role = u.get('role', 'user')
                updated_role = c2.selectbox("الصلاحية", ["user", "admin"], index=0 if current_role=='user' else 1, key=f"r_{u['id']}", label_visibility="collapsed")
                
                # تفعيل أو إيقاف
                is_act = c3.checkbox("حساب نشط", value=u.get('is_active', True), key=f"a_{u['id']}")
                
                if c4.button("💾 حفظ", key=f"btn_u_{u['id']}"):
                    supabase.table("profiles").update({"role": updated_role, "is_active": is_act}).eq("id", u['id']).execute()
                    st.success("تم التحديث")
                    st.rerun()
                st.divider()

    # Tab 4: الأقسام
    with tab4:
        st.subheader("📁 الأقسام الهيكلية")
        depts = supabase.table("departments").select("*").execute().data or []
        st.table(pd.DataFrame(depts)[['id', 'name']])
        
        c_d1, c_d2 = st.columns([3, 1])
        d_name = c_d1.text_input("اسم القسم الجديد", label_visibility="collapsed", placeholder="أدخل اسم القسم...")
        if c_d2.button("إضافة قسم"):
            if d_name:
                supabase.table("departments").insert({"name": d_name}).execute()
                st.success("تمت الإضافة")
                st.rerun()

    # Tab 5: إدارة طلبات الحذف
    with tab5:
        st.subheader("🗑️ طلبات الحذف المقدمة من الأساتذة")
        if not pending_docs:
            st.info("لا توجد طلبات حذف معلقة حالياً.")
        for d in pending_docs:
            col_x, col_y, col_z = st.columns([3, 1, 1])
            col_x.write(f"📄 **{d.get('title')}** (المرسل: {d.get('sender_name')})")
            if col_y.button("✅ موافقة بالحذف", key=f"confirm_{d['id']}"):
                supabase.table("documents").delete().eq("id", d['id']).execute()
                st.rerun()
            if col_z.button("❌ رفض", key=f"reject_{d['id']}"):
                supabase.table("documents").update({"is_deleted_pending": False}).eq("id", d['id']).execute()
                st.rerun()

# ----------------- 5. واجهة المستخدمين / الأساتذة -----------------
def show_user_workspace():
    st.markdown(f"## 🖐️ أهلاً بك، {st.session_state.user.get('full_name')}")
    st.caption("مساحة المراسلات والمستندات الخاصة بك")
    st.divider()

    # الحصول على الأقسام
    depts_data = supabase.table("departments").select("name").execute().data or []
    dept_names = [d['name'] for d in depts_data] or ["عام"]

    st.subheader("📤 إرسال مستند / مراسلة جديدة")
    with st.card if hasattr(st, 'card') else st.container():
        c1, c2 = st.columns(2)
        doc_title = c1.text_input("عنوان المراسلة*")
        ref_num = c2.text_input("الرقم المرجعي (إن وجد)")
        dept = c1.selectbox("القسم الموجه إليه", dept_names)
        up_file = c2.file_uploader("اختر الملف (PDF, Word, Excel, صور)")
        
        if st.button("🚀 إرسال المراسلة الآن", type="primary"):
            if not doc_title or not up_file:
                st.warning("⚠️ يرجى كتابة العنوان وأرفاق الملف.")
            else:
                path = f"{st.session_state.user['id']}/{up_file.name}"
                supabase.storage.from_("attachments").upload(path, up_file.getvalue())
                public_url = supabase.storage.from_("attachments").get_public_url(path)

                supabase.table("documents").insert({
                    "title": doc_title,
                    "ref_number": ref_num,
                    "department": dept,
                    "file_url": public_url,
                    "sender_id": st.session_state.user['id'],
                    "sender_name": st.session_state.user['full_name']
                }).execute()
                st.success("🎉 تم إرسال المستند بنجاح!")
                st.rerun()

    st.divider()
    st.subheader("📚 أرشيف المراسلات والمستندات العامة")
    docs = supabase.table("documents").select("*").eq("is_deleted_pending", False).execute().data or []

    for doc in docs:
        with st.expander(f"📄 {doc.get('title')} - (القسم: {doc.get('department', 'عام')})"):
            st.write(f"**المرسل:** {doc.get('sender_name')}")
            if doc.get('ref_number'):
                st.write(f"**الرقم المرجعي:** {doc.get('ref_number')}")
            
            c_v, c_d = st.columns([1, 1])
            if c_v.button("🔗 فتح/تحميل المستند", key=f"view_{doc['id']}"):
                supabase.table("document_reads").insert({
                    "document_id": doc['id'],
                    "user_id": st.session_state.user['id'],
                    "user_name": st.session_state.user['full_name']
                }).execute()
                st.markdown(f"[اضغط هنا للفتح مباشرة]({doc['file_url']})")
            
            if st.session_state.user['id'] == doc.get('sender_id'):
                if c_d.button("⚠️ طلب حذف المستند", key=f"req_del_{doc['id']}"):
                    supabase.table("documents").update({"is_deleted_pending": True}).eq("id", doc['id']).execute()
                    st.info("تم تقديم طلب الحذف للمدير.")
                    st.rerun()

# ----------------- 6. التحكم بالموجهات والتنقل -----------------
if st.session_state.user is None:
    show_login()
else:
    # الشريط الجانبي
    st.sidebar.markdown(f"### 👤 {st.session_state.user.get('full_name')}")
    st.sidebar.caption(f"الصلاحية: {'مدير نظام' if st.session_state.user.get('role') == 'admin' else 'أستاذ / مستخدم'}")
    st.sidebar.divider()
    
    if st.sidebar.button("🚪 تسجيل الخروج"):
        st.session_state.user = None
        st.rerun()

    # التوجيه حسب الصلاحية
    if st.session_state.user.get('role') == 'admin':
        show_admin_dashboard()
    else:
        show_user_workspace()
