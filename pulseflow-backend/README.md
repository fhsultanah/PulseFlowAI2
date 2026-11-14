# PulseFlow AI — Backend (نموذج أولي)

بيانات اصطناعية فقط. لا تُدخلوا بيانات مرضى حقيقية.

## التشغيل
```bash
pip install -r requirements.txt
uvicorn app.main:app --reload        # التوثيق التفاعلي: http://localhost:8000/docs
python -m unittest discover -s tests # اختبارات الخدمات
```
مع n8n: `cp .env.example .env` ثم `docker compose up --build` (n8n على http://localhost:5678).

## عقد الـ API (الكل يبني عليه)
| Endpoint | الوصف |
|---|---|
| `GET /forecast?hours=12` | التنبؤ بالوافدين لكل ساعة (expected / lower / upper) |
| `POST /simulate` | ماذا لو: حالات CTAS + `extra_patients` + الموارد المتاحة ← المطلوب والفجوات والخطورة |
| `POST /scribe` | نص محادثة ← SOAP + اقتراحات ICD-10 + نواقص التوثيق |
| `POST /alerts/check` | يقيّم التنبؤ، وإذا تجاوز الحد ينشئ تنبيهاً ويرسله لـ n8n |
| `GET /alerts` | قائمة التنبيهات للوحة |
| `POST /alerts/{id}/status` | n8n يستدعيه بعد الإرسال (يحتاج `X-API-Key` إذا حُدد `API_KEY`) |

كل الأشكال معرّفة في `app/schemas.py`. حالياً كل شي يشتغل بنسخة mock.

## ربط شغل البنات
- **جوري:** أنشئي `app/ml/forecast_model.py` فيه `predict(hours)` يرجع نفس الشكل (time, expected, lower, upper).
- **سلطانة:** أنشئي `app/ml/scribe_model.py` فيه `generate(transcript)` يرجع `soap` و`icd10` و`gaps` بنفس شكل الـ mock.
- كل وحدة تفعّل نموذجها لحالها: `FORECAST_MOCK=0` لجوري، `SCRIBE_MOCK=0` لسلطانة. الواجهة (ريماس) ما تتغير.
- ريماس تبني على `/docs` من الآن، والـ CORS مفتوح.

## n8n (workflowين فقط)
المسارات يستدعيها الباك إند: `{N8N_WEBHOOK_BASE}/surge` و `{N8N_WEBHOOK_BASE}/doc-gap`.
1. **Surge:** Webhook (POST, path `surge`) ← عقدة إشعار (Email/Telegram/Slack) ← HTTP Request `POST http://api:8000/alerts/{{$json.body.id}}/status` بجسم `{"status":"notified"}` وترويسة `X-API-Key`.
2. **Doc gap:** نفس البنية بمسار `doc-gap`.
3. اختياري: Schedule Trigger كل 15 دقيقة ← `POST http://api:8000/alerts/check`.
- للتجربة استخدموا عنوان `webhook-test`، وللتشغيل الفعلي فعّلوا الـ workflow (عنوان `webhook`).
- شغّلوا n8n على جهازكم (self-hosted) ولا ترسلون بيانات لخدمات خارجية.

## ما هو حقيقي وما هو افتراض (مهم للعرض)
- `simulate.py`: أوزان CTAS ونسب الطاقم **افتراضات مؤقتة غير مُتحقق منها سريرياً**. راجعوها مع ساره وضعوا مصدراً قبل عرضها.
- `scribe.py` (mock): مطابقة كلمات فقط، وليس نموذجاً. الثقة 0.5 ثابتة.
- `forecast.py` (mock): نمط يومي اصطناعي.
- النصوص المُدخلة للـ Scribe لا تُخزَّن، وتُخزَّن التنبيهات فقط.
