from sqlalchemy.orm import Session
from app.core.models import (
    User, Document, Approval, Workflow, Project, Vendor,
    Customer, KnowledgeArticle, Notification, AuditLog,
    UserRole, DocumentStatus, ApprovalStatus, WorkflowStatus
)
from app.core.security import get_password_hash
from datetime import datetime, timedelta
import json


def seed_database(db: Session):
    if db.query(User).count() > 0:
        return

    users = [
        User(name="أحمد الراشدي", email="admin@dociq.io", hashed_password=get_password_hash("admin123"),
             role=UserRole.SUPER_ADMIN, department="الإدارة العليا", language="ar", theme="light"),
        User(name="سارة المنصوري", email="manager@dociq.io", hashed_password=get_password_hash("manager123"),
             role=UserRole.MANAGER, department="إدارة المستندات", language="ar", theme="light"),
        User(name="محمد العبدالله", email="reviewer@dociq.io", hashed_password=get_password_hash("reviewer123"),
             role=UserRole.REVIEWER, department="المراجعة والتدقيق", language="ar", theme="dark"),
        User(name="فاطمة الزهراني", email="viewer@dociq.io", hashed_password=get_password_hash("viewer123"),
             role=UserRole.VIEWER, department="الموارد البشرية", language="ar", theme="light"),
        User(name="خالد البكري", email="khalid@dociq.io", hashed_password=get_password_hash("khalid123"),
             role=UserRole.MANAGER, department="المشاريع", language="ar", theme="light"),
    ]
    for u in users:
        db.add(u)
    db.flush()

    projects = [
        Project(name="مشروع الجسر الكبير", description="إنشاء جسر فوق وادي الدواسر", status="active",
                progress=65, client="وزارة النقل", budget=45000000, manager_id=users[1].id,
                start_date=datetime.now() - timedelta(days=120), end_date=datetime.now() + timedelta(days=180)),
        Project(name="برج الأعمال المركزي", description="مجمع أعمال تجاري في وسط المدينة", status="active",
                progress=32, client="مجموعة الرياض للتطوير", budget=120000000, manager_id=users[4].id,
                start_date=datetime.now() - timedelta(days=60), end_date=datetime.now() + timedelta(days=365)),
        Project(name="مستودعات لوجستية - الدمام", description="إنشاء مجمع مستودعات لوجستية", status="completed",
                progress=100, client="شركة الشحن السريع", budget=18000000, manager_id=users[1].id,
                start_date=datetime.now() - timedelta(days=365), end_date=datetime.now() - timedelta(days=30)),
        Project(name="منظومة الطاقة الشمسية", description="تركيب منظومة طاقة شمسية", status="on_hold",
                progress=15, client="شركة الكهرباء الوطنية", budget=8000000, manager_id=users[4].id,
                start_date=datetime.now() - timedelta(days=30), end_date=datetime.now() + timedelta(days=270)),
    ]
    for p in projects:
        db.add(p)
    db.flush()

    vendors = [
        Vendor(name="مجموعة الإنشاءات المتحدة", code="VND-001", category="إنشاءات", contact_name="عمر السالم",
               email="info@ucg.sa", phone="+966501234567", country="المملكة العربية السعودية", city="الرياض",
               status="active", rating=4.8, contract_count=12),
        Vendor(name="شركة التقنية المتقدمة", code="VND-002", category="تقنية المعلومات", contact_name="نورة الحربي",
               email="tech@advanced.sa", phone="+966507654321", country="المملكة العربية السعودية", city="جدة",
               status="active", rating=4.5, contract_count=8),
        Vendor(name="مؤسسة الخدمات اللوجستية", code="VND-003", category="لوجستيات", contact_name="فهد العتيبي",
               email="ops@logistic.sa", phone="+966509876543", country="المملكة العربية السعودية", city="الدمام",
               status="active", rating=4.2, contract_count=25),
        Vendor(name="شركة الاستشارات المالية", code="VND-004", category="استشارات مالية", contact_name="ريم الدوسري",
               email="finance@consult.sa", phone="+966503216789", country="المملكة العربية السعودية", city="الرياض",
               status="inactive", rating=3.9, contract_count=5),
    ]
    for v in vendors:
        db.add(v)
    db.flush()

    customers = [
        Customer(name="علي المحمدي", company="وزارة النقل", email="ali@mot.gov.sa", phone="+966501111111",
                 country="المملكة العربية السعودية", sector="حكومي", status="active",
                 contract_value=45000000, document_count=47),
        Customer(name="نواف السعيد", company="مجموعة الرياض للتطوير", email="nawaf@rdc.sa",
                 phone="+966502222222", country="المملكة العربية السعودية", sector="عقارات",
                 status="active", contract_value=120000000, document_count=82),
        Customer(name="هند العمري", company="شركة الشحن السريع", email="hind@fast.sa",
                 phone="+966503333333", country="المملكة العربية السعودية", sector="لوجستيات",
                 status="active", contract_value=18000000, document_count=33),
        Customer(name="سلطان الغامدي", company="شركة الكهرباء الوطنية", email="sultan@sec.sa",
                 phone="+966504444444", country="المملكة العربية السعودية", sector="طاقة",
                 status="on_hold", contract_value=8000000, document_count=19),
    ]
    for c in customers:
        db.add(c)
    db.flush()

    docs_data = [
        ("عقد إنشاء الجسر - المرحلة الأولى", "contract_bridge_phase1.pdf", "PDF", DocumentStatus.APPROVED, "عقود", 97.5, projects[0].id),
        ("مخططات هندسية - برج الأعمال", "engineering_tower.pdf", "PDF", DocumentStatus.PENDING_APPROVAL, "مخططات", 89.2, projects[1].id),
        ("فاتورة موردين - مجموعة الإنشاءات", "invoice_ucg_2024.pdf", "PDF", DocumentStatus.REVIEWED, "فواتير", 95.1, projects[0].id),
        ("تقرير سلامة - مستودعات الدمام", "safety_report_dammam.pdf", "PDF", DocumentStatus.APPROVED, "تقارير", 91.8, projects[2].id),
        ("عرض أسعار - منظومة الطاقة الشمسية", "quotation_solar.pdf", "PDF", DocumentStatus.PROCESSING, "عروض أسعار", 78.3, projects[3].id),
        ("محضر اجتماع - مجلس الإدارة", "board_meeting_minutes.docx", "DOCX", DocumentStatus.APPROVED, "محاضر", 99.0, None),
        ("سياسة الموارد البشرية المحدثة", "hr_policy_2024.pdf", "PDF", DocumentStatus.REVIEWED, "سياسات", 96.4, None),
        ("تقرير مالي - الربع الثالث", "financial_q3_2024.xlsx", "XLSX", DocumentStatus.PENDING_APPROVAL, "تقارير مالية", 88.7, None),
        ("مواصفات فنية - مشروع الجسر", "technical_specs_bridge.pdf", "PDF", DocumentStatus.APPROVED, "مواصفات فنية", 93.2, projects[0].id),
        ("عقد خدمات - شركة التقنية", "service_contract_tech.pdf", "PDF", DocumentStatus.UPLOADED, "عقود", 0.0, None),
    ]

    documents = []
    for i, (title, fname, ftype, status, cat, conf, proj_id) in enumerate(docs_data):
        d = Document(
            title=title, file_name=fname, file_type=ftype,
            file_size=1024 * (100 + i * 50), file_path=f"/uploads/{fname}",
            status=status, category=cat, confidence_score=conf,
            uploader_id=users[i % 3].id, project_id=proj_id,
            page_count=i + 1,
            summary=f"ملخص تلقائي للمستند: {title}",
            extracted_data={"vendor": "مجموعة الإنشاءات المتحدة", "amount": f"{(i+1)*50000}", "date": "2024-01-15"},
            created_at=datetime.now() - timedelta(days=i * 5)
        )
        db.add(d)
        documents.append(d)
    db.flush()

    pending_docs = [d for d in documents if d.status in [DocumentStatus.PENDING_APPROVAL, DocumentStatus.REVIEWED]]
    for doc in pending_docs:
        a = Approval(document_id=doc.id, approver_id=users[1].id, status=ApprovalStatus.PENDING,
                     due_date=datetime.now() + timedelta(days=3), priority="high")
        db.add(a)

    workflows = [
        Workflow(name="مسار اعتماد العقود", description="مسار تلقائي لاعتماد العقود متعددة المراحل",
                 status=WorkflowStatus.ACTIVE, trigger_type="document_upload", category="عقود",
                 run_count=47, created_by=users[0].id,
                 nodes=[
                     {"id": "1", "type": "trigger", "label": "رفع المستند", "x": 100, "y": 200},
                     {"id": "2", "type": "ai_review", "label": "مراجعة AI", "x": 300, "y": 200},
                     {"id": "3", "type": "approval", "label": "اعتماد المدير", "x": 500, "y": 200},
                     {"id": "4", "type": "notification", "label": "إشعار", "x": 700, "y": 200},
                 ],
                 edges=[{"from": "1", "to": "2"}, {"from": "2", "to": "3"}, {"from": "3", "to": "4"}]),
        Workflow(name="مسار معالجة الفواتير", description="استخراج وتحقق وتخزين بيانات الفواتير تلقائياً",
                 status=WorkflowStatus.ACTIVE, trigger_type="document_upload", category="فواتير",
                 run_count=156, created_by=users[1].id,
                 nodes=[
                     {"id": "1", "type": "trigger", "label": "رفع فاتورة", "x": 100, "y": 200},
                     {"id": "2", "type": "ocr", "label": "استخراج OCR", "x": 300, "y": 200},
                     {"id": "3", "type": "condition", "label": "مبلغ > 50,000؟", "x": 500, "y": 200},
                     {"id": "4", "type": "approval", "label": "اعتماد مزدوج", "x": 700, "y": 150},
                     {"id": "5", "type": "action", "label": "حفظ مباشر", "x": 700, "y": 250},
                 ],
                 edges=[{"from": "1", "to": "2"}, {"from": "2", "to": "3"},
                        {"from": "3", "to": "4", "label": "نعم"}, {"from": "3", "to": "5", "label": "لا"}]),
        Workflow(name="مسار التقارير الدورية", description="إنشاء وإرسال التقارير الأسبوعية تلقائياً",
                 status=WorkflowStatus.DRAFT, trigger_type="schedule", category="تقارير",
                 run_count=0, created_by=users[0].id, nodes=[], edges=[]),
    ]
    for w in workflows:
        db.add(w)

    articles = [
        KnowledgeArticle(title="دليل رفع المستندات", content="شرح تفصيلي لكيفية رفع المستندات وتصنيفها في المنصة...",
                         collection="دليل المستخدم", tags=["رفع", "مستندات", "تصنيف"], author_id=users[0].id, view_count=234),
        KnowledgeArticle(title="سياسة اعتماد العقود", content="الإجراءات الرسمية المعتمدة لدورة اعتماد العقود...",
                         collection="السياسات والإجراءات", tags=["عقود", "اعتماد", "مسار عمل"], author_id=users[1].id, view_count=189),
        KnowledgeArticle(title="معايير تصنيف الفواتير", content="معايير واضحة لتصنيف أنواع الفواتير وترميزها...",
                         collection="معايير مالية", tags=["فواتير", "تصنيف", "محاسبة"], author_id=users[0].id, view_count=142),
        KnowledgeArticle(title="إجراءات الأرشفة الإلكترونية", content="خطوات الأرشفة الرقمية وفق المعايير المؤسسية...",
                         collection="دليل المستخدم", tags=["أرشفة", "رقمنة", "حفظ"], author_id=users[2].id, view_count=98),
    ]
    for art in articles:
        db.add(art)

    notif_data = [
        (users[0].id, "طلب اعتماد جديد", "يتطلب عقد الجسر موافقتكم", "warning", "/approvals"),
        (users[0].id, "تمت معالجة المستند", "تم استخراج بيانات الفاتورة بنجاح", "success", "/documents/3"),
        (users[0].id, "تنبيه SLA", "اقتربت مهلة اعتماد التقرير المالي", "danger", "/approvals"),
        (users[0].id, "تحديث النظام", "تم تحديث وحدة البحث الذكي", "info", "/settings"),
        (users[0].id, "مستخدم جديد", "انضم فريد الأنصاري إلى المنصة", "info", "/users"),
    ]
    for uid, title, msg, typ, url in notif_data:
        n = Notification(user_id=uid, title=title, message=msg, type=typ, action_url=url)
        db.add(n)

    audit_actions = [
        (users[0].id, "LOGIN", "session", "1", None, {"ip": "192.168.1.1"}),
        (users[0].id, "UPLOAD_DOCUMENT", "document", "1", None, {"title": "عقد إنشاء الجسر"}),
        (users[1].id, "APPROVE_DOCUMENT", "document", "1", {"status": "pending"}, {"status": "approved"}),
        (users[2].id, "VIEW_DOCUMENT", "document", "3", None, None),
        (users[0].id, "CREATE_WORKFLOW", "workflow", "1", None, {"name": "مسار اعتماد العقود"}),
        (users[1].id, "UPDATE_USER", "user", "4", {"role": "viewer"}, {"role": "reviewer"}),
    ]
    for uid, action, rtype, rid, before, after in audit_actions:
        al = AuditLog(user_id=uid, action=action, resource_type=rtype, resource_id=rid,
                      before_data=before, after_data=after, ip_address="192.168.1.100",
                      created_at=datetime.now() - timedelta(hours=len(audit_actions)))
        db.add(al)

    db.commit()
