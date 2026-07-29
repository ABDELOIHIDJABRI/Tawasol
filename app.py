import streamlit as st
from supabase import create_client, Client
import pandas as pd
import datetime

# 1. إعداد الصفحة
st.set_page_config(page_title="نظام إدارة المراسلات المتكامل", layout="wide", page_icon="📑")

# 2. بيانات الاتصال بـ Supabase
SUPABASE_URL = "https://incuyohdmwfoavsnyzgc.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImluY3V5b2hkbXdmb2F2c255emdjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODUzMzM5ODYsImV4cCI6MjEwMDkwOTk4Nn0.kDgDlTsPVxobmrrXBuQJI0hdOvRwJLBpPps0IQTclC4"

CLEAN_URL = str(SUPABASE_URL).strip().strip("/")
CLEAN_KEY = str(SUPABASE_KEY).strip()

@st.cache_resource
def init_supabase():
    return create_client(CLEAN_URL, CLEAN_KEY)

supabase = init_supabase()

if "user" not in st.session_state:
    st.session_state.user = None

# ----------------- تسجيل الدخول -----------------
def login():
    st.title("🔑 تسجيل الدخول للنظام")
    col1, col2 = st.columns([1, 1])
    with col1:
        email = st.text_input("البريد الإلكتروني").strip()
        password = st.text_input("كلمة المرور", type="password").strip()
        if st.button("تسجيل الدخول", type="primary"):
            if not email or not password:
                st.warning("يرجى إدخال البيانات كاملة.")
                return
            try:
                res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                profile_res = supabase.table("profiles").select("*").eq("id", res.user.id).execute()
                if not profile_res.data:
                    st.error("⚠️ الحساب غير مسجل في جدول الصلاحيات.")
                elif not profile_res.data[0].get('is_active', False):
                    st.error("🔒 هذا الحساب معطل حاليًا من مدير النظام.")
                else:
                    st.session_state.user = profile_res.data[0]
                    st.rerun()
            except Exception as e:
                st.error(f"❌ خطأ في الدخول: {e}")

# ----------------- لوحة المدير الشاملة -----------------
def admin_dashboard():
    st.title("⚙️ لوحة قيادة مدير النظام")
    
    # الإشعارات السريعة
    pending_docs = supabase.table("documents").select("*").eq("is_deleted_pending", True).execute().data or []
    if pending_docs:
        st.warning(f"🔔 لديك ({len(pending_docs)}) طلبات حذف مستندات بانتظار الموافقة!")

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 التقارير والإحصائيات", 
        "👥 إدارة المستخدمين", 
        "📁 إدارة الأقسام", 
        "🔍 البحث والفلترة المتقدمة", 
        "🗑️ طلبات الحذف والأرشيف"
    ])

    # Tab 1: التقارير والتصدير
    with tab1:
        st.subheader("📊 إحصائيات النظام وتصدير التقارير")
        users = supabase.table("profiles").select("*").execute().data or []
        docs = supabase.table("documents").select("*").execute().data or []
        reads = supabase.table("document_reads").select("*").execute().data or []

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("إجمالي الحسابات", len(users))
        c2.metric("المستندات والمراسلات", len(docs))
        c3.metric("إجمالي الاطلاع", len(reads))
        c4.metric("الحسابات النشطة", sum(1 for u in users if u.get('is_active')))

        st.divider()
        st.write("📥 **تصدير التقارير إلى Excel:**")
        if docs:
            df_docs = pd.DataFrame(docs)
            csv_docs = df_docs.to_csv(index=False).encode('utf-8-sig')
            st.download_button("💾 تصدير سجل المراسلات (CSV)", data=csv_docs, file_name="documents_report.csv", mime="text/csv")

    # Tab 2: إدارة المستخدمين (إيقاف/تفعيل/تغيير صلاحيات)
    with tab2:
        st.subheader("👥 التعديل على صلاحيات وحالة المستخدمين")
        users_list = supabase.table("profiles").select("*").execute().data or []
        for u in users_list:
            col_a, col_b, col_c, col_d = st.columns([2, 1, 1, 1])
            col_a.write(f"👤 **{u.get('full_name')}** ({u.get('role')})")
            
            # تغيير الصلاحيات
            new_role = col_b.selectbox("الصلاحية", ["admin", "user"], index=0 if u.get('role')=='admin' else 1, key=f"role_{u['id']}")
            # تفعيل/إيقاف الحساب
            is_active = col_c.checkbox("نشط", value=u.get('is_active', True), key=f"act_{u['id']}")
            
            if col_d.button("حفظ", key=f"save_u_{u['id']}"):
                supabase.table("profiles").update({"role": new_role, "is_active": is_active}).eq("id", u['id']).execute()
                st.success("تم التحديث!")
                st.rerun()

    # Tab 3: إدارة الأقسام
    with tab3:
        st.subheader("📁 إضافة وتعديل الأقسام والجهات")
        depts = supabase.table("departments").select("*").execute().data or []
        st.dataframe(pd.DataFrame(depts), use_container_width=True)
        
        new_dept = st.text_input("اسم القسم الجديد")
        if st.button("إضافة القسم"):
            if new_dept:
                supabase.table("departments").insert({"name": new_dept}).execute()
                st.success("تمت الإضافة بنجاح!")
                st.rerun()

    # Tab 4: البحث والفلترة المتقدمة
    with tab4:
        st.subheader("🔍 البحث الدقيق المتقدم")
        search_term = st.text_input("ابحث بالعنوان، اسم الأستاذ، أو الرقم المرجعي:")
        
        all_docs = supabase.table("documents").select("*").execute().data or []
        if search_term:
            filtered = [d for d in all_docs if search_term.lower() in str(d.get('title')).lower() or search_term.lower() in str(d.get('sender_name')).lower() or search_term.lower() in str(d.get('ref_number')).lower()]
        else:
            filtered = all_docs

        st.dataframe(pd.DataFrame(filtered), use_container_width=True)

    # Tab 5: الحذف والأرشيف
    with tab5:
        st.subheader("🗑️ طلبات الحذف المعلقة")
        for doc in pending_docs:
            ca, cb, cc = st.columns([3, 1, 1])
            ca.write(f"📄 **{doc.get('title')}** (أرسله: {doc.get('sender_name')})")
            if cb.button("تأكيد الحذف", key=f"del_adm_{doc['id']}"):
                supabase.table("documents").delete().eq("id", doc['id']).execute()
                st.rerun()
            if cc.button("استرجاع", key=f"res_adm_{doc['id']}"):
                supabase.table("documents").update({"is_deleted_pending": False}).eq("id", doc['id']).execute()
                st.rerun()

