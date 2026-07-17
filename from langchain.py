import os
from dotenv import load_dotenv
load_dotenv()
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

# --- 1. AYARLAR VE API ANAHTARI ---
# API Anahtarı .env dosyasından otomatik yüklenmektedir.

KLASOR_YOLU = "/Users/yusufbb/Desktop/proje/faaliyet_raporları" 
DB_YOLU = "/Users/yusufbb/Desktop/proje/finans_db"

# --- 2. YEREL EMBEDDING MODELİ (Ücretsiz) ---
print("Yerel embedding modeli başlatılıyor (İnternet kotası harcamaz)...")
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

# --- 3. VEKTÖR VERİTABANI KONTROLÜ VE OLUŞTURMA ---
if not os.path.exists(DB_YOLU):
    print(f"\nVeritabanı bulunamadı. '{KLASOR_YOLU}' klasöründeki PDF'ler işleniyor...")
    
    loader = PyPDFDirectoryLoader(KLASOR_YOLU)
    belgeler = loader.load()
    print(f"Okuma tamam! Toplam {len(belgeler)} sayfa hafızaya alındı.")
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1500,
        chunk_overlap=300,
        length_function=len,
        separators=["\n\n", "\n", " ", ""]
    )
    chunks = text_splitter.split_documents(belgeler)
    print(f"Toplam {len(chunks)} parça oluşturuldu.")
    
    print("\nDİKKAT: Vektör veritabanı oluşturuluyor...")
    print("30.000 parçayı işlemek bilgisayarının hızına göre 5 ila 15 dakika sürebilir. Lütfen terminali kapatma, arkada çalışıyor...")
    
    vector_db = Chroma.from_documents(documents=chunks, embedding=embeddings, persist_directory=DB_YOLU)
    print("\nHarika! Veritabanı başarıyla oluşturuldu ve diske kaydedildi!")
else:
    print(f"\nMevcut vektör veritabanı '{DB_YOLU}' konumundan yükleniyor...")
    vector_db = Chroma(persist_directory=DB_YOLU, embedding_function=embeddings)
    print("Veritabanı başarıyla yüklendi!")

# --- 4. GEMINI LLM BAĞLANTISI ---
print("Gemini AI bağlantısı kuruluyor...")
llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash", temperature=0)

# --- 5. MODERN SIFIR HALÜSİNASYON PROMPT'U (GÜNCELLENDİ) ---
template = """
Sen uzman ve deneyimli bir finansal analistsin. Görevin, kullanıcının sorularını YALNIZCA aşağıda sağlanan 'Bağlam (Context)' içindeki raporlara, tablolara ve dipnotlara dayanarak yanıtlamaktır.

Uygulaman Gereken Kurallar:
1. Eğer sorulan soru (örneğin net kâr, kurulu güç vb.) bağlam içindeki tablolarda veya metinlerde doğrudan geçiyorsa, bu verileri kullanarak net ve profesyonel bir finansal yanıt oluştur.
2. Eğer net bir rakam yoksa ama tablolardaki verilerden (örneğin gelir tablosundan) hesaplanabiliyorsa, hesaplamayı yap ve nasıl hesapladığını açıkla.
3. Bağlam dışındaki genel bilgilerini veya internetteki güncel olmayan bilgileri KESİNLİKLE kullanma.
4. Eğer bağlam içinde sorulan şirketle veya konuyla ilgili hiçbir veri, tablo veya ima YOKSA, o zaman "Aradığınız bilgi sağlanan belgelerde bulunmamaktadır." de.
5. Yanıtının en altında, bu bilgiyi hangi belgeden aldığını mutlaka belirt.

Bağlam (Context):
{context}

Soru: {question}

Analist Yanıtı:"""

prompt = ChatPromptTemplate.from_template(template)

# --- 6. MODERN RAG SİSTEMİ (LCEL ZİNCİRİ) ---
# Gelen belgeleri tek bir metin haline getiren yardımcı fonksiyon
def format_docs(docs):
    formatted = []
    for doc in docs:
        source = doc.metadata.get('source', 'Bilinmeyen Kaynak').split('/')[-1]
        page = doc.metadata.get('page', '?')
        formatted.append(f"[{source} - Sayfa {page}]:\n{doc.page_content}")
    return "\n\n---\n\n".join(formatted)

retriever = vector_db.as_retriever(search_kwargs={"k": 5})

# Modern LangChain Zincir Yapısı (RetrievalQA yerine bunu kullanıyoruz)
rag_chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)

# --- 7. BASİT KULLANICI ARAYÜZÜ (CLI SOHBET DÖNGÜSÜ) ---
print("\n" + "="*50)
print("BİST ENERJİ FİNANSAL ANALİST BOTU HAZIR!")
print("Çıkmak için 'q' veya 'çıkış' yazabilirsiniz.")
print("="*50 + "\n")

while True:
    soru = input("\nSorunuzu girin (Örn: ENJSA'nın son çeyrek net kârı nedir?): ")
    
    if soru.lower() in ['q', 'çıkış', 'quit', 'exit']:
        print("Sistem kapatılıyor. İyi çalışmalar!")
        break
        
    if not soru.strip():
        continue
        
    print("\nAnalist belgeleri inceliyor, lütfen bekleyin...")
    
    try:
        yanit = rag_chain.invoke(soru)
        print("\n--- ANALİST YANITI ---")
        print(yanit)
        print("----------------------\n")
    except Exception as e:
        print(f"\nBir hata oluştu: {e}")