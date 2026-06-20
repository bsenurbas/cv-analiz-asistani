import { useCallback } from "react"
import { useDropzone } from "react-dropzone"
import { UploadCloud, FileText } from "lucide-react"
import { cn } from "@/lib/utils"

interface FileDropzoneProps {
  id: string
  label?: string
  fileName: string | null
  onFile: (file: File | null) => void
  compact?: boolean
}

export function FileDropzone({
  id,
  label,
  fileName,
  onFile,
  compact = false,
}: FileDropzoneProps) {
  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      if (acceptedFiles && acceptedFiles.length > 0) {
        onFile(acceptedFiles[0])
      }
    },
    [onFile]
  )

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "application/pdf": [".pdf"],
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
    },
    multiple: false,
  })

  return (
    <div className="w-full">
      {label && <p className="mb-2 text-sm font-medium">{label}</p>}
      <div
        {...getRootProps()}
        className={cn(
          "flex flex-col items-center justify-center rounded-xl border border-dashed border-border bg-muted/30 p-6 text-center transition-colors hover:bg-muted/50 cursor-pointer select-none",
          isDragActive && "border-primary bg-primary/5",
          compact ? "py-6" : "py-10"
        )}
      >
        <input {...getInputProps()} id={id} />
        {fileName ? (
          <div className="flex flex-col items-center gap-2 animate-in fade-in duration-200">
            <span className="flex size-10 items-center justify-center rounded-lg bg-primary/10 text-primary">
              <FileText className="size-5" />
            </span>
            <p className="text-sm font-medium max-w-[200px] truncate text-foreground">
              {fileName}
            </p>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-2">
            <span className="flex size-10 items-center justify-center rounded-lg bg-muted-foreground/10 text-muted-foreground">
              <UploadCloud className="size-5" />
            </span>
            <div>
              <p className="text-sm font-medium">
                {compact ? "CV Yükleyin" : "CV Yükleyin"}
              </p>
              {!compact && (
                <p className="mt-1 text-xs text-muted-foreground">
                  PDF veya DOCX yükleyiniz, en fazla 10MB
                </p>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}