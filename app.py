import os
import json
import tempfile
from flask import Flask, render_template, jsonify, request
from google import genai

app = Flask(__name__)

# Render Environment'tan veya doğrudan koddan AQ. anahtarını alır
API_KEY = os.environ.get("GEMINI_API_KEY", "AQ.Ab8RN6IF4_4qM6Qn4R8__Yj7QDUt01uHMYRQXxa0Ua78oFCx5w").strip()

# AQ. formatındaki yeni nesil anahtarlar için istemci
client = genai.Client(api_key=API_KEY) if API_KEY else None

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BANK_FILE = os.path.join(BASE_DIR, "questions_bank.json")
CACHE_FILE = os.path.join(BASE_DIR, "kpss_database.json")

def load_question_bank():
    if os.path.exists(BANK_FILE):
        try:
            with open(BANK_FILE, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    return json.loads(content)
        except Exception:
            pass
    return {"Tarih": [], "Coğrafya": [], "Türkçe": [], "Vatandaşlık": [], "Matematik": []}

def save_question_bank(data):
    try:
        with open(BANK_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def load_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    return json.loads(content)
        except Exception:
            pass
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
        except Exception:
            pass

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
        if not client:
            return jsonify({"success": False, "error": "GEMINI_API_KEY eksik."}), 500

        data = request.get_json() or {}
        subject = data.get("subject", "Tarih")
        unit_name = data.get("unit_name", "İlk ve Orta Çağ Türk Dünyası")
        force_refresh = data.get("force_refresh", False)
        cache_key = f"{subject}_{unit_name}"

        cache = load_cache()
        if not force_refresh and cache_key in cache.get("summaries", {}):
            return jsonify({"success": True, "markdown": cache["summaries"][cache_key], "from_cache": True})

        prompt = f"""
        Sen Türkiye'nin en iyi KPSS eğitmenisin.
        Ders: {subject} | Ünite: {unit_name}

        Eksiksiz bir Markdown ders notu oluştur:
        # 📌 {unit_name}
        ## 1. Konunun Mantığı ve Neden-Sonuç İlişkileri
        ## 2. Detaylı Konu Anlatımı ve Bilinmesi Gerekenler
        ## 3. ⚡ Beyne Kazınacak Şifreler ve Kodlamalar
        ## 4. 🔥 [SINAV GARANTİ] Kırmızı Kritik Bilgiler
        ## 5. ⚠️ ÖSYM'nin En Sevdiği Çeldiriciler ve Tuzaklar
        ## 6. 📚 Mini Terim Sözlüğü
        """
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        text_resp = response.text
        if "summaries" not in cache: cache["summaries"] = {}
        cache["summaries"][cache_key] = text_resp
        save_cache(cache)
        return jsonify({"success": True, "markdown": text_resp, "from_cache": False})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# 2. Konuyu Genişlet API
@app.route("/api/expand-summary", methods=["POST"])
def api_expand_summary():
    try:
        if not client:
            return jsonify({"success": False, "error": "GEMINI_API_KEY eksik."}), 500

        data = request.get_json() or {}
        subject = data.get("subject", "Tarih")
        unit_name = data.get("unit_name", "")
        current_content = data.get("current_markdown", "")
        cache_key = f"{subject}_{unit_name}"

        prompt = f"""
        Ders: {subject} | Ünite: {unit_name}
        Bu üniteyle ilgili ÖSYM'nin en eleyici dipnotlarını ve 3 altın kuralı ek Markdown olarak yaz:
        ## 🔍 [ÖSYM DİPNOT & KRİTİK EK BİLGİLER]
        """
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        cache = load_cache()
        if "summaries" not in cache: cache["summaries"] = {}
        full_merged_markdown = f"{current_content}\n\n---\n\n{response.text}"
        cache["summaries"][cache_key] = full_merged_markdown
        save_cache(cache)

        return jsonify({"success": True, "full_markdown": full_merged_markdown})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# 3. Soru Üretme API
@app.route("/api/generate", methods=["POST"])
def api_generate():
    try:
        if not client:
            return jsonify({"success": False, "error": "GEMINI_API_KEY eksik."}), 500

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
        Sen ÖSYM Soru Komisyonu başkanısın.
        Ders: {subject} | Ünite: {unit_name} | Soru Sayısı: {count}
        
        KPSS formatında 5 şıklı sorular üret. Sadece geçerli bir JSON formatında şu şemayla döndür:
        {{
          "questions": [
            {{
              "id": "q1",
              "question": "Soru metni",
              "options": {{"A": "...", "B": "...", "C": "...", "D": "...", "E": "..."}},
              "correct_answer": "A",
              "explanations": {{"A": "...", "B": "...", "C": "...", "D": "...", "E": "..."}},
              "memory_trick": "Hafıza kodu",
              "osym_traps": "ÖSYM tuzağı",
              "key_concepts": "Kritik kavramlar"
            }}
          ]
        }}
        """

        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        
        raw_text = response.text.strip()
        if raw_text.startswith("```json"):
            raw_text = raw_text[7:]
        if raw_text.startswith("```"):
            raw_text = raw_text[3:]
        if raw_text.endswith("```"):
            raw_text = raw_text[:-3]

        res_json = json.loads(raw_text.strip())
        serialized_questions = res_json.get("questions", [])

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
        return jsonify({"success": False, "error": str(e)}), 500

# 4. Çıkmış Soru İkizleri API
@app.route("/api/past-questions", methods=["POST"])
def api_past_questions():
    try:
        if not client:
            return jsonify({"success": False, "error": "GEMINI_API_KEY eksik."}), 500

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
        Sen ÖSYM Arşiv ve Soru Analiz Uzmanısın.
        Ders: {subject} | Ünite: {unit_name} | Adet: {count}
        
        Son yıllarda ÖSYM'nin sorduğu çıkmış soruların birebir mantık ikizlerini üret. Sadece geçerli bir JSON döndür:
        {{
          "questions": [
            {{
              "id": "past_q1",
              "question": "Soru metni",
              "options": {{"A": "...", "B": "...", "C": "...", "D": "...", "E": "..."}},
              "correct_answer": "A",
              "explanations": {{"A": "...", "B": "...", "C": "...", "D": "...", "E": "..."}},
              "memory_trick": "Taktik kural",
              "osym_traps": "📌 2022 KPSS benzeri...",
              "key_concepts": "Kavramlar"
            }}
          ]
        }}
        """

        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        
        raw_text = response.text.strip()
        if raw_text.startswith("```json"):
            raw_text = raw_text[7:]
        if raw_text.startswith("```"):
            raw_text = raw_text[3:]
        if raw_text.endswith("```"):
            raw_text = raw_text[:-3]

        res_json = json.loads(raw_text.strip())
        serialized_questions = res_json.get("questions", [])

        for q in serialized_questions:
            q["subject"] = subject
            q["unit"] = unit_name

        cache["past_questions"][cache_key] = serialized_questions
        save_cache(cache)

        return jsonify({"success": True, "questions": serialized_questions, "from_cache": False})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# 5. Eğitmene Sor API
@app.route("/api/ask-coach", methods=["POST"])
def api_ask_coach():
    try:
        if not client:
            return jsonify({"success": False, "error": "GEMINI_API_KEY eksik."}), 500

        data = request.get_json() or {}
        q_text = data.get("question", "")
        user_q = data.get("user_query", "")
        correct = data.get("correct_answer", "")

        prompt = f"Soru: {q_text}\nDoğru Şık: {correct}\nÖğrenci Sorusu: {user_q}\nKısa ve net sınav mantığıyla açıkla."
        resp = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        return jsonify({"success": True, "reply": resp.text})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
