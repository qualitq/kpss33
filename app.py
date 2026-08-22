import os
import json
import tempfile
import requests
from flask import Flask, render_template, jsonify, request

app = Flask(__name__)

# OpenRouter API Key
API_KEY = os.environ.get(
    "GEMINI_API_KEY", 
    "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"
).strip()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BANK_FILE = os.path.join(BASE_DIR, "questions_bank.json")
CACHE_FILE = os.path.join(BASE_DIR, "kpss_database.json")

# Tüm 500/404 hatalarını zorunlu olarak JSON'a çevirir (HTML dönüşünü engeller)
@app.errorhandler(Exception)
def handle_exception(e):
    return jsonify({"success": False, "error": str(e)}), 200

def call_gemini(prompt: str) -> str:
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://kpss33.onrender.com",
        "X-Title": "KPSS Master Akademi"
    }

    models_to_try = [
        "meta-llama/llama-3.1-8b-instruct:free",
        "google/gemma-2-9b-it:free",
        "qwen/qwen-2.5-7b-instruct:free"
    ]

    for model in models_to_try:
        try:
            payload = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3
            }
            res = requests.post(url, headers=headers, json=payload, timeout=25)
            if res.status_code == 200:
                data = res.json()
                if "choices" in data and len(data["choices"]) > 0:
                    return data["choices"][0]["message"]["content"]
        except Exception:
            continue

    raise Exception("Yapay zeka modelleri şu an meşgul.")

def parse_json_safely(raw_text: str):
    text = raw_text.strip()
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0]
    elif "```" in text:
        text = text.split("```")[1].split("```")[0]
    
    start_idx = text.find("{")
    end_idx = text.rfind("}")
    if start_idx != -1 and end_idx != -1:
        text = text[start_idx:end_idx+1]
        
    return json.loads(text.strip())

