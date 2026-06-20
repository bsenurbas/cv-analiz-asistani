import { useState, useEffect } from "react"
import { BrainCircuit, Clock, Inbox, Search, Sparkles, Loader2, AlertCircle, CheckCircle2, Zap, XCircle } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Textarea } from "@/components/ui/textarea"
import { matchJobs, getMatchingHistory } from "@/lib/api"
import type { MatchingResult, HistoryRecord } from "@/lib/api"

function EmptyPanel({ message }: { message: string }) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 py-12 text-center">
      <span className="flex size-12 items-center justify-center rounded-2xl bg-muted/50">
        <Inbox className="size-5 text-muted-foreground" />
      </span>
      <p className="max-w-xs text-xs text-muted-foreground leading-relaxed">{message}</p>
    </div>
  )
}

export function TabJobMatching() {
  const [jobDesc, setJobDesc] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [result, setResult] = useState<MatchingResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [history, setHistory] = useState<HistoryRecord[]>([])

  const loadHistory = async () => {
    try {
      const hist = await getMatchingHistory()
      setHistory(hist)
    } catch (e) {
      console.error("Geçmiş çekilemedi", e)
    }
  }

  useEffect(() => {
    loadHistory()
  }, [])

  const handleMatch = async () => {
    if (!jobDesc.trim()) return
    
    setIsLoading(true)
    setError(null)
    setResult(null)

    try {
      let data = await matchJobs(jobDesc)
      
      if ((data as any)?.data?.outputs?.eslesme_sonucu) {
        const rawStr = (data as any).data.outputs.eslesme_sonucu
        const cleanStr = rawStr.replace(/```json/g, "").replace(/```/g, "").trim()
        data = { ...data, ...JSON.parse(cleanStr) }
      } else if (typeof data === 'string') {
        data = JSON.parse((data as string).replace(/```json/g, "").replace(/```/g, "").trim())
      }

      setResult(data)
      await loadHistory() 
    } catch (err: unknown) {
      console.error("Eşleştirme Hatası:", err)
      const msg = err instanceof Error ? err.message : "Eşleştirme sırasında bilinmeyen bir hata oluştu."
      setError(msg)
    } finally {
      setIsLoading(false)
    }
  }

  const safeAdaylar = Array.isArray(result?.adaylar) ? result.adaylar : []
  const safeTfIdf = Array.isArray(result?.tfidf_sonuclari) ? result.tfidf_sonuclari : []

  return (
    <div className="space-y-8 pb-10">
      
      <section>
        <div className="mb-4">
          <div className="flex items-center gap-2 mb-1.5">
            <span className="text-[11px] font-black uppercase tracking-widest text-primary">ADIM 2</span>
          </div>
          <h3 className="text-2xl font-bold tracking-tight text-foreground">İş İlanı - CV Uyum Analizi</h3>
        </div>

        <Card className="hover:border-primary/20 transition-colors">
          <CardContent className="space-y-4 p-6">
            <Textarea
              value={jobDesc}
              onChange={(e) => setJobDesc(e.target.value)}
              placeholder="İş İlanı Metnini Buraya Yapıştırın. Örn: En az 3 yıl deneyimli, Python ve SQL bilen veri mühendisi aranıyor..."
              className="min-h-36 resize-none bg-muted/30"
              disabled={isLoading}
            />
            <Button 
              onClick={handleMatch} 
              disabled={!jobDesc.trim() || isLoading} 
              size="lg"
              className="w-full sm:w-auto"
            >
              {isLoading ? (
                <><Loader2 className="size-4 animate-spin" /> Aday havuzunda tarama yapılıyor…</>
              ) : (
                <><Search className="size-4" /> En Uygun Adayları Getir</>
              )}
            </Button>
            
            {error && (
              <div className="flex items-center gap-2 mt-2 text-sm text-destructive bg-destructive/10 p-3 rounded-md animate-in fade-in">
                <AlertCircle className="size-4 shrink-0" />
                <span>{error}</span>
              </div>
            )}
          </CardContent>
        </Card>
      </section>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader className="border-b border-border bg-muted/20 pb-4">
            <CardTitle className="flex items-center gap-2 text-sm uppercase tracking-wider font-bold">
              <Sparkles className="size-4 text-primary" /> TF-IDF · VEKTÖREL ANALİZ
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-6">
            {result ? (
              safeTfIdf.length > 0 ? (
                <div className="space-y-5 animate-in fade-in duration-300">
                  {safeTfIdf.map((item, idx) => (
                    <div key={idx} className="space-y-1.5">
                      <div className="flex justify-between items-end">
                        <span className="font-bold text-sm text-foreground">
                          CV #{item.cv_id}
                        </span>
                        <span className="text-primary font-bold text-sm">{item.skor}%</span>
                      </div>
                      <div className="text-xs text-muted-foreground mb-2">
                        {item.kategori}
                      </div>
                      <div className="w-full h-2 bg-muted/60 rounded-full overflow-hidden">
                        <div 
                          className="h-full bg-primary transition-all duration-1000 ease-out rounded-full"
                          style={{ width: `${item.skor}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <EmptyPanel message="TF-IDF analizi sonucu döndürülmedi (CSV veritabanı bulunamamış olabilir)." />
              )
            ) : (
              <EmptyPanel message="Anahtar kelime eşleşmeleri sonuçları getirdiğinizde burada görünecektir." />
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="border-b border-border bg-muted/20 pb-4">
            <CardTitle className="flex items-center gap-2 text-sm uppercase tracking-wider font-bold">
              <BrainCircuit className="size-4 text-emerald-500" /> LLM · ANLAMSAL ANALİZ
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-6">
            {result ? (
              safeAdaylar.length > 0 ? (
                <div className="space-y-4 animate-in fade-in duration-300">
                  {safeAdaylar.map((aday, idx) => {
                    const skor = Number(aday.skor) || 0
                    const isRecommended = skor >= 70
                    const isPotential = skor >= 50 && skor < 70
                    
                    let badgeClass = "bg-rose-500/10 text-rose-600 border-rose-500/20"
                    let badgeIcon = <XCircle className="size-3" />
                    let badgeText = "Uygun Değil"
                    
                    if (isRecommended) {
                      badgeClass = "bg-emerald-500/10 text-emerald-600 border-emerald-500/20"
                      badgeIcon = <CheckCircle2 className="size-3" />
                      badgeText = "Önerilir"
                    } else if (isPotential) {
                      badgeClass = "bg-amber-500/10 text-amber-600 border-amber-500/20"
                      badgeIcon = <Zap className="size-3" />
                      badgeText = "Potansiyel"
                    }

                    return (
                      <div key={idx} className="border-b border-border pb-4 last:border-0 last:pb-0">
                        <div className="flex items-start justify-between mb-2">
                          <h4 className="font-bold text-foreground text-sm flex items-center gap-2">
                            Aday {idx + 1} <span className="text-muted-foreground font-normal">| {aday.aday_id || `#ID-${idx+1}`}</span>
                          </h4>
                          <span className={`flex items-center gap-1.5 border px-2.5 py-0.5 rounded-full text-xs font-bold ${badgeClass}`}>
                            {badgeIcon} {badgeText} · {skor}/100
                          </span>
                        </div>
                        {aday.gerekce && (
                          <p className="text-[13px] text-muted-foreground leading-relaxed">
                            {aday.gerekce}
                          </p>
                        )}
                      </div>
                    )
                  })}
                </div>
              ) : (
                <EmptyPanel message="Bu iş ilanı için uygun aday bulunamadı veya sonuç boş döndü." />
              )
            ) : (
              <EmptyPanel message="Aday havuzunda arama yaptığınızda anlamsal sonuçlar burada listelenecektir." />
            )}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader className="border-b border-border bg-muted/20 pb-4">
          <CardTitle className="flex items-center gap-2 text-sm uppercase tracking-wider font-bold">
            <Clock className="size-4 text-amber-500" /> GEÇMİŞ EŞLEŞTİRMELER
          </CardTitle>
        </CardHeader>
        <CardContent className="pt-0 p-0">
          <Table>
            <TableHeader>
              <TableRow className="hover:bg-transparent">
                <TableHead className="w-[180px] pl-6 font-semibold">Tarih</TableHead>
                <TableHead className="font-semibold">İş İlanı Özeti</TableHead>
                <TableHead className="font-semibold text-center w-[200px]">En İyi Aday</TableHead>
                <TableHead className="text-right pr-6 font-semibold w-[120px]">Süre</TableHead>
              </TableRow>
            </TableHeader>
<TableBody>
              {history.length > 0 ? (
                history.map((kayit, index) => {
                  // Güvenli veri çekimi (Eski ve Yeni JSON formatını destekler)
                  const ilanText = kayit["İlan"] || kayit["İlan Metni"] || "İlan metni yok"
                  const sureText = kayit["Süre"] || kayit["Sure"] || "-"
                  
                  // Aday gösterimi için mantık
                  let badgeContent = "Sonuç Yok"
                  if (kayit["Aday ID"]) {
                    // Eski formattaysa en iyi adayı göster
                    badgeContent = `ID: ${kayit["Aday ID"]} • ${kayit["Skor"]}`
                  } else if (kayit["Aday Sayısı"]) {
                    // Yeni formattaysa taranan aday sayısını göster
                    badgeContent = `${kayit["Aday Sayısı"]} Aday Analiz Edildi`
                  }

                  return (
                    <TableRow key={index} className="animate-in fade-in slide-in-from-bottom-2">
                      <TableCell className="pl-6 text-xs text-muted-foreground whitespace-nowrap">
                        {kayit["Tarih"]}
                      </TableCell>
                      <TableCell className="text-sm font-medium">
                        <div className="line-clamp-1 max-w-[400px]" title={ilanText}>
                          {ilanText}
                        </div>
                      </TableCell>
                      <TableCell className="text-center">
                        <span className="inline-flex items-center justify-center rounded-full bg-primary/10 px-3 py-1 text-[11px] font-bold text-primary whitespace-nowrap">
                          {badgeContent}
                        </span>
                      </TableCell>
                      <TableCell className="text-right pr-6 text-xs text-muted-foreground whitespace-nowrap">
                        {sureText}
                      </TableCell>
                    </TableRow>
                  )
                })
              ) : (
                <TableRow>
                  <TableCell colSpan={4} className="py-12 text-center text-sm text-muted-foreground">
                    Henüz kaydedilmiş bir eşleştirme geçmişi bulunmuyor.
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

    </div>
  )
}