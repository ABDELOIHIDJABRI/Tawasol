import streamlit as st
from supabase import create_client, Client

# 1. إعداد الصفحة
st.set_page_config(page_title="نظام إدارة المراسلات", layout="wide")

# 2. بيانات الاتصال
SUPABASE_URL = "https://incuyohdmwfoavsnyzgc.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImluY3V5b2hkbXdmb2F2c255emdjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODUzMzM5ODYsImV4cCI6MjEwMDkwOTk4Nn0.kDgDlTsPVxobmrrXBuQJI0hdOvRwJLBpPps0IQTclC4"

CLEAN_URL = str(SUPABASE_URL).strip().strip("/")
CLEAN_KEY = str(SUPABASE_KEY).strip()

@st.cache_resource
def init_supabase():
    return create_client(CLEAN_URL, CLEAN_KEY)

supabase = init_supabase()

# تهيئة متغير الجلسة بأمان في بداية الكود
if "user" not in st.session_state:
    st.session_state.user = None

# 3. دالة تسجيل الدخول
def login():
    st.title("🔑 تسجيل الدخول للنظام")
    
    email = st.text_input("البريد الإلكتروني").strip()
    password = st.text_input("كلمة المرور", type="password").strip()
    
    if st.button("دخول"):
        if not email or not password:
            st.warning("يرجى إدخال البريد الإلكتروني وكلمة المرور.")
            return

        try:
            # تسجيل الدخول عبر Supabase
            res = supabase.auth.sign_in_with_password({
                "email": email, 
                "password": password
            })
            
            # جلب بيانات البروفايل والصلاحيات
            profile_response = supabase.table("profiles").select("*").eq("id", res.user.id).execute()
            
            if not profile_response.data:
                st.error("⚠️ الحساب غير مسجل في جدول الصلاحيات (profiles).")
            elif not profile_response.data[0].get('is_active', False):
                st.error("🔒 هذا الحساب غير نشط حاليًا. يرجى مراجعة إدارة النظام.")
            else:
                st.session_state.user = profile_response.data[0]
                st.success("تم تسجيل الدخول بنجاح! جاري التحميل...")
                st.rerun()
                
        except Exception as e:
            error_msg = str(e).encode('utf-8', errors='ignore').decode('utf-8')
            st.error(f"❌ فشل الدخول: {error_msg}")

# 4. توجيه الصفحة
if st.session_state.user is None:
    login()
else:
    user_data = st.session_state.user
    if isinstance(user_data, list):
        user_data = user_data[0]

    full_name = user_data.get('full_name', 'مستخدم')
    role = user_data.get('role', 'user')

    st.sidebar.title(f"مرحباً، {full_name}")
    st.sidebar.write(f"الصلاحية: {role}")
    
    if st.sidebar.button("تسجيل الخروج"):
        st.session_state.user = None
        st.rerun()
        
    st.title("🎉 مرحباً بك في لوحة التحكم!")
    st.success("تم تسجيل الدخول بنجاح للنظام.")
    def admin_dashboard():
    st.header("⚙️ لوحة قيادة مدير النظام")
    
    # 1. قسم الإحصائيات الشاملة
    col1, col2, col3 = st.columns(3)
    users_data = supabase.table("profiles").select("*").execute().data
    docs_data = supabase.table("documents").select("*").execute().data
    
    total_users = len(users_data)
    active_users = sum(1 for u in users_data if u['is_active'])
    pending_deletes = sum(1 for d in docs_data if d['is_deleted_pending'])
    
    col1.metric("إجمالي الحسابات", total_users)
    col2.metric("الحسابات النشطة", active_users)
    col3.metric("طلبات الحذف المعلقة", pending_deletes, delta_color="inverse")

    st.divider()

    # 2. إدارة طلبات الحذف (Soft Delete Control)
    st.subheader("🗑️ طلبات الحذف بانتظار الموافقة")
    pending_docs = supabase.table("documents").select("*").eq("is_deleted_pending", True).execute().data
    
    if not pending_docs:
        st.info("لا توجد طلبات حذف معلقة حاليًا.")
    else:
        for doc in pending_docs:
            c1, c2, c3 = st.columns([3, 1, 1])
            c1.write(f"📄 **{doc['title']}** — أرسله: {doc['sender_name']}")
            
            # موافقة المدير على الحذف النهائي
            if c2.button("تأكيد الحذف النهائي", key=f"del_{doc['id']}"):
                supabase.table("documents").delete().eq("id", doc['id']).execute()
                st.success("تم الحذف النهائي بنجاح.")
                st.rerun()
                
            # رفض الحذف واعادة الملف
            if c3.button("استرجاع الملف", key=f"res_{doc['id']}"):
                supabase.table("documents").update({"is_deleted_pending": False}).eq("id", doc['id']).execute()
                st.info("تم استرجاع الملف.")
                st.rerun()

    st.divider()

    # 3. جدول الاطلاع على المراسلات (Read Receipts)
    st.subheader("👁️ تتبع اطلاع الأساتذة والمدراء على المستندات")
    reads = supabase.table("document_reads").select("*").execute().data
    if reads:
        st.dataframe(reads, use_container_width=True)
    else:
        st.write("لم يتم تسجيل عمليات اطلاع بعد.")

