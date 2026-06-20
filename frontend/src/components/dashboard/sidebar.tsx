import { useState, useEffect } from "react"
import {
  Activity,
  BrainCircuit,
  Database,
  FileText,
  Gauge,
  ScanSearch,
  UserCheck,
} from "lucide-react"
import { Card } from "@/components/ui/card"
import { cn } from "@/lib/utils"
import { getSystemMetrics } from "@/lib/api"
import type { SystemMetrics } from "@/lib/api"

export function Sidebar({ className }: { className?: string }) {
  const [metrics, setMetrics] = useState<SystemMetrics | null>(null)

  useEffect(() => {
    async function fetchMetrics() {
      try {
        const data = await getSystemMetrics()
        setMetrics(data)
      } catch (error) {
        console.error("Metrikler yüklenemedi", error)
      }
    }
    fetchMetrics()
    
    // Opsiyonel: Verilerin 30 saniyede bir otomatik güncellenmesi için
    const interval = setInterval(fetchMetrics, 30000)
    return () => clearInterval(interval)
  }, [])

  const statusCards = [
    {
      label: "Veritabanı",
      value: metrics?.veritabani || "—",
      icon: Database,
      accent: metrics?.veritabani === "Bağlı" ? "text-emerald-500" : "text-muted-foreground",
      dot: metrics?.veritabani === "Bağlı" ? "bg-emerald-500" : "bg-muted-foreground/40",
    },
    {
      label: "Toplam CV",
      value: metrics?.toplam_cv || "—",
      icon: FileText,
      accent: "text-muted-foreground",
      dot: "bg-muted-foreground/40",
    },
    {
      label: "AI Modeli",
      value: metrics?.ai_durumu || "—",
      icon: BrainCircuit,
      accent: metrics?.ai_durumu === "Aktif" ? "text-primary" : "text-muted-foreground",
      dot: metrics?.ai_durumu === "Aktif" ? "bg-primary" : "bg-muted-foreground/40",
    },
    {
      label: "İşlem Hızı",
      value: metrics?.hiz || "—",
      icon: Gauge,
      accent: "text-muted-foreground",
      dot: "bg-muted-foreground/40",
    },
  ]

  const summaryRows = [
    { label: "Analiz Edilen", value: metrics?.analiz_yapilan ?? "—", icon: ScanSearch, accent: "text-emerald-500" },
    { label: "Eşleşen", value: metrics?.eslestirilen ?? "—", icon: UserCheck, accent: "text-amber-500" },
  ]

  return (
    <aside className={cn("flex w-full flex-col gap-6 lg:w-80 lg:shrink-0", className)}>
      {/* Branding */}
      <div className="flex items-center gap-3">
        <div className="flex size-10 items-center justify-center rounded-xl bg-primary text-primary-foreground shadow-sm">
          <ScanSearch className="size-5" />
        </div>
        <div className="leading-tight">
          <p className="text-base font-semibold tracking-tight">Yapay Zeka Destekli - CV Asistanı</p>
          <p className="text-xs text-muted-foreground">Bitirme Projesi</p>
        </div>
      </div>

      {/* System Status */}
      <div className="space-y-3">
        <div className="flex items-center gap-2 px-1">
          <Activity className="size-3.5 text-muted-foreground" />
          <h2 className="text-xs font-medium uppercase tracking-wider text-muted-foreground">Sistem Durumu</h2>
        </div>
        <div className="grid grid-cols-2 gap-3">
          {statusCards.map((s) => (
            <Card key={s.label} className="gap-0 border-border/70 p-3">
              <div className="flex items-center justify-between">
                <s.icon className={cn("size-4", s.accent)} />
                <span className={cn("size-1.5 rounded-full shadow-sm", s.dot)} />
              </div>
              <p className="mt-2 text-sm font-semibold leading-none">{s.value}</p>
              <p className="mt-1 text-[11px] text-muted-foreground">{s.label}</p>
            </Card>
          ))}
        </div>
      </div>

      {/* Weekly Summary */}
      <Card className="gap-0 border-border/70 p-4">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold">Aktivite Özeti</h2>
          <span className="rounded-full bg-muted px-2 py-0.5 text-[11px] font-medium text-muted-foreground">
            —
          </span>
        </div>
        <p className="mt-0.5 text-xs text-muted-foreground">Tüm zamanların istatistikleri</p>
        <div className="mt-4 flex flex-col gap-1">
          {summaryRows.map((row) => (
            <div
              key={row.label}
              className="flex items-center justify-between rounded-lg px-2 py-2 transition-colors hover:bg-muted/60"
            >
              <div className="flex items-center gap-2.5">
                <span className="flex size-7 items-center justify-center rounded-md bg-muted">
                  <row.icon className={cn("size-3.5", row.accent)} />
                </span>
                <span className="text-sm text-muted-foreground">{row.label}</span>
              </div>
              <span className="text-sm font-semibold tabular-nums">{row.value}</span>
            </div>
          ))}
        </div>
      </Card>
    </aside>
  )
}