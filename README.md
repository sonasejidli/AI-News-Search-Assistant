AI Xəbər Axtarış Assistenti
Neurotime hackathon tapşırığı üçün AI əsaslı xəbər axtarış sistemi.
✨ Xüsusiyyətlər

✅ Təbii dildə axtarış — OpenAI yerləşdirmə + ChromaDB semantik axtarışı
✅ Tarix / tarix aralığının filtrlənməsi — ChromaDB metaməlumatları where-clause (filtrdən sonra yox)
✅ Metadata-aware axtarış — əlavə, mənbə üzrə filtr
✅ Keyword & entity extraction — Azərbaycan stopwords ilə təmiz keyfiyyətlər
✅ Telegram botu — təbii dil interaksiyası + inline düymələr
✅ Streamlit veb interfeysi — bonus xüsusiyyət

📁 Layihə strukturu
news_assistant/
├── .env.example          # API key şablonu
├── .gitignore            
├── requirements.txt
├── README.md
├── config.py             # Mərkəzi konfiq
├── az_stopwords.py       # Azərbaycan dili stopwords
├── ingest.py             # CSV → embedding → ChromaDB
├── query_parser.py       # Natural language → structured query
├── search.py             # Semantic search + metadata filter
├── keywords.py           # Keyword/entity extraction (5.4 tələbi)
├── bot.py                # Telegram bot
├── app.py                # Streamlit web interface
└── check_setup.py        # Setup yoxlama skripti
🚀 Quraşdırma
1. Paketləri qurur
başpip install -r requirements.txt
2. .envfaylı yarat
ÇOX VACİB : VS Code-da əl ilə yarat, terminaldan istifadə etmə.
VS Code-da File Explorer-də sağ vurun → Yeni Fayl → reklam:.env
İçinə dəqiq belə yaz (hər biri ayrı sətirdə):
OPENAI_API_KEY=sk-proj-sənin-key-in
TELEGRAM_BOT_TOKEN=botfather-dan-aldığın-token
CSV_PATH=news_data.csv
⚠️ Diqqət:

Fayl adı dəqiq .env( env.txtYOX, .env.txtYOX)
=dövründə BOŞLUQ yoxdur
DIRNAQ yoxdur

3. Dataset-i layihə qovluğuna at
CSV faylı layihə qovluğunda olmalıdır. Adı .env-də CSV_PATH-ə uyğun olmalıdır.
4. Setup-ı yoxla
başpython check_setup.py
Hər şey yaşıl olmalıdır. Xəta varsa, çıxış sənə nə etməli olduğunu deyəcək.
📊 İstifadə
Addım 1: Embedding yarat (yalnız bir dəfə)
başpython ingest.py
~5-10 dəqiqə çəkir 20K məqalə üçün. Ortada dayansa, yenidən işə sal — qaldığı yerdən davam edəcək.
Addım 2: Telegram botu işə sal
başpython bot.py
Sonra Telegram-da botuna mesaj yaz:

"AccessBank haqqında xəbər tap"
"20 may SOCAR-la bağlı nə var?"
“18-21 may arası gömrük xəbərləri”
"Bank xəbərlərində ən çox keçən sözlər"

Addım 3 (bonus): Web frontend
başstreamlit run app.py
Brauzer http://localhost:8501ünvanında açılacaq.
🔍 Texniki detallar
Relevance ball necə hesablanır?
ChromaDB kosinus məsafəsi qaytarır (0 = eyni, 2 = fərqli fərqli). Biz score = 1 - distanceformuluyla 0-1 aralığında uyğunluq skoru hesablayırıq. 1.0 = uyğunluq, 0.5 = orta uyğunluq.
Date filter necə işləyir?
ChromaDB-nin wherebənd-i ilə axtarış zamanı filter olunur, post-filter deyil:
pitonwhere = {"$and": [
    {"published_at": {"$gte": "2025-05-18"}},
    {"published_at": {"$lte": "2025-05-21"}}
]}
Bu o deməkdir ki, top-N nəticələri artıq filtrlənmişdir — naive post-filter yanaşmasındakı kimi keyfiyyət itmir.
Açar söz çıxarılması necə işləyir?
İki paralel pipeline:

Tək sözlər : kiçik hərf, 4+ simvol, Azərbaycan stopwords çıxarılır
Entity-lər : böyük hərflə başlayan 1-4 sözlü ifadələr (təşkilat, şəxs, yer adları)

Hər ikisi Counterilə seçilir və top-N qaytarılır.
Sorğu təhlili necə işləyir?
gpt-4o-miniistifadə olunur (ucuz və sürətli). Strukturlaşdırılmış çıxış rejimi ( response_format={"type": "json_object"}) zəmanət verir ki, JSON parse olunan formada gəlsin. Bugünkü tarix kontekst kimi verilir.
🐛 Xətaları həll etmək
XətaHəllOPENAI_API_KEY tapılmadı.envfaylının adını və daxilini yoxlaCSV tapılmadı.env-də CSV_PATH-i düzəltCollection boşdurpython ingest.pyişə salRate limitBATCH_SIZE-i config.py-da azaltMarkdown parse errorBot artıq HTML rejimi istifadə edir
📝 5.4 — Açar sözün çıxarılması tələbi
Bu tələb iki yerdə edilib:

Qlobal — keywords.pymodul bütün verilənlər toplusu işləyə bilər
Search-result — hər axtarışdan sonra bot frontend nəticədə açar söz/ göstərir

İki kateqoriyaya qaytarılır:

Müəssisə-lər : təşkilat, şəxs, brend adları (məs. "AccessBank", "SOCAR", "Mərkəzi Bank")
Açar söz-lər : ümumi tez-tez keçən sözlər (məs. "kredit", "vergi", "bazar")
