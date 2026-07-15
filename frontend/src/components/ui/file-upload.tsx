"use client";

import { useState, useRef, useCallback, type DragEvent } from "react";
import { Upload, X, FileText, Image, Film, Music } from "lucide-react";
import { cn } from "@/lib/utils";
import { Spinner } from "./loading";

interface FileUploadProps {
  onUpload: (file: File) => Promise<void>;
  accept?: string;
  maxSizeMB?: number;
  className?: string;
}

const MIME_ICONS: Record<string, typeof FileText> = {
  image: Image,
  video: Film,
  audio: Music,
};

function getIcon(type: string) {
  const category = type.split("/")[0];
  const Icon = MIME_ICONS[category] || FileText;
  return <Icon className="h-8 w-8" />;
}

function formatSize(bytes: number) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function FileUpload({ onUpload, accept, maxSizeMB = 50, className }: FileUploadProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const validate = useCallback(
    (file: File): string | null => {
      if (file.size > maxSizeMB * 1024 * 1024) {
        return `文件不能超过 ${maxSizeMB}MB`;
      }
      return null;
    },
    [maxSizeMB]
  );

  const handleFile = useCallback(
    async (file: File) => {
      setError(null);
      const validationError = validate(file);
      if (validationError) {
        setError(validationError);
        return;
      }
      setSelectedFile(file);
      setUploading(true);
      try {
        await onUpload(file);
        setSelectedFile(null);
      } catch (e) {
        setError(e instanceof Error ? e.message : "上传失败");
      } finally {
        setUploading(false);
      }
    },
    [onUpload, validate]
  );

  const onDragOver = (e: DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };
  const onDragLeave = (e: DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };
  const onDrop = (e: DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  };

  return (
    <div className={className}>
      <div
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        onDrop={onDrop}
        onClick={() => inputRef.current?.click()}
        className={cn(
          "border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-colors",
          isDragging
            ? "border-brand-500 bg-brand-50 dark:bg-brand-950/20"
            : "border-[hsl(var(--border))] hover:border-brand-400"
        )}
      >
        <input
          ref={inputRef}
          type="file"
          accept={accept}
          className="hidden"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) handleFile(file);
            e.target.value = "";
          }}
        />

        {uploading && selectedFile ? (
          <div className="flex flex-col items-center gap-3">
            <Spinner className="h-8 w-8" />
            <div className="flex items-center gap-2 text-sm">
              {getIcon(selectedFile.type)}
              <span>{selectedFile.name}</span>
              <span className="text-[hsl(var(--muted-foreground))]">({formatSize(selectedFile.size)})</span>
            </div>
            <p className="text-sm text-[hsl(var(--muted-foreground))]">上传中...</p>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-2">
            <Upload className="h-8 w-8 text-[hsl(var(--muted-foreground))]" />
            <p className="text-sm font-medium">拖拽文件到此处，或点击选择</p>
            <p className="text-xs text-[hsl(var(--muted-foreground))]">
              最大 {maxSizeMB}MB
            </p>
          </div>
        )}
      </div>

      {error && (
        <div className="mt-2 flex items-center gap-2 text-sm text-red-500">
          <X className="h-4 w-4" />
          {error}
        </div>
      )}
    </div>
  );
}
