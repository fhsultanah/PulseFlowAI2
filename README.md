<div dir="rtl">

# PulseFlow AI

مساعد ذكي يساعد الطوارئ تتجهّز للزحام قبل ما يصير، ويوفّر على الطبيب وقت كتابة الملاحظات.

مشروع فريق **Synapse** في هاكاثون MEDATHON ضمن المنتدى السعودي للشباب للرعاية الصحية (SYHF)، المسار الأول: إدارة الازدحام وتدفق المرضى.

## وش المشكلة؟

الطوارئ ممكن تمتلئ فجأة، والطاقم غالبًا يعرف إن فيه ضغط بعد ما يبدأ. وبنفس الوقت، الطبيب يقضي جزء كبير من وقته في الكتابة والتوثيق بدل ما يكون مع المريض. والنتيجة تأخير في الرعاية، وأحيانًا ملفات ناقصة.

## وش فكرتنا؟

المشروع فيه جزئين يكمّلون بعض، وتجمعهم لوحة تحكم واحدة:

**١. توقّع الازدحام**
نتوقع كم مريض بيوصل كل ساعة، وننبّه قبل ما نوصل للحد الخطر. وفيه خاصية "ماذا لو": تحرّك الشريط وتزيد عدد المرضى، فيطلع لك كم سرير وممرض وطبيب تحتاجون حسب درجة استعجال الحالات (CTAS)، مع توصيات بالعربي والإنجليزي.

**٢. المساعد الكاتب (Scribe)**
تسجّل كلام الزيارة بالمايك أو تكتب النص، ويطلع لك ملاحظة SOAP، وأكواد ICD-10 مقترحة، وتنبيه على الناقص في التوثيق مثل الحساسية والأدوية والعلامات الحيوية والخطة. نستخدم Whisper لتحويل الصوت (يدعم العربي) ونموذج لغوي عبر Groq لكتابة الملاحظة. والطبيب هو اللي يراجع ويعتمد، المساعد ما يقرر شي.

**اللوحة:** أربع شاشات (مركز القيادة، توقع تدفق المرضى، تخطيط الموارد، الـ Scribe)، مع وضع فاتح وداكن ودخول تجريبي.

## وين وصلنا؟ 

- اللوحة والـ API شغّالين، والبيانات كلها اصطناعية.
- التنبؤ حاليًا نمط يومي اصطناعي، وما فيه نموذج مدرَّب بعد.
- الـ Scribe له وضعين. الافتراضي تجريبي (مطابقة كلمات). والحقيقي (Whisper مع نموذج لغوي عبر Groq) مكتوب في الكود ويحتاج مفتاح `GROQ_API_KEY`. ما قسنا دقته بعد.
- أوزان CTAS ونسب الطاقم افتراضات مؤقتة، وساره تراجعها سريريًا.
- ما قسنا دقة أي شي على بيانات حقيقية، فما نذكر أي أرقام دقة.
- في الوضع الحقيقي الصوت والنص يروحون لخدمة خارجية (Groq). لا تدخلون بيانات مرضى حقيقية أبدًا.

## كيف تشغّله؟

- **الواجهة:** افتح `frontend/index.html` في المتصفح. تشتغل ببيانات تجريبية بدون تثبيت. بيانات الدخول في ملف العرض.
- **الباك إند** (من المجلد اللي فيه `app`):

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
python -m unittest discover -s tests
```

- **الـ Scribe الحقيقي والمايك:** شغّلوا بـ `SCRIBE_MOCK=0` مع `GROQ_API_KEY`. المفتاح يكون في `.env` أو متغير بيئة، ولا ينكتب في الكود أبدًا لأن المستودع عام.
- **ربط الواجهة بالباك إند:** حطّوا عنوانه في `API_BASE` داخل `frontend/index.html`. التوثيق التفاعلي على `http://localhost:8000/docs`.

## الفريق

- **وجد**: قائدة الفريق، الباك إند والربط والنشر
- **جوري**: التنبؤ ومحاكاة توزيع الأسرّة والطاقم
- **سلطانة**: توثيق الذكاء الاصطناعي (الصوت لنص، ملاحظة SOAP، أكواد ICD-10)
- **ريماس**: الواجهة وتصميم لوحة التحكم
- **ساره**: المستشارة السريرية، تراجع CTAS وأكواد ICD-10 وقواعد التوثيق

</div>

---

# PulseFlow AI (English)

A smart assistant that helps emergency departments get ready for a rush before it happens, and gives doctors time back from paperwork.

Built by Team **Synapse** for MEDATHON at the Saudi Youth Healthcare Forum (SYHF), Track 1: Healthcare Crowd & Patient Flow Management.

## The problem

An emergency department can fill up fast, and staff usually find out about the pressure once it has already started. At the same time, doctors spend a big part of their shift typing notes instead of being with the patient. That means slower care and sometimes incomplete records.

## Our idea

Two parts that work together, in one dashboard:

**1. Crowd forecasting**
We estimate how many patients will arrive each hour and warn the team before arrivals hit a risky level. There is also a "what if" tool: add extra patients with a slider and it shows how many beds, nurses and physicians you would need based on how urgent the cases are (CTAS), with recommendations in Arabic and English.

**2. The Scribe**
Record the visit with the mic, or type the text. You get a SOAP note, suggested ICD-10 codes, and a flag for anything missing from the documentation, like allergies, medications, vital signs or the plan. We use Whisper for speech-to-text (it handles Arabic) and a language model through Groq to write the note. The doctor always reviews and approves. The assistant doesn't make decisions.

**The dashboard:** four screens (command center, patient flow forecast, resource planning, Scribe), with light and dark modes and a demo login.

## Where we are, honestly

- The dashboard and the API both run, and all data is synthetic.
- The forecast is currently an artificial daily pattern. There is no trained model yet.
- The Scribe has two modes. The default is a demo mode (keyword matching). The real one (Whisper plus a language model through Groq) is written in the code and needs a `GROQ_API_KEY`. We haven't measured its accuracy yet.
- The CTAS weights and staffing ratios are temporary assumptions, and Sarah is reviewing them clinically.
- We haven't measured accuracy on real data, so we don't quote any accuracy numbers.
- In real mode, audio and text are sent to an external service (Groq). Please never enter real patient data.

## How to run it

- **Dashboard:** open `frontend/index.html` in your browser. It runs on demo data with nothing to install. The login details are in our presentation file.
- **Backend** (from the folder that contains `app`):

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
python -m unittest discover -s tests
```

- **Real Scribe and the mic:** start with `SCRIBE_MOCK=0` and a `GROQ_API_KEY`. Keep the key in `.env` or an environment variable, never in the code, because the repository is public.
- **Connect the dashboard to the backend:** put its address in `API_BASE` inside `frontend/index.html`. Interactive docs are at `http://localhost:8000/docs`.

## The team

- **Wajd Alhothaly**: IT, team leader. Backend, integration and deployment.
- **Jory Alzahrani**: CS, ML specialist. Forecasting and bed and staff simulation.
- **Sultana Alhomaiyani**: CS, AI and NLP developer. Speech-to-text and automated clinical documentation.
- **Rimas Althopity**: CS, UI/UX and front-end. Dashboard and design.
- **Sarah Alghamdi**: Pharmacy, clinical advisor. Reviews CTAS logic, ICD-10 codes and documentation rules.
