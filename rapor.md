# Proje Raporu: Dolapta Ne Var? (Gurme Mutfak Asistanı)

Bu doküman, RAG (Retrieval-Augmented Generation) ve LangChain ReAct (Reasoning and Acting) Agent mimarileri kullanılarak geliştirilen "Dolapta Ne Var?" isimli yapay zeka mutfak asistanı projesinin detaylarını ve gelişim sürecini içermektedir.

## Proje Özeti
Proje, kullanıcılara yemek tarifleri sunan, mutfakla ilgili soruları cevaplayan, eksik malzemeler için alternatifler bulan ve tamamen yapay zeka ile güçlendirilmiş interaktif bir aşçı botudur. Hem komut satırından (Terminal) hem de web arayüzünden (Streamlit) çalışabilmektedir.

- **Kullanılan Dil / Kütüphaneler:** Python, LangChain, Streamlit, ChromaDB.
- **Kullanılan LLM:** Gemini 3.1 Flash Lite (`gemini-3.1-flash-lite`).
- **Embedding Modeli:** Google Generative AI Embeddings.
- **Vektör Veritabanı:** Chroma.

## Dosya Yapısı ve Bileşenler
- `tarifler/tarifler.txt`: Sistemin RAG yeteneği için kullanılan yerel tarif dokümanları.
- `gurme_rag_bot.py`: Projenin komut satırında (terminal) çalışan interaktif versiyonu.
- `gurme_rag_ui.py`: Projenin Streamlit kütüphanesi ile yazılmış olan, modern ve kullanıcı dostu web arayüzü (UI) versiyonu.

## Temel Özellikler
1. **Akıllı Veri Çekimi (RAG):** Kullanıcının isteği öncelikle yerel tarif veritabanında (Chroma) aranır.
2. **Follow-Up (Takipli Soru) Baloncukları:** Ajan, cevabını verdikten sonra kullanıcıya yol gösterecek ve konuyu devam ettirebilecek öneri sorular üretir. UI üzerinde bu sorulara tıklanabilir butonlar şeklinde basılır.
3. **DNS ve Ağ Hata Yönetimi:** İnternet araması sırasında oluşabilecek ağ engelleri veya DNS hataları (örneğin DuckDuckGo/Brave block) ajan tarafından yakalanıp uygulamayı çökertmeden güvenle idare edilir.
4. **Şeffaf ve Kalıcı Düşünme Süreci (Agent Transparency):** Ajanın arka planda hangi araçları kullanmaya karar verdiği, bu araçlara hangi argümanları gönderdiği ve araçlardan dönen sonuçlar Streamlit arayüzünde detaylı olarak gösterilir. Bu düşünce süreci ("Şefin Düşünce Süreci") sohbet geçmişinde kalıcı olarak kaydedilir; böylece kullanıcı dilediği zaman bu adımları açıp inceleyebilir.
5. **Gelişmiş Yan Panel (Sidebar):** Sol panelde teknik detaylar (veritabanı yenileme vb.) "Geliştirici Ayarları" menüsü altına gizlenmiş, bunun yerine kullanıcıya "Sürpriz Tarif Öner", "15 Dakikalık Yemek" ve "Sağlıklı Diyet" gibi tek tıkla çalıştırılabilen faydalı Hızlı Asistan butonları eklenmiştir.
6. **Güvenlik Kalkanı (Guardrail):** Siber saldırılara (Prompt Injection, SQL Injection) ve toksik/argo kullanıma karşı özel bir Python kalkanı geliştirilmiştir. Yasaklı ifadeler LLM'e ulaşmadan arayüzde yakalanıp engellenir.

## Ajanın Sahip Olduğu Araçlar (Tools)
Ajan, soruları yanıtlarken ihtiyacına göre kendi kararıyla aşağıdaki fonksiyonlara ve araçlara başvurabilir:

1. 🔍 **Yerel Veritabanı (`tarif_veritabani`):** Kullanıcının normal tarif isteklerinde her zaman ilk başvurduğu araçtır. Yerel belgelere RAG üzerinden erişir.
2. 🌐 **Web Arama (`web_arama`):** Eğer kullanıcı yeni, farklı ve heyecan verici bir tarif isterse, ajan doğrudan DuckDuckGo üzerinden internet araştırması yapar.
3. 🌍 **Tarihçe ve Kültür (`yemek_tarihcesi`):** Her tarif sunumunda otomatik olarak Wikipedia üzerinden yemeğin tarihi kökeni veya kültürel önemi hakkında bilgi çeker. "Tarihten Bir Tutam" başlığı altında kullanıcıya anektod sunar.
4. 🧮 **Porsiyon Hesaplama (`porsiyon_hesapla`):** Kullanıcı porsiyon değiştirmek istediğinde matematiğini kusursuz bir şekilde yaparak yeni malzeme ölçülerini hesaplar.
5. 🔄 **Malzeme Alternatifi (`malzeme_alternatifi`):** Evde eksik olan bir malzeme için, bir şef mantığıyla aynı lezzet ve asiditeyi sağlayacak alternatifler önerir (Örn: Krema yerine süt + tereyağı).
6. 🔥 **Kalori Hesaplama (`kalori_hesapla`):** Yemeğin protein, karbonhidrat ve yağ değerlerini tahmin ederek porsiyon başı tahmini kalorisini bilimsel formül ile hesaplar.
7. 💚 **Sağlık Skoru (`saglik_skoru_hesapla`):** Yemeğin içerdiği şeker, yağ, kızartma işlemi ve lif dengesine bakarak 100 üzerinden bir "Sağlık Skoru" çıkarır ve yemeği daha sağlıklı yapmak için öneriler sunar.
8. 🧊 **Dolap Hafızası (`dolaba_ekle` & `dolaptan_cikar`):** Kullanıcının mutfağındaki malzemeleri `dolap_envanteri.json` dosyasına kaydederek kalıcı bir hafıza oluşturur. Tarif üretirken bu envanteri baz alır.
9. 🛒 **Alışveriş Listesi (`alisveris_listesi_olustur`):** Kullanıcının evinde olmayan eksik malzemeler için reyonlara/kategorilere (Manav, Kasap vb.) ayrılmış şık bir Markdown tablosu üretir. Ayrıca eksik malzemeleri `.env` ayarlarında belirtilen kullanıcı e-posta adresine **otomatik olarak mail atar**.
10. 🍷 **İçecek Eşleştirme (`icecek_eslestir`):** Önerilen yemeğin lezzet profiline, asiditesine veya ağırlığına göre en uygun eşlikçi içeceği (şarap, ev yapımı kokteyl vb.) seçer ve "Tarifini istersen verebilirim" diyerek kullanıcıyı yönlendirir.

---
*Not: Bu rapor, projeye eklenen yeni özelliklerle birlikte otomatik olarak güncellenecektir.*
