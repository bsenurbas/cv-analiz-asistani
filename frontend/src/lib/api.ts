// ─── Base URL ──────────────────────────────────────────────────────────────────
// Proxy kullandığımız için artık doğrudan absolute URL (http://localhost:8000) yazmıyoruz.
// İstekler doğrudan kendi frontend portumuz üzerinden (/api) geçerek proxy ile backend'e iletilir.
const API_BASE = import.meta.env.VITE_API_BASE_URL ?? ""
const BASE = `${API_BASE}/api`

// ─── Tip Tanımları ─────────────────────────────────────────────────────────────

export interface CvAnalysisResult {
  isim?: string
  kategori?: string
  kategori_guven?: number
  ozet?: string
  toplam_deneyim_yil?: number
  teknik_beceriler?: string[]
  egitim?: Array<{
    kurum?: string
    bolum?: string
    derece?: string
  }>
  deneyim?: Array<{
    pozisyon?: string
    sirket?: string
    baslangic?: number
    bitis?: number | null
  }>
  oneriler?: string[]
  guclu_yonler?: string[]
  zayif_yonler?: string[]
}

export interface CompareCandidate {
  isim?: string
  skor?: number
  guclu_yonler?: string[]
  zayif_yonler?: string[]
}

export interface CvCompareResult {
  kazanan?: string           // "cv1" | "cv2"
  cv1?: CompareCandidate
  cv2?: CompareCandidate
  karar_gerekcesi?: string
}

export interface MatchingCandidate {
  aday_id?: string
  skor?: number
  gerekce?: string
}

export interface MatchingResult {
  adaylar?: MatchingCandidate[]
}

export interface AssistantMessage {
  answer: string
  conversation_id?: string
}

// ─── Yardımcı: HTTP Hata Kontrolü ──────────────────────────────────────────────
async function handleResponse<T>(res: Response, label: string): Promise<T> {
  if (!res.ok) {
    const detail = await res.text().catch(() => "")
    throw new Error(`${label} (${res.status}): ${detail}`)
  }
  return res.json() as Promise<T>
}

// ──────────────────────────────────────────────────────────────────────────────
// 1. CV Analizi
//    POST /api/cv/analyze (Proxy üzerinden -> http://localhost:8000/api/cv/analyze)
// ──────────────────────────────────────────────────────────────────────────────
export async function analyzeCV(file: File): Promise<CvAnalysisResult> {
  const form = new FormData()
  form.append("file", file)

  // BASE /api olduğu için url: /api/cv/analyze olacaktır.
  const res = await fetch(`${BASE}/cv/analyze`, {
    method: "POST",
    body: form,
  })

  return handleResponse<CvAnalysisResult>(res, "CV analiz hatası")
}

// ──────────────────────────────────────────────────────────────────────────────
// 2. CV Karşılaştırma
//    POST /api/cv/compare (Proxy üzerinden -> http://localhost:8000/api/cv/compare)
// ──────────────────────────────────────────────────────────────────────────────
export async function compareCVs(
  cv1: File,
  cv2: File,
  jobDesc: string,
): Promise<CvCompareResult> {
  const form = new FormData()
  form.append("cv1", cv1)
  form.append("cv2", cv2)
  form.append("job_desc", jobDesc)

  const res = await fetch(`${BASE}/cv/compare`, {
    method: "POST",
    body: form,
  })

  return handleResponse<CvCompareResult>(res, "CV karşılaştırma hatası")
}

// ──────────────────────────────────────────────────────────────────────────────
// 3. İş İlanı Eşleştirme
//    POST /api/matching (Proxy üzerinden -> http://localhost:8000/api/matching)
// ──────────────────────────────────────────────────────────────────────────────
export async function matchJobs(jobDesc: string): Promise<MatchingResult> {
  const res = await fetch(`${BASE}/matching`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ job_desc: jobDesc }),
  })

  return handleResponse<MatchingResult>(res, "Eşleştirme hatası")
}

// ──────────────────────────────────────────────────────────────────────────────
// 4. İK Asistanı Chat
//    POST /api/assistant/chat (Proxy üzerinden -> http://localhost:8000/api/assistant/chat)
// ──────────────────────────────────────────────────────────────────────────────
export async function chatWithAssistant(
  message: string,
  conversationId: string,
): Promise<AssistantMessage> {
  const res = await fetch(`${BASE}/assistant/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, conversation_id: conversationId }),
  })

  return handleResponse<AssistantMessage>(res, "Asistan hatası")
}
export interface TfidfResult {
  cv_id: string
  kategori: string
  skor: number
}

export interface MatchingResult {
  adaylar?: MatchingCandidate[]
  tfidf_sonuclari?: TfidfResult[] // TF-IDF verisi için eklendi
}

export interface HistoryRecord {
  Tarih: string
  // Eski format destekleri
  "İlan Metni"?: string
  "Aday ID"?: string
  Skor?: string
  Sure?: string
  // Yeni format destekleri
  "İlan"?: string
  "Aday Sayısı"?: number
  "Süre"?: string
}

// ──────────────────────────────────────────────────────────────────────────────
// 5. İş İlanı Geçmişini Getir
//    GET /api/matching/history
// ──────────────────────────────────────────────────────────────────────────────
export async function getMatchingHistory(): Promise<HistoryRecord[]> {
  const res = await fetch(`${BASE}/matching/history`, {
    method: "GET",
  })
  
  if (!res.ok) return []
  return res.json()
}
export interface SystemMetrics {
  veritabani: string;
  toplam_cv: string;
  ai_durumu: string;
  hiz: string;
  analiz_yapilan: number;
  eslestirilen: number;
}

// ──────────────────────────────────────────────────────────────────────────────
// 6. Sistem Metriklerini Getir
//    GET /api/metrics
// ──────────────────────────────────────────────────────────────────────────────
export async function getSystemMetrics(): Promise<SystemMetrics> {
  const res = await fetch(`${BASE}/metrics`, {
    method: "GET",
  })
  
  if (!res.ok) {
    throw new Error("Metrikler alınamadı")
  }
  return res.json()
}