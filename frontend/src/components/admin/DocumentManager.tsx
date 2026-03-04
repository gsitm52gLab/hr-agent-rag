"use client";
import { useEffect, useState } from "react";
import { getDocuments, createDocument, updateDocument, deleteDocument, reindex } from "@/lib/api";
import type { DocumentInfo } from "@/lib/types";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";
import Modal from "@/components/ui/Modal";

export default function DocumentManager() {
  const [documents, setDocuments] = useState<DocumentInfo[]>([]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editing, setEditing] = useState<DocumentInfo | null>(null);
  const [form, setForm] = useState({ filename: "", title: "", content: "" });
  const [reindexing, setReindexing] = useState(false);

  const load = async () => {
    try {
      const data = await getDocuments();
      setDocuments(data);
    } catch { /* ignore */ }
  };

  useEffect(() => { load(); }, []);

  const openCreate = () => {
    setEditing(null);
    setForm({ filename: "", title: "", content: "" });
    setIsModalOpen(true);
  };

  const openEdit = (doc: DocumentInfo) => {
    setEditing(doc);
    setForm({ filename: doc.filename, title: doc.title, content: doc.content });
    setIsModalOpen(true);
  };

  const handleSave = async () => {
    if (editing) {
      await updateDocument(editing.id, { title: form.title, content: form.content });
    } else {
      await createDocument(form);
    }
    setIsModalOpen(false);
    load();
  };

  const handleDelete = async (id: string) => {
    if (!confirm("정말 삭제하시겠습니까?")) return;
    await deleteDocument(id);
    load();
  };

  const handleReindex = async () => {
    setReindexing(true);
    try {
      await reindex();
      alert("재인덱싱 완료!");
    } catch {
      alert("재인덱싱 실패");
    } finally {
      setReindexing(false);
    }
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold text-white">문서 관리</h2>
        <div className="flex gap-2">
          <Button variant="secondary" onClick={handleReindex} disabled={reindexing}>
            {reindexing ? "인덱싱 중..." : "벡터 재인덱싱"}
          </Button>
          <Button onClick={openCreate}>새 문서</Button>
        </div>
      </div>

      <div className="space-y-3">
        {documents.map((doc) => (
          <div
            key={doc.id}
            className="bg-surface border border-surface-border rounded-xl p-4 flex items-center justify-between"
          >
            <div>
              <h3 className="text-white font-medium">{doc.title}</h3>
              <p className="text-gray-500 text-sm">{doc.filename}</p>
            </div>
            <div className="flex gap-2">
              <Button variant="ghost" size="sm" onClick={() => openEdit(doc)}>
                수정
              </Button>
              <Button variant="danger" size="sm" onClick={() => handleDelete(doc.id)}>
                삭제
              </Button>
            </div>
          </div>
        ))}
        {documents.length === 0 && (
          <p className="text-gray-500 text-center py-8">등록된 문서가 없습니다</p>
        )}
      </div>

      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title={editing ? "문서 수정" : "새 문서 추가"}
      >
        <div className="space-y-4">
          {!editing && (
            <div>
              <label className="block text-sm text-gray-400 mb-1">파일명</label>
              <Input
                value={form.filename}
                onChange={(e) => setForm({ ...form, filename: e.target.value })}
                placeholder="09_새규정.md"
              />
            </div>
          )}
          <div>
            <label className="block text-sm text-gray-400 mb-1">제목</label>
            <Input
              value={form.title}
              onChange={(e) => setForm({ ...form, title: e.target.value })}
              placeholder="제1장 새 규정"
            />
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1">내용 (Markdown)</label>
            <textarea
              value={form.content}
              onChange={(e) => setForm({ ...form, content: e.target.value })}
              rows={12}
              className="w-full rounded-xl bg-surface border border-surface-border px-4 py-2.5 text-gray-200 placeholder-gray-500 focus:outline-none focus:border-purple-500 text-sm font-mono"
              placeholder="# 제1장 규정&#10;&#10;## 제1조 (목적)&#10;..."
            />
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="secondary" onClick={() => setIsModalOpen(false)}>
              취소
            </Button>
            <Button onClick={handleSave}>저장</Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