# ----------------- واجهة الأساتذة والمدراء -----------------
def user_workspace():
    st.header(f"مرحبًا بك: {st.session_state.user['full_name']}")
    
    # 1. إرسال مرفق جديد
    st.subheader("📤 إرسال مرفق إلى المدير")
    title = st.text_input("عنوان المراسلة / المرفق")
    uploaded_file = st.file_uploader("اختر الملف (PDF, صور, Excel...)")
    
    if st.button("إرسال"):
        if uploaded_file and title:
            # رفع الملف إلى Supabase Storage
            file_path = f"{st.session_state.user['id']}/{uploaded_file.name}"
            supabase.storage.from_("attachments").upload(file_path, uploaded_file.getvalue())
            file_url = supabase.storage.from_("attachments").get_public_url(file_path)
            
            # تسجيل المراسلة في قاعدة البيانات
            supabase.table("documents").insert({
                "title": title,
                "file_url": file_url,
                "sender_id": st.session_state.user['id'],
                "sender_name": st.session_state.user['full_name']
            }).execute()
            
            st.success("تم إرسال المرفق بنجاح!")
        else:
            st.warning("يرجى ملء كافة البيانات واختيار ملف.")

    st.divider()

    # 2. عرض المستندات المتاحة وتتبع الاطلاع
    st.subheader("📑 المراسلات والمرفقات المتاحة")
    docs = supabase.table("documents").select("*").eq("is_deleted_pending", False).execute().data
    
    for doc in docs:
        col1, col2 = st.columns([3, 1])
        col1.write(f"📄 **{doc['title']}** (من: {doc['sender_name']})")
        
        # زر فتح الملف وتسجيل "الاطلاع"
        if col2.button("عرض / تحميل", key=f"view_{doc['id']}"):
            # تسجل في قاعدة البيانات أن هذا المستخدم فتح الملف الآن
            supabase.table("document_reads").insert({
                "document_id": doc['id'],
                "user_id": st.session_state.user['id'],
                "user_name": st.session_state.user['full_name']
            }).execute()
            st.markdown(f"[اضغط هنا لفتح الملف]({doc['file_url']})")
            
        # زر طلب الحذف (الحذف المؤقت)
        if st.session_state.user['id'] == doc['sender_id']:
            if st.button("طلب حذف الملف", key=f"req_del_{doc['id']}"):
                supabase.table("documents").update({"is_deleted_pending": True}).eq("id", doc['id']).execute()
                st.warning("تم إرسال طلب الحذف لمدير النظام للموافقة عليه.")
                st.rerun()

# ----------------- التوجيه حسب حالة الدخول -----------------
if st.session_state.user is None:
    login()
else:
    st.sidebar.write(f"المستخدم: {st.session_state.user['full_name']}")
    st.sidebar.write(f"الرتبة: {st.session_state.user['role']}")
    
    if st.sidebar.button("تسجيل الخروج"):
        st.session_state.user = None
        st.rerun()

    # توجيه حسب الصلاحيات
    if st.session_state.user['role'] == 'admin':
        admin_dashboard()
    else:
        user_workspace()