# ----------------- واجهة الأساتذة والمدراء -----------------
def user_workspace():
    st.title(f"مرحبًا بك: {st.session_state.user.get('full_name')}")
    
    # جلب الأقسام
    departments_data = supabase.table("departments").select("name").execute().data or []
    dept_options = [d['name'] for d in departments_data] or ["عام"]

    st.subheader("📤 إرسال مراسلة أو مرفق جديد")
    c1, c2 = st.columns(2)
    title = c1.text_input("عنوان المراسلة")
    ref_num = c2.text_input("الرقم المرجعي (اختياري)")
    dept = c1.selectbox("القسم / الجهة", dept_options)
    uploaded_file = c2.file_uploader("الملف المرفق (PDF, Excel, صور...)")

    if st.button("إرسال المراسلة", type="primary"):
        if uploaded_file and title:
            file_path = f"{st.session_state.user['id']}/{uploaded_file.name}"
            supabase.storage.from_("attachments").upload(file_path, uploaded_file.getvalue())
            file_url = supabase.storage.from_("attachments").get_public_url(file_path)

            supabase.table("documents").insert({
                "title": title,
                "ref_number": ref_num,
                "department": dept,
                "file_url": file_url,
                "sender_id": st.session_state.user['id'],
                "sender_name": st.session_state.user['full_name']
            }).execute()
            st.success("تم إرسال المستند بنجاح!")
            st.rerun()

    st.divider()
    st.subheader("📑 المستندات والمراسلات المتاحة")
    docs = supabase.table("documents").select("*").eq("is_deleted_pending", False).execute().data or []

    for doc in docs:
        col1, col2, col3 = st.columns([3, 1, 1])
        col1.write(f"📄 **{doc.get('title')}** | القسم: `{doc.get('department', 'عام')}` | من: {doc.get('sender_name')}")
        
        if col2.button("فتح / تحميل", key=f"usr_view_{doc['id']}"):
            supabase.table("document_reads").insert({
                "document_id": doc['id'],
                "user_id": st.session_state.user['id'],
                "user_name": st.session_state.user['full_name']
            }).execute()
            st.markdown(f"[🔗 اضغط هنا لفتح الرابط]({doc['file_url']})")
        
        if st.session_state.user['id'] == doc.get('sender_id'):
            if col3.button("طلب حذف", key=f"usr_del_{doc['id']}"):
                supabase.table("documents").update({"is_deleted_pending": True}).eq("id", doc['id']).execute()
                st.warning("تم طلب الحذف.")
                st.rerun()

# ----------------- توجيه الصفحات -----------------
if st.session_state.user is None:
    login()
else:
    st.sidebar.title(f"👤 {st.session_state.user.get('full_name')}")
    st.sidebar.caption(f"الصلاحية: {st.session_state.user.get('role')}")
    if st.sidebar.button("تسجيل الخروج"):
        st.session_state.user = None
        st.rerun()

    if st.session_state.user.get('role') == 'admin':
        admin_dashboard()
    else:
        user_workspace()
