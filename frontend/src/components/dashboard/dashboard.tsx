import { Bot, FileText, Link2, Sparkles } from 'lucide-react'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { ThemeToggle } from '@/components/theme-toggle'
import { Sidebar } from '@/components/dashboard/sidebar'
import { TabCvAnalysis } from '@/components/dashboard/tab-cv-analysis'
import { TabJobMatching } from '@/components/dashboard/tab-job-matching'
import { TabHrAssistant } from '@/components/dashboard/tab-hr-assistant'

const tabs = [
  { value: 'analysis', label: 'CV Analizi', icon: FileText },
  { value: 'matching', label: 'İş İlanı Eşleştirme', icon: Link2 },
  { value: 'assistant', label: 'İK Asistanı', icon: Bot },
]

export function Dashboard() {
  return (
    <div className="mx-auto flex max-w-[1400px] flex-col gap-6 px-4 py-6 lg:flex-row lg:px-6 lg:py-8">
      <Sidebar />
      <main className="min-w-0 flex-1 space-y-6">
        <div className="flex items-center justify-end">
          <ThemeToggle />
        </div>
        <section className="relative overflow-hidden rounded-2xl border border-border bg-card p-6 sm:p-8">
          <div className="pointer-events-none absolute -right-16 -top-16 size-64 rounded-full bg-primary/10 blur-3xl" />
          <div className="relative">
            <span className="inline-flex items-center gap-1.5 rounded-full border border-primary/30 bg-primary/10 px-3 py-1 text-xs font-medium text-primary">
              <Sparkles className="size-3" /> YAPAY ZEKA DESTEKLİ
            </span>
            <h1 className="mt-4 text-balance text-2xl font-semibold tracking-tight sm:text-3xl lg:text-4xl">
              Yapay Zeka Destekli - CV Analiz Sistemi & Akıllı İK Paneli
            </h1>
            <p className="mt-2 max-w-2xl text-pretty text-sm leading-relaxed text-muted-foreground sm:text-base">
              Özgeçmişleri yükleyin, TF-IDF ve anlamsal yapay zeka ile adayları iş ilanlarıyla eşleştirin ve akıllı İK asistanıyla sohbet edin - hepsi tek bir modern çalışma alanında.
            </p>
          </div>
        </section>
        <Tabs defaultValue="analysis" className="gap-6">
          <TabsList className="h-auto w-full justify-start gap-1 overflow-x-auto rounded-xl bg-muted/60 p-1 sm:w-auto">
            {tabs.map((t) => (
              <TabsTrigger key={t.value} value={t.value} className="gap-2 px-4 py-2">
                <t.icon className="size-4" /> {t.label}
              </TabsTrigger>
            ))}
          </TabsList>
          <TabsContent value="analysis" className="mt-0"><TabCvAnalysis /></TabsContent>
          <TabsContent value="matching" className="mt-0"><TabJobMatching /></TabsContent>
          <TabsContent value="assistant" className="mt-0"><TabHrAssistant /></TabsContent>
        </Tabs>
      </main>
    </div>
  )
}