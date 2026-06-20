import { useState } from "react"
import { GitCompareArrows, Inbox, Trophy, Zap, Loader2, CheckCircle2, XCircle, Briefcase, GraduationCap, Target, Lightbulb, Star, MapPin } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Textarea } from "@/components/ui/textarea"
import { Separator } from "@/components/ui/separator"
import { FileDropzone } from "@/components/dashboard/file-dropzone"
import { analyzeCV, compareCVs } from "@/lib/api"
import type { CvAnalysisResult, CvCompareResult } from "@/lib/api"

export function TabCvAnalysis() {
  // ── Step 1: Tekli CV Analiz ──────────────────────────────────────────────────
  const [cvFileObj, setCvFileObj] = useState<File | null>(null)
  const [result, setResult] = useState<CvAnalysisResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [analyzeError, setAnalyzeError] = useState<string | null>(null)

  // ── Step 1B: CV Karşılaştırma ────────────────────────────────────────────────
  const [cv1, setCv1] = useState<File | null>(null)
  const [cv2, setCv2] = useState<File | null>(null)
  const [jobDesc, setJobDesc] = useState("")
  const [compareResult, setCompareResult] = useState<CvCompareResult | null>(null)
  const [compareLoading, setCompareLoading] = useState(false)
  const [compareError, setCompareError] = useState<string | null>(null)

  // ── Tekli CV Analiz ──────────────────────────────────────────────────────────
  const handleAnalyze = async () => {
    if (!cvFileObj) return
    setLoading(true)
    setAnalyzeError(null)
    setResult(null)
    try {
      const data = await analyzeCV(cvFileObj)
      setResult(data)
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Bilinmeyen hata"
      setAnalyzeError(msg)
      console.error("CV Analiz Hatası:", msg)
    } finally {
      setLoading(false)
    }
  }

  // ── CV Karşılaştırma ─────────────────────────────────────────────────────────
  const handleCompare = async () => {
    if (!cv1 || !cv2) return
    setCompareLoading(true)
    setCompareError(null)
    setCompareResult(null)
    try {
      const data = await compareCVs(cv1, cv2, jobDesc)
      setCompareResult(data)
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Bilinmeyen hata"
      setCompareError(msg)
      console.error("Karşılaştırma Hatası:", msg)
    } finally {
      setCompareLoading(false)
    }
  }

  // Güvenli Veri Çıkartımları (Beyaz Ekran ve Kayıp Veri Çözümleri)
  const safeEgitim = Array.isArray(result?.egitim) ? result.egitim : []
  const safeDeneyim = Array.isArray(result?.deneyim) ? result.deneyim : []
  const safeBeceriler = Array.isArray(result?.teknik_beceriler) 
    ? result.teknik_beceriler 
    : (typeof result?.teknik_beceriler === 'string' ? (result.teknik_beceriler as string).split(',').map(s => s.trim()) : [])
  const safeOneriler = Array.isArray(result?.oneriler) ? result.oneriler : []
  
  // Dify 'isim' verisini 'kisisel' objesi içine koyduğunda yakalamak için:
  const safeIsim = (result as any)?.kisisel?.isim || result?.isim || "İsim Belirtilmemiş"
  const safeSehir = (result as any)?.kisisel?.sehir || ""

  return (
    <div className="space-y-8 pb-10">
      {/* ── Step 1: Upload & Analyze ────────────────────────────────────────── */}
      <section>
        <SectionHeading
          step="ADIM 1"
          title="Özgeçmiş Yükle & Analiz Et"
          desc="Yapay zeka analizi ve detaylı aday profilini çıkarmak için CV yükleyin."
        />

        <div className="grid gap-6 lg:grid-cols-12">
          {/* Sol Kart — Dosya Yükleme */}
          <div className="lg:col-span-4 space-y-4">
            <Card className="hover:border-primary/20 transition-colors h-full">
              <CardContent className="space-y-4 p-6 flex flex-col justify-center h-full">
                <FileDropzone
                  id="cv-main"
                  fileName={cvFileObj?.name ?? null}
                  onFile={(file) => { setCvFileObj(file); setResult(null); setAnalyzeError(null) }}
                />
                <Button
                  onClick={handleAnalyze}
                  disabled={!cvFileObj || loading}
                  className="w-full"
                  size="lg"
                >
                  {loading ? (
                    <><Loader2 className="size-4 animate-spin" /> Analiz ediliyor…</>
                  ) : (
                    <><Zap className="size-4" /> Analiz Başlat</>
                  )}
                </Button>
                {analyzeError && (
                  <p className="text-xs text-destructive text-center">{analyzeError}</p>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Sağ Kart — Analiz Sonucu veya Boş Durum */}
          <div className="lg:col-span-8">
            {result ? (
              <div className="space-y-6 animate-in fade-in zoom-in-95 duration-300">
                
                {/* Üst Metrikler */}
                <div className="grid grid-cols-3 gap-4">
                  <MetricTile icon={<Briefcase />} value={result.toplam_deneyim_yil ?? 0} label="Deneyim (Yıl)" />
                  <MetricTile icon={<Star />} value={safeBeceriler.length} label="Teknik Yetenek" />
                  <MetricTile icon={<GraduationCap />} value={safeEgitim.length} label="Eğitim Kaydı" />
                </div>

                {/* Aday Profili Detayları */}
                <Card>
                  <CardContent className="p-6 space-y-6">
                    <div className="flex justify-between items-start border-b border-border pb-4">
                      <div>
                        <h4 className="text-xl font-bold text-foreground flex items-center gap-2">
                          {safeIsim}
                          {safeSehir && (
                            <span className="text-xs font-normal bg-muted text-muted-foreground px-2 py-0.5 rounded-full flex items-center gap-1">
                              <MapPin className="size-3" /> {safeSehir}
                            </span>
                          )}
                        </h4>
                        {result.ozet && (
                          <p className="mt-1 text-sm text-muted-foreground leading-relaxed">
                            {result.ozet}
                          </p>
                        )}
                      </div>
                    </div>

                    <div className="space-y-4">
                      {/* Eğitim */}
                      <div>
                        <h5 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-2 flex items-center gap-1.5">
                          <GraduationCap className="size-4" /> EĞİTİM
                        </h5>
                        {safeEgitim.length > 0 ? (
                          <div className="font-medium text-sm">
                            {safeEgitim[0]?.kurum || "Bilinmiyor"}, {safeEgitim[0]?.bolum || "Bilinmiyor"} {safeEgitim[0]?.derece ? `(${safeEgitim[0].derece})` : ""}
                          </div>
                        ) : (
                          <div className="text-sm text-muted-foreground">Eğitim bilgisi bulunamadı.</div>
                        )}
                      </div>

                      {/* Yetenekler */}
                      <div>
                        <h5 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-2 flex items-center gap-1.5">
                          <Target className="size-4" /> TEKNİK BECERİLER
                        </h5>
                        <div className="flex flex-wrap gap-1.5">
                          {safeBeceriler.length > 0 ? (
                            safeBeceriler.slice(0, 15).map((b, idx) => (
                              <span key={idx} className="rounded-md bg-primary/10 px-2.5 py-1 text-xs font-medium text-primary">
                                {typeof b === 'object' ? JSON.stringify(b) : String(b)}
                              </span>
                            ))
                          ) : (
                            <span className="text-sm text-muted-foreground">Teknik beceri bulunamadı.</span>
                          )}
                        </div>
                      </div>

                      {/* Deneyimler */}
                      <div>
                        <h5 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-2 flex items-center gap-1.5">
                          <Briefcase className="size-4" /> DENEYİMLER
                        </h5>
                        <div className="space-y-2">
                          {safeDeneyim.length > 0 ? (
                            safeDeneyim.slice(0, 4).map((d: any, i: number) => (
                              <div key={i} className="text-sm">
                                <span className="text-primary mr-1.5">•</span>
                                <span className="font-semibold">{d?.pozisyon || "Pozisyon Bilinmiyor"}</span>
                                <span className="text-muted-foreground">, {d?.sirket || ""} ({d?.baslangic || "Bilinmiyor"} - {d?.bitis || "Günümüz"})</span>
                              </div>
                            ))
                          ) : (
                            <div className="text-sm text-muted-foreground">Deneyim bilgisi bulunamadı.</div>
                          )}
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>

              </div>
            ) : (
              <Card className="h-full border-dashed bg-muted/20">
                <CardContent className="flex h-full flex-col justify-center py-16">
                  <EmptyState
                    icon={<Inbox className="size-8 text-muted-foreground" />}
                    title="Analiz sonuçları burada görünecek"
                    desc="Soldan dosya yükleyip 'Analiz Başlat'a tıklayın. Aday profili, yetenek radarı ve deneyim çizelgesi burada oluşturulacaktır."
                  />
                </CardContent>
              </Card>
            )}
          </div>
        </div>

        {/* ── Ek Görselleştirmeler (Grafikler & Öneriler) ────────────────────── */}
        {result && (
          <div className="mt-6 space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500 delay-150">
        
            {/* Grafikler: Radar ve Timeline */}
            <div className="grid gap-6 md:grid-cols-2">
              <Card>
                <CardContent className="p-6">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-muted-foreground mb-4 text-center">Beceri Radar Grafiği</h4>
                  <SkillRadarChart skills={safeBeceriler} />
                </CardContent>
              </Card>

              <Card>
                <CardContent className="p-6">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-muted-foreground mb-4 text-center">Deneyim Zaman Çizelgesi</h4>
                  <ExperienceTimeline experiences={safeDeneyim} />
                </CardContent>
              </Card>
            </div>

            {/* Güçlendirme Önerileri */}
            {safeOneriler.length > 0 && (
              <div className="space-y-4 pt-4">
                <SectionHeading step="ÖNERİLER" title="CV'yi Güçlendirmek İçin Öneriler" desc="Yapay zeka tarafından adayın özgeçmişini iyileştirmek için saptanan maddeler." />
                <div className="grid gap-4 md:grid-cols-2">
                  {safeOneriler.map((oneri: any, idx: number) => {
                    const isObj = typeof oneri === 'object' && oneri !== null;
                    const baslik = isObj ? (oneri.baslik || oneri.kategori || "İyileştirme Fikri") : "İyileştirme Fikri";
                    const aciklama = isObj ? (oneri.aciklama || JSON.stringify(oneri)) : oneri;

                    return (
                      <div key={idx} className="rounded-xl bg-emerald-500/5 border border-emerald-500/15 p-5 transition-colors hover:bg-emerald-500/10">
                        <div className="flex items-center gap-2 mb-2">
                          <Lightbulb className="size-4 text-emerald-600 dark:text-emerald-400 shrink-0" />
                          <span className="text-xs font-bold text-emerald-600/80 dark:text-emerald-400/80 uppercase line-clamp-1">{baslik}</span>
                        </div>
                        <p className="text-sm font-semibold text-foreground leading-snug">
                          {aciklama}
                        </p>
                      </div>
                    )
                  })}
                </div>
              </div>
            )}
          </div>
        )}
      </section>

      <Separator className="my-10" />

      {/* ── Step 1B: Comparison Engine ──────────────────────────────────────── */}
      <section className="space-y-6">
        <SectionHeading
          step="ADIM 1B"
          title="İki CV Karşılaştır"
          desc="Bir iş ilanı metnine karşı iki farklı adayı değerlendirin ve kazananı bulun."
          icon={GitCompareArrows}
        />

        <div className="grid gap-6 lg:grid-cols-12">
          {/* Form Alanı */}
          <div className="lg:col-span-5 space-y-4">
            <Card className="hover:border-primary/20 transition-colors">
              <CardContent className="space-y-5 p-6">
                <div className="grid gap-4 sm:grid-cols-2">
                  <FileDropzone
                    id="cmp-1"
                    label="Birinci CV"
                    fileName={cv1?.name ?? null}
                    onFile={(file) => { setCv1(file); setCompareResult(null) }}
                    compact
                  />
                  <FileDropzone
                    id="cmp-2"
                    label="İkinci CV"
                    fileName={cv2?.name ?? null}
                    onFile={(file) => { setCv2(file); setCompareResult(null) }}
                    compact
                  />
                </div>

                <div>
                  <p className="mb-2 text-sm font-medium text-foreground">Karşılaştırma için İş İlanı</p>
                  <Textarea
                    value={jobDesc}
                    onChange={(e) => setJobDesc(e.target.value)}
                    placeholder="Örn: Stratejik İK deneyimi olan, performans yönetimi ve işe alım süreçlerini yönetecek İK yöneticisi aranıyor..."
                    className="min-h-32 resize-none"
                  />
                </div>

                <Button
                  onClick={handleCompare}
                  disabled={!cv1 || !cv2 || !jobDesc.trim() || compareLoading}
                  size="lg"
                  className="w-full"
                >
                  {compareLoading ? (
                    <><Loader2 className="size-4 animate-spin" /> Karşılaştırılıyor…</>
                  ) : (
                    <><GitCompareArrows className="size-4" /> CV Karşılaştır</>
                  )}
                </Button>

                {compareError && (
                  <p className="text-xs text-destructive text-center">{compareError}</p>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Sonuç Alanı */}
          <div className="lg:col-span-7">
            {compareResult ? (
              <CompareResultCard result={compareResult} />
            ) : (
              <Card className="border-dashed h-full bg-muted/20">
                <CardContent className="flex flex-col items-center justify-center gap-3 h-full py-16 text-center">
                  <EmptyState
                    icon={<Trophy className="size-8 text-muted-foreground" />}
                    title="Karşılaştırma sonucu bekleniyor"
                    desc="İki CV yükleyin ve bir iş ilanı girerek karşılaştırma analizini başlatın. Karar gerekçesi ve detaylı skorlar burada listelenecektir."
                  />
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </section>
    </div>
  )
}

// ─── Özel Görselleştirme: Radar Grafiği (Pure SVG) ──────────────────────────
function SkillRadarChart({ skills }: { skills: string[] }) {
  const safeSkills = Array.isArray(skills) ? skills : []
  const text = safeSkills.join(" ").toLowerCase()
  
  const axesDef = {
    "Programlama": ["python", "sql", "c#", "c", "javascript", "java", "typescript", "go", "php"],
    "AI / Veri": ["machine learning", "deep learning", "nlp", "rag", "llm", "pandas", "numpy", "scikit", "tensor"],
    "Web": ["html", "css", "streamlit", "react", "django", "flask", "node", "next"],
    "Araçlar": ["git", "github", "linux", "docker", "vector", "database", "aws", "azure"],
    "Test": ["pytest", "unittest", "test", "automation", "jest", "cypress"]
  }

  const data = Object.entries(axesDef).map(([subject, keywords]) => {
    const matched = keywords.filter(k => text.includes(k)).length
    const score = Math.min(100, Math.round((matched / Math.max(keywords.length / 2, 1)) * 100))
    return { subject, score: score || 15 } 
  })

  const size = 300
  const center = size / 2
  const maxRadius = 100
  const angleStep = (Math.PI * 2) / data.length

  const getCoordinates = (value: number, index: number) => {
    const r = (value / 100) * maxRadius
    const angle = index * angleStep - Math.PI / 2
    return { x: center + r * Math.cos(angle), y: center + r * Math.sin(angle) }
  }

  const polygonPoints = data.map((d, i) => `${getCoordinates(d.score, i).x},${getCoordinates(d.score, i).y}`).join(" ")

  return (
    <div className="flex justify-center items-center w-full">
      <svg viewBox={`0 0 ${size} ${size}`} className="w-full max-w-[300px] h-auto overflow-visible">
        {[20, 40, 60, 80, 100].map(p => {
          const pts = data.map((_, i) => `${getCoordinates(p, i).x},${getCoordinates(p, i).y}`).join(" ")
          return <polygon key={p} points={pts} fill="none" stroke="currentColor" className="text-muted-foreground/20 stroke-[1.5]" />
        })}
        
        {data.map((d, i) => {
          const ptEnd = getCoordinates(100, i)
          const angle = i * angleStep - Math.PI / 2
          const labelRadius = maxRadius + 24
          const labelX = center + labelRadius * Math.cos(angle)
          const labelY = center + labelRadius * Math.sin(angle)
          
          return (
            <g key={d.subject}>
              <line x1={center} y1={center} x2={ptEnd.x} y2={ptEnd.y} stroke="currentColor" className="text-muted-foreground/30 stroke-[1.5]" />
              <text 
                x={labelX} 
                y={labelY} 
                textAnchor="middle" 
                dominantBaseline="middle" 
                className="text-[11px] font-bold fill-muted-foreground"
              >
                {d.subject}
              </text>
            </g>
          )
        })}

        <polygon points={polygonPoints} className="fill-primary/20 stroke-primary stroke-[2.5]" />
        
        {data.map((d, i) => {
          const pt = getCoordinates(d.score, i)
          return <circle key={i} cx={pt.x} cy={pt.y} r={4} className="fill-background stroke-primary stroke-[2]" />
        })}
      </svg>
    </div>
  )
}

// ─── Özel Görselleştirme: Deneyim Zaman Çizelgesi (YENİLENMİŞ MATEMATİK) ──────
function ExperienceTimeline({ experiences }: { experiences: any[] }) {
  const safeExperiences = Array.isArray(experiences) ? experiences : []
  const validExps = safeExperiences.filter(e => e && typeof e === 'object' && e.baslangic != null && !isNaN(Number(e.baslangic)))
  
  if (validExps.length === 0) {
    return <div className="text-sm text-muted-foreground text-center py-10">Zaman çizelgesi için uygun formatta deneyim tarihi bulunamadı.</div>
  }

  const currentYear = new Date().getFullYear()
  const rawMinYear = Math.min(...validExps.map(e => Number(e.baslangic)))
  const rawMaxYear = Math.max(...validExps.map(e => e.bitis && !isNaN(Number(e.bitis)) ? Number(e.bitis) : currentYear))
  
  // Eksene pay (padding) bırakıyoruz ki barlar uçlara yapışıp %100 genişlik almasın.
  const displayMinYear = rawMinYear - 1
  const displayMaxYear = rawMaxYear + 1
  const span = Math.max(displayMaxYear - displayMinYear, 1)

  return (
    <div className="space-y-5 py-4 px-2">
      {validExps.map((exp, i) => {
        const start = Number(exp.baslangic)
        const end = exp.bitis && !isNaN(Number(exp.bitis)) ? Number(exp.bitis) : currentYear
        
        // Aynı yıl içinde başlayıp biten işler için "0" hesaplanmasın diye minimum 1 veriyoruz
        const duration = Math.max(end - start, 1)
        
        const left = ((start - displayMinYear) / span) * 100
        const width = (duration / span) * 100

        // Dify'dan gelen "sure_ay" varsa görselde ay olarak gösteriyoruz, yoksa yıl yazıyoruz
        const durationText = exp.sure_ay ? `${exp.sure_ay} ay` : `${duration} yıl`

        return (
          <div key={i} className="relative group">
            <div className="flex justify-between items-end text-xs mb-1.5">
              <span className="font-semibold text-foreground truncate max-w-[80%] pr-2">
                {exp.pozisyon || "Bilinmiyor"} <span className="font-normal text-muted-foreground">- {exp.sirket || "Bilinmiyor"}</span>
              </span>
              <span className="text-muted-foreground font-medium shrink-0">{durationText}</span>
            </div>
            <div className="w-full h-3 bg-muted/50 rounded-full relative overflow-hidden">
              <div
                className="absolute top-0 bottom-0 bg-emerald-400 dark:bg-emerald-500 rounded-full transition-all duration-500 ease-out group-hover:bg-primary"
                style={{ left: `${left}%`, width: `${width}%` }}
              />
            </div>
          </div>
        )
      })}
      
      <div className="flex justify-between text-[11px] font-bold text-muted-foreground pt-3 border-t border-border mt-4">
        <span>{displayMinYear}</span>
        <span>{displayMaxYear}</span>
      </div>
    </div>
  )
}

// ─── Yardımcı Bileşenler ────────────────────────────────────────────────────────
function MetricTile({ icon, value, label }: { icon: React.ReactNode, value: number | string, label: string }) {
  return (
    <Card className="bg-primary/5 border-primary/10">
      <CardContent className="p-4 flex flex-col items-center justify-center text-center">
        <div className="text-primary mb-1 opacity-80">{icon}</div>
        <div className="text-2xl font-black text-foreground">{value}</div>
        <div className="text-[10px] font-bold tracking-wider uppercase text-muted-foreground mt-0.5">{label}</div>
      </CardContent>
    </Card>
  )
}

function CompareResultCard({ result }: { result: CvCompareResult }) {
  const winner = result.kazanan // "cv1" | "cv2"

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {winner && (
        <div className="rounded-xl bg-primary/10 border border-primary/20 p-5 flex items-start gap-4">
          <div className="rounded-full bg-primary/20 p-3 text-primary mt-1">
            <Trophy className="size-6" />
          </div>
          <div>
            <p className="text-sm font-bold text-primary uppercase tracking-wider mb-1">Daha Uygun Aday</p>
            <h4 className="text-xl font-bold text-foreground">{winner === "cv1" ? "Aday 1" : "Aday 2"}</h4>
            {result.karar_gerekcesi && (
              <p className="mt-2 text-sm text-muted-foreground leading-relaxed">{result.karar_gerekcesi}</p>
            )}
          </div>
        </div>
      )}

      <div className="grid gap-4 md:grid-cols-2">
        {(["cv1", "cv2"] as const).map((key, idx) => {
          const candidate = result[key]
          const isWinner = winner === key
          const gucluYonler = Array.isArray(candidate?.guclu_yonler) ? candidate?.guclu_yonler : []
          const zayifYonler = Array.isArray(candidate?.zayif_yonler) ? candidate?.zayif_yonler : []

          return (
            <Card key={key} className={`transition-all ${isWinner ? "border-primary/50 shadow-md shadow-primary/5" : ""}`}>
              <CardContent className="space-y-4 p-6">
                <div className="flex items-center justify-between border-b pb-4">
                  <div>
                    <h4 className="font-bold text-lg">Aday {idx + 1}</h4>
                    {candidate?.isim && <p className="text-sm text-muted-foreground">{candidate.isim}</p>}
                  </div>
                  {candidate?.skor != null && (
                    <div className="flex flex-col items-center justify-center bg-muted/50 rounded-lg px-4 py-2">
                      <span className="text-2xl font-black">{candidate.skor}</span>
                      <span className="text-[10px] font-bold text-muted-foreground uppercase">Skor</span>
                    </div>
                  )}
                </div>

                {gucluYonler.length > 0 && (
                  <div>
                    <p className="mb-2 text-xs font-bold uppercase tracking-wider text-emerald-600 dark:text-emerald-400 flex items-center gap-1.5">
                      <CheckCircle2 className="size-4" /> Güçlü Yönler
                    </p>
                    <ul className="space-y-2">
                      {gucluYonler.map((g, i) => (
                        <li key={i} className="flex items-start gap-2 text-sm text-foreground/80 leading-snug">
                          <span className="text-emerald-500 mt-0.5 font-bold">•</span> {typeof g === 'object' ? JSON.stringify(g) : String(g)}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {zayifYonler.length > 0 && (
                  <div className="pt-2">
                    <p className="mb-2 text-xs font-bold uppercase tracking-wider text-rose-600 dark:text-rose-400 flex items-center gap-1.5">
                      <XCircle className="size-4" /> Gelişim Alanları
                    </p>
                    <ul className="space-y-2">
                      {zayifYonler.map((z, i) => (
                        <li key={i} className="flex items-start gap-2 text-sm text-foreground/80 leading-snug">
                          <span className="text-rose-500 mt-0.5 font-bold">•</span> {typeof z === 'object' ? JSON.stringify(z) : String(z)}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </CardContent>
            </Card>
          )
        })}
      </div>
    </div>
  )
}

function EmptyState({ icon, title, desc }: { icon: React.ReactNode, title: string, desc: string }) {
  return (
    <div className="flex flex-col items-center justify-center gap-4 text-center">
      <span className="flex size-16 items-center justify-center rounded-2xl bg-muted/50 shadow-sm">
        {icon}
      </span>
      <div>
        <p className="text-base font-bold text-foreground">{title}</p>
        <p className="mt-1.5 max-w-sm text-sm text-muted-foreground leading-relaxed">{desc}</p>
      </div>
    </div>
  )
}

function SectionHeading({ step, title, desc, icon: Icon }: { step: string, title: string, desc: string, icon?: React.ElementType }) {
  return (
    <div className="mb-6 border-b border-border pb-4">
      <div className="flex items-center gap-2 mb-1.5">
        {Icon ? <Icon className="size-4 text-primary" /> : null}
        <span className="text-[11px] font-black uppercase tracking-widest text-primary">{step}</span>
      </div>
      <h3 className="text-2xl font-bold tracking-tight text-foreground">{title}</h3>
      <p className="text-sm text-muted-foreground mt-1">{desc}</p>
    </div>
  )
}