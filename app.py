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

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap');
    
    html, body, [class*="css"], div, span, button, input {
        font-family: 'Cairo', sans-serif !important;
        direction: rtl;
        text-align: right;
    }
    
    .stApp { background-color: #f8f9fa; }
    
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
    
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

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
            <h2 style="color: #1E88E5; margin-bottom: 5px;">🏢 نظام المراسلات الإدارية</h2>
            <p style="color: #6c757d; font-size: 14px;">تسجيل الدخول للمنصة</p>
        </div>
        """, unsafe_allow_html=True)
        st.write("")
        email = st.text_input("📧 البريد الإلكتروني")
        password = st.text_input("🔒 كلمة المرور", type="password")
        st.write("")
        if st.button("دخول للنظام ➔", type="primary"):
            if not email or not password:
                st.warning("⚠️ يرجى إدخال البيانات كاملة.")
            else:
                try:
                    res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                    profile = supabase.table("profiles").select("*").eq("id", res.user.id).execute()
                    if not profile.data:
                        st.error("⚠️ ملف المستخدم غير موجود.")
                    elif not profile.data[0].get('is_active', True):
                        st.error("🔒 الحساب معطل حالياً.")
                    else:
                        st.session_state.user = profile.data[0]
                        st.rerun()
                except Exception as e:
                    st.error("❌ بيانات الدخول غير صحيحة.")

# ----------------- 4. مكون إرسال المراسلات والمرفقات (مشترك) -----------------
def render_send_document_form():
    st.subheader("📤 إرسال مراسلة / ملف جديد")
    
    # جلب الأقسام والمستخدمين لتحديد الجهة المستقبلة
    depts = [d['name'] for d in (supabase.table("departments").select("name").execute().data or [])] or ["عام"]
    all_users = supabase.table("profiles").select("id, full_name").execute().data or []
    user_map = {u['full_name']: u['id'] for u in all_users if u['id'] != st.session_state.user['id']}

    with st.form("send_doc_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        title = c1.text_input("عنوان المراسلة*")
        ref_num = c2.text_input("الرقم المرجعي / الإشاري")
        
        target_type = c1.radio("وجهة المراسلة", ["قسم إداري", "مستخدم محدد (شخصي)"], horizontal=True)
        
        selected_dept = None
        selected_user_id = None
        selected_user_name = None
        
        if target_type == "قسم إداري":
            selected_dept = c2.selectbox("اختر القسم", depts)
        else:
            if user_map:
                selected_user_name = c2.selectbox("اختر المستلم", list(user_map.keys()))
                selected_user_id = user_map[selected_user_name]
            else:
                c2.info("لا يوجد مستخدمون آخرون حالياً.")

        up_file = st.file_uploader("رفق الملف (PDF, Word, الصور...)*")
        submit = st.form_submit_button("🚀 إرسال المراسلة فوراً", type="primary")

        if submit:
            if not title or not up_file:
                st.warning("⚠️ يرجى تعبئة العنوان وإرفاق الملف.")
            else:
                try:
                    # رفع الملف للمخزن
                    file_path = f"{st.session_state.user['id']}/{up_file.name}"
                    supabase.storage.from_("attachments").upload(file_path, up_file.getvalue())
                    file_url = supabase.storage.from_("attachments").get_public_url(file_path)

                    # إدراج البيانات
                    supabase.table("documents").insert({
                        "title": title,
                        "ref_number": ref_num,
                        "department": selected_dept,
                        "receiver_id": selected_user_id,
                        "receiver_name": selected_user_name,
                        "file_url": file_url,
                        "sender_id": st.session_state.user['id'],
                        "sender_name": st.session_state.user['full_name']
                    }).execute()
                    st.success("✅ تم إرسال المراسلة بنجاح!")
                    st.rerun()
                except Exception as err:
                    st.error(f"❌ تعذر الإرسال: {err}")

# ----------------- 5. مكون صندوق المراسلات (استقبال وعرض) -----------------
def render_inbox_and_outbox():
    tab_in, tab_out = st.tabs(["📥 الوارد (الرسائل والمرفقات المستقبلة)", "📤 الصادر (المراسلات المُرسلة)"])
    
    user_id = st.session_state.user['id']
    
    with tab_in:
        # جلب المراسلات الموجهة للمستخدم شخضياً أو للعام
        docs = supabase.table("documents").select("*").or_(f"receiver_id.eq.{user_id},receiver_id.is.null").order("id", desc=True).execute().data or []
        
        if not docs:
            st.info("لا توجد مراسلات واردة حتى الآن.")
        for doc in docs:
            dept_info = f"القسم: {doc['department']}" if doc.get('department') else "مراسلة خاصة"
            with st.expander(f"📥 {doc['title']} — (من: {doc['sender_name']}) | [{dept_info}]"):
                if doc.get('ref_number'):
                    st.write(f"**الرقم المرجعي:** {doc['ref_number']}")
                
                c_act1, c_act2 = st.columns([2, 1])
                c_act1.markdown(f"📎 **المرفق:** [تنزيل/معاينة الملف]({doc['file_url']})")
                if c_act2.button("👁️ تأكيد الاطلاع", key=f"read_{doc['id']}"):
                    supabase.table("document_reads").insert({
                        "document_id": doc['id'],
                        "user_id": user_id,
                        "user_name": st.session_state.user['full_name']
                    }).execute()
                    st.success("تم تسجيل الإطلاع.")

    with tab_out:
        out_docs = supabase.table("documents").select("*").eq("sender_id", user_id).order("id", desc=True).execute().data or []
        if not out_docs:
            st.info("لم تقم بإرسال أي مراسلات بعد.")
        for doc in out_docs:
            target = doc.get('receiver_name') or f"قسم {doc.get('department')}"
            with st.expander(f"📤 {doc['title']} — (المستلم: {target})"):
                st.write(f"**الرقم المرجعي:** {doc.get('ref_number', 'غير محدد')}")
                st.markdown(f"📎 [رابط المرفق المُرسل]({doc['file_url']})")
                
                if st.button("🗑️ طلب حذف هذه المراسلة", key=f"del_out_{doc['id']}"):
                    supabase.table("documents").update({"is_deleted_pending": True}).eq("id", doc['id']).execute()
                    st.info("تم تقديم طلب الحذف للمدير.")

# ----------------- 6. لوحة التحكم للمدير -----------------
def show_admin_dashboard():
    st.markdown("## ⚙️ لوحة قيادة مدير النظام")
    st.divider()

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📨 مركز المراسلات (إرسال واستقبال)",
        "📁 إدارة الأقسام (تعديل وحذف)", 
        "➕ إضافة مستخدم جديد", 
        "👥 إدارة الحسابات", 
        "🗑️ طلبات الحذف"
    ])

    # Tab 1: المراسلات الكاملة
    with tab1:
        render_send_document_form()
        st.divider()
        render_inbox_and_outbox()

    # Tab 2: إدارة الأقسام مع الحذف والتعديل
    with tab2:
        st.subheader("📁 إدارة الأقسام الهيكلية")
        
        # إضافة قسم
        c_add1, c_add2 = st.columns([3, 1])
        new_d_name = c_add1.text_input("اسم القسم الجديد", placeholder="أدخل اسم القسم الجديد...", label_visibility="collapsed")
        if c_add2.button("➕ إضافة قسم", type="primary"):
            if new_d_name:
                try:
                    supabase.table("departments").insert({"name": new_d_name}).execute()
                    st.success("تمت إضافة القسم.")
                    st.rerun()
                except Exception as e:
                    st.error("القسم موجود مسبقاً أو حدث خطأ.")

        st.divider()
        st.subheader("قائمة الأقسام المسجلة (يمكنك التعديل أو الحذف)")
        
        depts = supabase.table("departments").select("*").order("id").execute().data or []
        for d in depts:
            col_id, col_name, col_edit, col_del = st.columns([1, 4, 2, 2])
            col_id.write(f"#{d['id']}")
            
            # حقل تعديل الاسم
            edited_name = col_name.text_input("الاسم", value=d['name'], key=f"dept_input_{d['id']}", label_visibility="collapsed")
            
            if col_edit.button("💾 حفظ", key=f"save_d_{d['id']}"):
                if edited_name != d['name']:
                    supabase.table("departments").update({"name": edited_name}).eq("id", d['id']).execute()
                    st.success("تم التعديل")
                    st.rerun()
                    
            if col_del.button("❌ حذف", key=f"del_d_{d['id']}"):
                supabase.table("departments").delete().eq("id", d['id']).execute()
                st.warning("تم حذف القسم")
                st.rerun()

    # Tab 3: إضافة مستخدم
    with tab3:
        st.subheader("➕ إنشاء حساب مستخدم جديد")
        with st.form("create_user_form", clear_on_submit=True):
            col_a, col_b = st.columns(2)
            new_email = col_a.text_input("البريد الإلكتروني*")
            new_pass = col_b.text_input("كلمة المرور*", type="password")
            new_name = col_a.text_input("الاسم الكامل*")
            new_role = col_b.selectbox("الصلاحية", ["user", "admin"], format_func=lambda x: "أستاذ / مستخدم" if x=="user" else "مدير نظام")
            
            # كود إنشاء الحساب المحدث
if st.form_submit_button("✨ إنشاء الحساب الآن", type="primary"):
    if new_email and new_pass and new_name:
        try:
            # 1. إنشاء الحساب في Supabase Auth
            auth_res = supabase.auth.sign_up({"email": new_email, "password": new_pass})
            
            if auth_res.user:
                # 2. إضافة بيانات البروفايل
                supabase.table("profiles").insert({
                    "id": auth_res.user.id,
                    "full_name": new_name,
                    "role": new_role,
                    "is_active": True
                }).execute()
                
                st.success(f"✅ تم إنشاء حساب {new_name} بنجاح!")
                st.rerun()
        except Exception as err:
            if "violates row-level security" in str(err):
                st.error("❌ يجب إلغاء سياسة RLS من SQL Editor في Supabase أولاً.")
            else:
                st.error(f"❌ خطأ أثناء الإضافة: {err}")

    # Tab 4: إدارة الحسابات
    with tab4:
        st.subheader("👥 القائمة الكاملة للمستخدمين")
        users_list = supabase.table("profiles").select("*").execute().data or []
        for u in users_list:
            c1, c2, c3, c4 = st.columns([3, 2, 2, 2])
            c1.write(f"👤 **{u.get('full_name')}**")
            current_role = u.get('role', 'user')
            updated_role = c2.selectbox("الصلاحية", ["user", "admin"], index=0 if current_role=='user' else 1, key=f"r_{u['id']}", label_visibility="collapsed")
            is_act = c3.checkbox("حساب نشط", value=u.get('is_active', True), key=f"a_{u['id']}")
            if c4.button("💾 حفظ", key=f"btn_u_{u['id']}"):
                supabase.table("profiles").update({"role": updated_role, "is_active": is_act}).eq("id", u['id']).execute()
                st.success("تم التحديث")
                st.rerun()

    # Tab 5: طلبات الحذف
    with tab5:
        st.subheader("🗑️ طلبات الحذف المعلقة")
        pending_docs = supabase.table("documents").select("*").eq("is_deleted_pending", True).execute().data or []
        if not pending_docs:
            st.info("لا توجد طلبات حذف حالياً.")
        for d in pending_docs:
            col_x, col_y, col_z = st.columns([3, 1, 1])
            col_x.write(f"📄 **{d.get('title')}** (المرسل: {d.get('sender_name')})")
            if col_y.button("✅ موافقة بالحذف", key=f"confirm_{d['id']}"):
                supabase.table("documents").delete().eq("id", d['id']).execute()
                st.rerun()
            if col_z.button("❌ رفض", key=f"reject_{d['id']}"):
                supabase.table("documents").update({"is_deleted_pending": False}).eq("id", d['id']).execute()
                st.rerun()

# ----------------- 7. واجهة المستخدمين / الأساتذة -----------------
def show_user_workspace():
    st.markdown(f"## 🖐️ أهلاً بك، {st.session_state.user.get('full_name')}")
    st.divider()

    tab_send, tab_inbox = st.tabs(["📤 إرسال مراسلة ومرفق", "📬 صندوق الرسائل والمرفقات"])
    
    with tab_send:
        render_send_document_form()
        
    with tab_inbox:
        render_inbox_and_outbox()

# ----------------- 8. التحكم بالتنقل -----------------
if st.session_state.user is None:
    show_login()
else:
    st.sidebar.markdown(f"### 👤 {st.session_state.user.get('full_name')}")
    st.sidebar.caption(f"الصلاحية: {'مدير نظام' if st.session_state.user.get('role') == 'admin' else 'أستاذ / مستخدم'}")
    st.sidebar.divider()
    
    if st.sidebar.button("🚪 تسجيل الخروج"):
        st.session_state.user = None
        st.rerun()

    if st.session_state.user.get('role') == 'admin':
        show_admin_dashboard()
    else:
        show_user_workspace()