def load_question_bank():
    if os.path.exists(BANK_FILE):
        try:
            with open(BANK_FILE, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content: return json.loads(content)
        except Exception: pass
    return {"Tarih": [], "Coğrafya": [], "Türkçe": [], "Vatandaşlık": [], "Matematik": []}

def save_question_bank(data):
    try:
        with open(BANK_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception: pass

def load_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content: return json.loads(content)
        except Exception: pass
    return {"summaries": {}, "questions": {}, "past_questions": {}}

def save_cache(data):
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        temp_path = os.path.join(tempfile.gettempdir(), "kpss_database.json")
        try:
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception: pass

KPSS_SYLLABUS = {
    "Tarih": [
        "İlk ve Orta Çağ Türk Dünyası",
        "İlk Türk-İslam Devletleri ve Türkiye Tarihi",
        "Osmanlı Devleti: Kuruluş ve Yükselme Dönemi",
        "Osmanlı Devleti: Kültür ve Medeniyet",
        "Osmanlı Devleti: Duraklama, Gerileme ve Dağılma",
        "20. Yüzyıl Başlarında Osmanlı ve I. Dünya Savaşı",
        "Kurtuluş Savaşı Hazırlık ve Muharebeler Dönemi",
        "Atatürk İlkeleri ve İnkılap Tarihi",
        "Çağdaş Türk ve Dünya Tarihi"
    ],
    "Coğrafya": [
        "Türkiye'nin Coğrafi Konumu ve Jeopolitiği",
        "Türkiye'nin Yer Şekilleri ve Su Varlığı",
        "Türkiye'nin İklimi ve Bitki Örtüsü",
        "Türkiye'de Nüfus ve Yerleşme",
        "Türkiye'de Tarım ve Hayvancılık",
        "Türkiye'de Madenler ve Enerji Kaynakları",
        "Türkiye'de Sanayi, Ulaşım ve Ticaret",
        "Türkiye'nin Bölgesel Kalkınma Projeleri"
    ],
    "Türkçe": [
        "Sözcükte ve Cümlede Anlam",
        "Paragrafta Anlam ve Yapı",
        "Ses Bilgisi ve Yazım Kuralları",
        "Noktalama İşaretleri",
        "Sözcük Türleri ve Cümle Bilgisi",
        "Sözel Mantık"
    ],
    "Vatandaşlık": [
        "Temel Hukuk Kavramları",
        "Devlet Biçimleri ve Hükümet Sistemleri",
        "Anayasa Tarihi ve 1982 Anayasası Esasları",
        "Yasama, Yürütme ve Yargı Organları",
        "İdare Hukuku ve Türkiye'nin İdari Yapısı",
        "Uluslararası Kuruluşlar ve Güncel Bilgiler"
    ],
    "Matematik": [
        "Temel Kavramlar ve Sayı Kümeleri",
        "Bölme, Bölünebilme ve OBEB-OKEK",
        "Rasyonel Sayılar ve Basit Eşitsizlikler",
        "Mutlak Değer, Üslü ve Köklü Sayılar",
        "Çarpanlara Ayırma ve Oran-Orantı",
        "KPSS Problemler (Sayı, Kesir, Yaş, Yüzde, Hareket)",
        "Sayısal Mantık ve Tablo-Grafik Yorumlama"
    ]
}

@app.route("/")
def index():
    return render_template("index.html", syllabus=KPSS_SYLLABUS)

# 1. Konu Anlatımı API
@app.route("/api/summary", methods=["POST"])
def api_summary():
    try:
        data = request.get_json() or {}
        subject = data.get("subject", "Tarih")
        unit_name = data.get("unit_name", "İlk ve Orta Çağ Türk Dünyası")
        force_refresh = data.get("force_refresh", False)
        cache_key = f"{subject}_{unit_name}"

        cache = load_cache()
        if not force_refresh and cache_key in cache.get("summaries", {}):
            return jsonify({"success": True, "markdown": cache["summaries"][cache_key], "from_cache": True})

        prompt = f"""
        Sen Türkiye'nin en iyi KPSS hocasısın. Ders: {subject}, Ünite: {unit_name}.
        Eksiksiz bir Markdown ders fasikülü oluştur:
        # 📌 {unit_name}
        ## 1. Konunun Mantığı ve Temel Kavramlar
        ## 2. Detaylı Konu Anlatımı
        ## 3. ⚡ Sınav Şifreleri ve Kodlamalar
        ## 4. 🔥 [SINAV GARANTİ] Kritik Bilgiler
        ## 5. ⚠️ ÖSYM'nin En Sevdiği Çeldiriciler
        """
        try:
            text_resp = call_gemini(prompt)
        except Exception:
            text_resp = f"# 📌 {unit_name}\n\n## 1. Konunun Özeti\nBu konu KPSS'de her yıl en az 1-2 soru getiren temel ünitelerdendir.\n\n## 2. Kritik Kodlama\n* **Önemli Nokta:** Konu kavramlarını ve neden-sonuç ilişkilerini mutlaka pekiştirin.\n\n## 3. ÖSYM Uyarısı\n* Soru köklerindeki olumsuz ifadelere (değildir, söylenemez) dikkat edin."

        if "summaries" not in cache: cache["summaries"] = {}
        cache["summaries"][cache_key] = text_resp
        save_cache(cache)
        return jsonify({"success": True, "markdown": text_resp, "from_cache": False})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 200

# 2. Konuyu Genişlet API
@app.route("/api/expand-summary", methods=["POST"])
def api_expand_summary():
    try:
        data = request.get_json() or {}
        subject = data.get("subject", "Tarih")
        unit_name = data.get("unit_name", "")
        current_content = data.get("current_markdown", "")
        cache_key = f"{subject}_{unit_name}"

        prompt = f"Ders: {subject}, Ünite: {unit_name}. Bu konuyla ilgili ÖSYM'nin en eleyici dipnotlarını ekle."
        try:
            extra_markdown = call_gemini(prompt)
        except Exception:
            extra_markdown = "## 🔍 ÖSYM Dipnotları\n* Konuyla ilgili kronolojik sıralamalara ve temel ayırt edici terimlere dikkat ediniz."

        cache = load_cache()
        if "summaries" not in cache: cache["summaries"] = {}
        full_merged = f"{current_content}\n\n---\n\n{extra_markdown}"
        cache["summaries"][cache_key] = full_merged
        save_cache(cache)

        return jsonify({"success": True, "full_markdown": full_merged})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 200

# 3. Soru Üretme API
@app.route("/api/generate", methods=["POST"])
def api_generate():
    try:
        data = request.get_json() or {}
        subject = data.get("subject", "Tarih")
        unit_name = data.get("unit_name", "İlk ve Orta Çağ Türk Dünyası")
        count = int(data.get("count", 3))
        force_refresh = data.get("force_refresh", False)
        cache_key = f"{subject}_{unit_name}_{count}"

        cache = load_cache()
        if "questions" not in cache: cache["questions"] = {}

        if not force_refresh and cache_key in cache["questions"]:
            return jsonify({"success": True, "questions": cache["questions"][cache_key], "from_cache": True})

        prompt = f"""
        KPSS {subject} dersi {unit_name} ünitesinden {count} adet 5 şıklı test sorusu üret.
        SADECE JSON döndür:
        {{
          "questions": [
            {{
              "id": "q1",
              "question": "Soru metni",
              "options": {{"A": "A şıkkı", "B": "B şıkkı", "C": "C şıkkı", "D": "D şıkkı", "E": "E şıkkı"}},
              "correct_answer": "A",
              "explanations": {{"A": "Doğru çünkü...", "B": "Yanlış çünkü...", "C": "Yanlış", "D": "Yanlış", "E": "Yanlış"}},
              "memory_trick": "Pratik kodlama",
              "osym_traps": "Çeldirici analizi",
              "key_concepts": "Temel terim"
            }}
          ]
        }}
        """

        try:
            raw_resp = call_gemini(prompt)
            res_json = parse_json_safely(raw_resp)
            serialized_questions = res_json.get("questions", [])
        except Exception:
            serialized_questions = [
                {
                    "id": "kpss_f1",
                    "question": f"{unit_name} konusu ile ilgili aşağıdakilerden hangisi ÖSYM standartlarında temel ve doğru bir bilgidir?",
                    "options": {
                        "A": "Konuyla ilgili temel neden-sonuç bağı esastır.",
                        "B": "Yalnızca ezber bilgiye dayanır.",
                        "C": "Sınavda soru değeri taşımaz.",
                        "D": "Kronoloji tamamen önemsizdir.",
                        "E": "Tüm şıklar eşdeğerdir."
                    },
                    "correct_answer": "A",
                    "explanations": {
                        "A": "ÖSYM sorularında kavramlar ve mantıksal sonuçlar daima önceliklidir.",
                        "B": "Yanlış; kavrama düzeyi ölçülür.",
                        "C": "Yanlış; her yıl soru gelir.",
                        "D": "Yanlış; kronoloji mühimdir.",
                        "E": "Yanlış."
                    },
                    "memory_trick": "Mantık + Kavram = Net",
                    "osym_traps": "Aşırı kesinlik bildiren ifadelere dikkat edilmelidir.",
                    "key_concepts": f"{unit_name}, KPSS Mantığı"
                }
            ]

        for q in serialized_questions:
            q["subject"] = subject
            q["unit"] = unit_name

        cache["questions"][cache_key] = serialized_questions
        save_cache(cache)

        bank = load_question_bank()
        if subject not in bank: bank[subject] = []
        for q in serialized_questions:
            if not any(ex.get("id") == q.get("id") for ex in bank[subject]):
                bank[subject].append(q)
        save_question_bank(bank)

        return jsonify({"success": True, "questions": serialized_questions, "from_cache": False})
    except Exception as e:
        return jsonify({"success": False, "error": str(e), "questions": []}), 200

# 4. Çıkmış Soru İkizleri API
@app.route("/api/past-questions", methods=["POST"])
def api_past_questions():
    try:
        data = request.get_json() or {}
        subject = data.get("subject", "Tarih")
        unit_name = data.get("unit_name", "İlk ve Orta Çağ Türk Dünyası")
        count = int(data.get("count", 3))
        force_refresh = data.get("force_refresh", False)
        cache_key = f"past_{subject}_{unit_name}_{count}"

        cache = load_cache()
        if "past_questions" not in cache: cache["past_questions"] = {}

        if not force_refresh and cache_key in cache["past_questions"]:
            return jsonify({"success": True, "questions": cache["past_questions"][cache_key], "from_cache": True})

        prompt = f"""
        KPSS {subject} dersi {unit_name} ünitesinden ÖSYM Çıkmış Soru İkizi üret.
        SADECE JSON döndür:
        {{
          "questions": [
            {{
              "id": "past_q1",
              "question": "Soru metni",
              "options": {{"A": "A", "B": "B", "C": "C", "D": "D", "E": "E"}},
              "correct_answer": "A",
              "explanations": {{"A": "Açıklama", "B": "Açıklama", "C": "Açıklama", "D": "Açıklama", "E": "Açıklama"}},
              "memory_trick": "Taktik",
              "osym_traps": "ÖSYM Kalıbı",
              "key_concepts": "Kavram"
            }}
          ]
        }}
        """

        try:
            raw_resp = call_gemini(prompt)
            res_json = parse_json_safely(raw_resp)
            serialized_questions = res_json.get("questions", [])
        except Exception:
            serialized_questions = [
                {
                    "id": "past_f1",
                    "question": f"ÖSYM'nin geçmiş yıllarda {unit_name} konusunda sıklıkla sorduğu mantık çerçevesinde hangisi söylenebilir?",
                    "options": {
                        "A": "Öncüllü sorularda her yargı tek tek metinden teyit edilmelidir.",
                        "B": "Bilgi olmadan sadece tahminle çözülür.",
                        "C": "Kavramların zıt anlamları sorulmaz.",
                        "D": "Genel geçer kurallar sınavda değişir.",
                        "E": "Hiçbiri."
                    },
                    "correct_answer": "A",
                    "explanations": {
                        "A": "Çıkmış sorularda öncül-metin uyumu en kritik çözüm anahtarıdır.",
                        "B": "Yanlış.", "C": "Yanlış.", "D": "Yanlış.", "E": "Yanlış."
                    },
                    "memory_trick": "Öncülü Metne Bağla",
                    "osym_traps": "Metinde olmayan bilgiyi doğru kabul etmek en büyük tuzaktır.",
                    "key_concepts": "Çıkmış Soru Analizi"
                }
            ]

        for q in serialized_questions:
            q["subject"] = subject
            q["unit"] = unit_name

        cache["past_questions"][cache_key] = serialized_questions
        save_cache(cache)

        return jsonify({"success": True, "questions": serialized_questions, "from_cache": False})
    except Exception as e:
        return jsonify({"success": False, "error": str(e), "questions": []}), 200

# 5. Eğitmene Sor API
@app.route("/api/ask-coach", methods=["POST"])
def api_ask_coach():
    try:
        data = request.get_json() or {}
        q_text = data.get("question", "")
        user_q = data.get("user_query", "")
        correct = data.get("correct_answer", "")

        prompt = f"Soru: {q_text}\nDoğru Cevap: {correct}\nÖğrenci Sorusu: {user_q}\nKısa ve net sınav mantığıyla açıkla."
        try:
            reply = call_gemini(prompt)
        except Exception:
            reply = "Bu soruda doğru cevaba ulaşmak için soru kökündeki temel kurala ve şıklar arasındaki çelişkiye odaklanmalısın."
        return jsonify({"success": True, "reply": reply})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
