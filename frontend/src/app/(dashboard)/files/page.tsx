"use client";

import { useRef, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { formatRelativeTime } from "@/lib/utils";
import { Upload, FileText, Image, Film, Music, File as FileIcon } from "lucide-react";

interface FileRecord {
  id: string;
  file_name: string;
  original_file_name: string;
  mime_type: string;
  file_size: number;
  processing_status: string;
  created_at: string;
}

function formatSize(bytes: number) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1048576) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1048576).toFixed(1)} MB`;
}

function fileIcon(mime: string) {
  if (mime.startsWith("image/")) return <Image className="h-5 w-5 text-green-500" />;
  if (mime.startsWith("video/")) return <Film className="h-5 w-5 text-purple-500" />;
  if (mime.startsWith("audio/")) return <Music className="h-5 w-5 text-orange-500" />;
  if (mime.includes("pdf")) return <FileText className="h-5 w-5 text-red-500" />;
  return <FileIcon className="h-5 w-5 text-blue-500" />;
}

export default function FilesPage() {
  const queryClient = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);

  const { data: files = [] } = useQuery({
    queryKey: ["files"],
    queryFn: () => api.get<FileRecord[]>("/api/files"),
  });

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    try {
      const presign = await api.post<{ file_id: string; upload_url: string; storage_key: string }>(
        "/api/files/presign",
        { file_name: file.name, mime_type: file.type, file_size: file.size }
      );

      await fetch(presign.upload_url, { method: "PUT", body: file, headers: { "Content-Type": file.type } });

      await api.post("/api/files/complete", { file_id: presign.file_id, storage_key: presign.storage_key });

      queryClient.invalidateQueries({ queryKey: ["files"] });
    } catch (err) {
      console.error("Upload failed:", err);
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  return (
    <div className="max-w-3xl mx-auto px-4 py-6 space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold">文件中心</h1>
        <label className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-brand-600 text-white text-sm hover:bg-brand-700 cursor-pointer">
          <Upload className="h-4 w-4" />
          {uploading ? "上传中..." : "上传"}
          <input ref={fileInputRef} type="file" className="hidden" onChange={handleUpload} disabled={uploading} />
        </label>
      </div>

      <div className="space-y-2">
        {files.map((f) => (
          <div key={f.id} className="p-3 rounded-xl bg-[hsl(var(--card))] border text-sm flex items-center gap-3">
            {fileIcon(f.mime_type)}
            <div className="flex-1 min-w-0">
              <p className="font-medium truncate">{f.original_file_name}</p>
              <p className="text-xs text-[hsl(var(--muted-foreground))]">
                {formatSize(f.file_size)} · {formatRelativeTime(f.created_at)}
              </p>
            </div>
            <span className={`text-xs px-1.5 py-0.5 rounded ${
              f.processing_status === "completed" ? "bg-green-100 text-green-700" :
              f.processing_status === "pending" ? "bg-yellow-100 text-yellow-700" :
              "bg-gray-100 text-gray-600"
            }`}>{f.processing_status}</span>
          </div>
        ))}
        {files.length === 0 && (
          <p className="text-center text-sm text-[hsl(var(--muted-foreground))] py-8">暂无文件</p>
        )}
      </div>
    </div>
  );
}
