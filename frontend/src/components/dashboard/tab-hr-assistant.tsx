import { useEffect, useRef, useState } from "react"
import { Bot, SendHorizonal, Sparkles, Trash2, User, Loader2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { cn } from "@/lib/utils"
import { chatWithAssistant } from "@/lib/api"

type Message = { id: number; role: "user" | "assistant"; text: string }

const quickQuestions = [
  "Python geliştiricilerini listele", 
  "Mülakat sorusu öner", 
  "Kıdemli (Senior) rolüne en uygun kim?"
]

export function TabHrAssistant() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState("")
  // API istekleri için yüklenme durumu
  const [isLoading, setIsLoading] = useState(false)
  // Dify üzerindeki sohbet bağlamını korumak için
  const [conversationId, setConversationId] = useState("")
  
  const scrollRef = useRef<HTMLDivElement>(null)
  const idRef = useRef(0)

  // Mesaj eklendikçe otomatik en alta kaydır
  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" })
  }, [messages])

  async function send(text: string) {
    const trimmed = text.trim()
    if (!trimmed) return

    // Kullanıcı mesajını arayüze ekle
    const userMsg: Message = { id: idRef.current++, role: "user", text: trimmed }
    setMessages((m) => [...m, userMsg])
    setInput("")
    setIsLoading(true)

    try {
      // Backend'e API isteği gönder
      const res = await chatWithAssistant(trimmed, conversationId)
      
      // Eğer Dify yeni bir conversation_id döndürdüyse, sonraki istekler için kaydet
      if (res.conversation_id) {
        setConversationId(res.conversation_id)
      }

      // Asistan yanıtını arayüze ekle
      const botMsg: Message = { 
        id: idRef.current++, 
        role: "assistant", 
        text: res.answer || "Yanıt alınamadı." 
      }
      setMessages((m) => [...m, botMsg])

    } catch (error) {
      console.error("Asistan Hatası:", error)
      // Hata durumunda kullanıcıyı bilgilendir
      const errMsg: Message = { 
        id: idRef.current++, 
        role: "assistant", 
        text: "Bir hata oluştu. Lütfen bağlantınızı kontrol edip tekrar deneyin." 
      }
      setMessages((m) => [...m, errMsg])
    } finally {
      setIsLoading(false)
    }
  }

  const hasHistory = messages.length > 0

  return (
    <Card className="overflow-hidden">
      {/* Greeting header */}
      <CardHeader className="border-b border-border bg-muted/30">
        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <span className="flex size-10 items-center justify-center rounded-xl bg-primary/15 text-primary">
              <Bot className="size-5" />
            </span>
            <div>
              <CardTitle className="text-base">Akıllı İK Asistanı</CardTitle>
              <p className="text-sm text-muted-foreground">
                Adaylar hakkında sorular sorun, mülakat soruları hazırlatın veya işe alım önerileri alın.
              </p>
            </div>
          </div>
          {hasHistory ? (
            <Button 
              variant="ghost" 
              size="sm" 
              onClick={() => {
                setMessages([])
                setConversationId("") // Sohbeti temizlerken bağlamı da sıfırla
              }} 
              className="text-muted-foreground"
            >
              <Trash2 className="size-4" /> Sohbeti Temizle
            </Button>
          ) : null}
        </div>

        {/* Quick questions */}
        <div className="mt-3 flex flex-wrap gap-2">
          {quickQuestions.map((q) => (
            <button
              key={q}
              type="button"
              disabled={isLoading}
              onClick={() => send(q)}
              className="inline-flex items-center gap-1.5 rounded-full border border-border bg-background px-3 py-1.5 text-xs font-medium transition-colors hover:border-primary/50 hover:bg-primary/5 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Sparkles className="size-3 text-primary" /> {q}
            </button>
          ))}
        </div>
      </CardHeader>

      <CardContent className="p-0">
        {/* Chat window */}
        <div ref={scrollRef} className="h-[420px] space-y-4 overflow-y-auto p-4">
          {!hasHistory ? (
            <div className="flex h-full flex-col items-center justify-center gap-3 text-center">
              <span className="flex size-14 items-center justify-center rounded-2xl bg-muted">
                <Bot className="size-6 text-muted-foreground" />
              </span>
              <div>
                <p className="text-sm font-medium">Bugün işe alım süreçlerinde nasıl yardımcı olabilirim?</p>
                <p className="mt-1 max-w-sm text-xs text-muted-foreground">
                  Başlamak için yukarıdaki hızlı sorulardan birini seçin veya kendi sorunuzu yazın.
                </p>
              </div>
            </div>
          ) : null}

          {messages.map((m) => (
            <div key={m.id} className={cn("flex items-end gap-2.5", m.role === "user" ? "justify-end" : "justify-start")}>
              {m.role === "assistant" ? (
                <span className="flex size-8 shrink-0 items-center justify-center rounded-full bg-primary/15 text-primary">
                  <Bot className="size-4" />
                </span>
              ) : null}
              <div
                className={cn(
                  "max-w-[78%] whitespace-pre-line rounded-2xl px-4 py-2.5 text-sm leading-relaxed",
                  m.role === "user"
                    ? "rounded-br-md bg-primary text-primary-foreground"
                    : "rounded-bl-md bg-muted text-foreground",
                )}
              >
                {m.text}
              </div>
              {m.role === "user" ? (
                <span className="flex size-8 shrink-0 items-center justify-center rounded-full bg-muted text-muted-foreground">
                  <User className="size-4" />
                </span>
              ) : null}
            </div>
          ))}

          {/* Loading Indicator */}
          {isLoading && (
            <div className="flex items-end gap-2.5 justify-start animate-in fade-in duration-300">
              <span className="flex size-8 shrink-0 items-center justify-center rounded-full bg-primary/15 text-primary">
                <Bot className="size-4" />
              </span>
              <div className="max-w-[78%] rounded-2xl px-4 py-3.5 bg-muted text-foreground flex items-center gap-2">
                <Loader2 className="size-4 animate-spin text-muted-foreground" />
                <span className="text-xs text-muted-foreground">Asistan düşünüyor...</span>
              </div>
            </div>
          )}
        </div>

        {/* Input bar */}
        <div className="border-t border-border bg-muted/30 p-3">
          <form
            onSubmit={(e) => {
              e.preventDefault()
              send(input)
            }}
            className="flex items-center gap-2"
          >
            <Input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="İK asistanına bir soru sorun..."
              className="bg-background"
              disabled={isLoading}
            />
            <Button 
              type="submit" 
              size="icon" 
              disabled={!input.trim() || isLoading} 
              aria-label="Mesaj gönder"
            >
              {isLoading ? <Loader2 className="size-4 animate-spin" /> : <SendHorizonal className="size-4" />}
            </Button>
          </form>
        </div>
      </CardContent>
    </Card>
  )
}