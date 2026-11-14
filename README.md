# PulseFlow Backend

مشروع **PulseFlow** هو نظام خلفية برمجية (Backend) مبني باستخدام **FastAPI**، مخصص لدعم خدمات الطوارئ الطبية والتنبؤ بالازدحام (Surge forecasting)، تحويل النصوص الطبية إلى ملاحظات SOAP واقتراح رموز التشخيص الدولية (ICD-10)، وإجراء محاكاة لإدارة الموارد والطاقة الاستيعابية[span_0](start_span)[span_0](end_span)[span_1](start_span)[span_1](end_span)[span_2](start_span)[span_2](end_span)[span_3](start_span)[span_3](end_span)[span_4](start_span)[span_4](end_span)[span_5](start_span)[span_5](end_span).

---

## التقنيات المستخدمة (Tech Stack)
* **Python 3.12+**[span_6](start_span)[span_6](end_span)
* **FastAPI** (إطار عمل الـ API)[span_7](start_span)[span_7](end_span)[span_8](start_span)[span_8](end_span)
* **Pydantic v2** (للتحقق من البيانات والـ Schemas)[span_9](start_span)[span_9](end_span)[span_10](start_span)[span_10](end_span)
* **SQLite** (قاعدة بيانات خفيفة لتخزين التنبيهات والحالة)[span_11](start_span)[span_11](end_span)
* **Groq SDK / Llama 3** (للذكاء الاصطناعي وتحليل النصوص الطبية)[span_12](start_span)[span_12](end_span)
* **Docker & Docker Compose** (للحاويات والتشغيل السريع)[span_13](start_span)[span_13](end_span)[span_14](start_span)[span_14](end_span)

---

## هيكلية المشروع (Project Structure)
```text
pulseflow-backend/
│
├── app/
│   ├── ml/                # نماذج الذكاء الاصطناعي ومعالجة النصوص (مثل scribe_model.py)
│   ├── services/          # خدمات النظام (alerts, forecast, scribe, simulate)
│   ├── config.py          # إعدادات النظام وقراءة المتغيرات البيئية
│   ├── db.py              # إدارة قاعدة بيانات SQLite والتنبيهات
│   ├── main.py            # نقطة البداية لتطبيق FastAPI ونقاط النهاية (Endpoints)
│   └── schemas.py         # نماذج Pydantic للتحقق من البيانات (API Contracts)
│
├── tests/                 # اختبارات النظام (Unit Tests)
├── Dockerfile             # ملف بناء حاوية Docker للتطبيق
├── docker-compose.yml     # ملف التشغيل المشترك (يتضمن FastAPI و n8n)
├── requirements.txt       # مكتبات بايثون المطلوبة
└── .env.example           # مثال لملف الإعدادات والبيانات البيئية
