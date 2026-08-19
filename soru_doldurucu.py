import os
import json
import time
from google import genai
from google.genai import types

# API Anahtarın
client = genai.Client(api_key="AQ.Ab8RN6K_3c_JCnxPS023SN7oB8zlbicJSVI9ZSCzAc-tDP3kuA")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BANK_FILE = os.path.join(BASE_DIR, "questions_bank.json")

# En güncel ve standart model
MODEL_NAME = "gemini-3.6-flash"

KPSS_SYLLABUS = {
    "Tarih": [
        "İlk ve Orta Çağ Türk Dünyası",
        "İlk Türk-İslam Devletleri ve Türkiye Tarihi",
        "Osmanlı Devleti: Kuruluş ve Yükselme",
        "Osmanlı Devleti: Kültür ve Medeniyet",
        "Osmanlı Devleti: Dağılma Dönemi",
        "Kurtuluş Savaşı Hazırlık ve Muharebeler",
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
        "Türkiye'de Sanayi ve Ulaşım"
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
        "1982 Anayasası Esasları",
        "Yasama, Yürütme ve Yargı Organları",
        "İdare Hukuku",
        "Güncel Bilgiler"
    ],
    "Matematik": [
        "Temel Kavramlar ve Sayı Kümeleri",
        "Bölme-Bölünebilme ve OBEB-OKEK",
        "Rasyonel Sayılar ve Basit Eşitsizlikler",
        "Üslü ve Köklü Sayılar",
        "KPSS Problemler (Yaş, Kesir, Yüzde, Hız)",
        "Sayısal Mantık"
    ]
}

def load_bank():
    if os.path.exists(BANK_FILE):
        try:
            with open(BANK_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"Tarih": [], "Coğrafya": [], "Türkçe": [], "Vatandaşlık": [], "Matematik": []}

def save_bank(data):
    try:
        with open(BANK_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Kayıt hatası: {e}")

def generate_questions_for_unit(subject, unit, count=3):
    prompt = f"""
    Sen ÖSYM Soru Komisyonu başkanısın.
    Ders: {subject}
    Ünite: {unit}
    Adet: {count}
    
    Lütfen sadece saf JSON formatında bir liste döndür. Başka hiçbir açıklama yazma.
    Format şu yapıda olmalıdır:
    [
      {{
        "id": "{subject[:3].lower()}_{int(time.time())}_1",
        "subject": "{subject}",
        "unit": "{unit}",
        "question": "Soru metni...",
        "options": {{
          "A": "Şık A",
          "B": "Şık B",
          "C": "Şık C",
          "D": "Şık D",
          "E": "Şık E"
        }},
        "correct_answer": "A",
        "explanations": {{
          "A": "A şıkkı açıklaması...",
          "B": "B şıkkı açıklaması...",
          "C": "C şıkkı açıklaması...",
          "D": "D şıkkı açıklaması...",
          "E": "E şıkkı açıklaması..."
        }},
        "memory_trick": "Hafıza kodu veya şifre...",
        "osym_traps": "Öğrencilerin düştüğü çeldirici...",
        "key_concepts": "Kritik kavramlar..."
      }}
    ]
    """
    
    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.3,
                ),
            )
            data = json.loads(response.text)
            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and "questions" in data:
                return data["questions"]
            return []
        except Exception as e:
            print(f"    [Hata Detayı]: {e}")
            time.sleep(3)
            
    return []

def main():
    try:
        bank = load_bank()
        print("🚀 Soru havuzu doldurma başlatıldı...\n")

        for subject, units in KPSS_SYLLABUS.items():
            if subject not in bank:
                bank[subject] = []
            
            print(f"\n==========================================")
            print(f"📚 DERS: {subject}")
            print(f"==========================================")
            
            for unit in units:
                existing = [q for q in bank[subject] if q.get("unit") == unit]
                if len(existing) >= 3:
                    print(f"  ⏭️ {unit} zaten kayıtlı ({len(existing)} soru), atlanıyor.")
                    continue

                print(f"  ⏳ {unit} için sorular üretiliyor...")
                questions = generate_questions_for_unit(subject, unit, count=3)
                
                if questions:
                    bank[subject].extend(questions)
                    save_bank(bank)
                    print(f"  ✅ +{len(questions)} soru eklendi! (Toplam {subject}: {len(bank[subject])})")
                else:
                    print(f"  ❌ {unit} için soru alınamadı.")
                
                time.sleep(1)

        print("\n🎉 Tüm müfredat başarıyla tamamlandı!")
    except Exception as err:
        print(f"\n💥 Beklenmeyen hata: {err}")
    finally:
        print("\n" + "="*50)
        input("Pencereyi kapatmak için [ENTER]'a basın...")

if __name__ == "__main__":
    main()