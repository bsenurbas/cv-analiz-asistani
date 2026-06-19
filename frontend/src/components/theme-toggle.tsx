import { useEffect, useState } from 'react'
import { useTheme } from 'next-themes'
import { Moon, Sun } from 'lucide-react'
import { cn } from '@/lib/utils'

export function ThemeToggle({ className }: { className?: string }) {
  const { resolvedTheme, setTheme } = useTheme()
  const [mounted, setMounted] = useState(false)
  useEffect(() => setMounted(true), [])
  const isDark = resolvedTheme === 'dark'

  return (
    <button
      type="button"
      aria-label="Toggle theme"
      onClick={() => setTheme(isDark ? 'light' : 'dark')}
      className={cn(
        'group relative inline-flex h-9 w-16 items-center rounded-full border border-border bg-muted/60 px-1 transition-colors hover:bg-muted',
        className,
      )}
    >
      <span
        className={cn(
          'flex size-7 items-center justify-center rounded-full bg-card shadow-sm transition-transform duration-300',
          mounted && isDark ? 'translate-x-7' : 'translate-x-0',
        )}
      >
        {mounted && isDark ? (
          <Moon className="size-4 text-primary" />
        ) : (
          <Sun className="size-4 text-amber" />
        )}
      </span>
    </button>
  )
}