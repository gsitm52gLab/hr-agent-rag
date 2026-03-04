"use client";
import { useEffect, useState } from "react";
import { getGlossary, createGlossary, updateGlossary, deleteGlossary } from "@/lib/api";
import type { GlossaryItem } from "@/lib/types";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";
import Modal from "@/components/ui/Modal";

export default function GlossaryEditor() {
  const [items, setItems] = useState<GlossaryItem[]>([]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editing, setEditing] = useState<GlossaryItem | null>(null);
  const [form, setForm] = useState({ term: "", definition: "", category: "", aliases: "" });
  const [filter, setFilter] = useState("");

  const load = async () => {
    try {
      const data = await getGlossary();
      setItems(data);
    } catch { /* ignore */ }
  };

  useEffect(() => { load(); }, []);

  const openCreate = () => {
    setEditing(null);
    setForm({ term: "", definition: "", category: "", aliases: "" });
    setIsModalOpen(true);
  };

  const openEdit = (item: GlossaryItem) => {
    setEditing(item);
    setForm({ term: item.term, definition: item.definition, category: item.category || "", aliases: item.aliases || "" });
    setIsModalOpen(true);
  };

  const handleSave = async () => {
    if (editing) {
      await updateGlossary(editing.id, form);
    } else {
      await createGlossary(form);
    }
    setIsModalOpen(false);
    load();
  };

  const handleDelete = async (id: number) => {
    if (!confirm("정말 삭제하시겠습니까?")) return;
    await deleteGlossary(id);
    load();
  };

  const filtered = filter
    ? items.filter((i) => i.term.includes(filter) || i.category?.includes(filter) || i.aliases?.includes(filter))
    : items;

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold text-white">용어사전 관리</h2>
        <Button onClick={openCreate}>새 용어</Button>
      </div>

      <div className="mb-4">
        <Input
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          placeholder="용어 검색..."
        />
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-surface-border">
              <th className="text-left py-3 px-4 text-gray-400 font-medium">용어</th>
              <th className="text-left py-3 px-4 text-gray-400 font-medium">설명</th>
              <th className="text-left py-3 px-4 text-gray-400 font-medium">별칭</th>
              <th className="text-left py-3 px-4 text-gray-400 font-medium">카테고리</th>
              <th className="text-right py-3 px-4 text-gray-400 font-medium">작업</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((item) => (
              <tr key={item.id} className="border-b border-surface-border/50 hover:bg-white/5">
                <td className="py-3 px-4 text-white font-medium">{item.term}</td>
                <td className="py-3 px-4 text-gray-300 max-w-md truncate">{item.definition}</td>
                <td className="py-3 px-4 text-gray-400 max-w-xs truncate text-xs">{item.aliases}</td>
                <td className="py-3 px-4">
                  {item.category && (
                    <span className="px-2 py-0.5 rounded-full bg-purple-600/30 text-purple-300 text-xs">
                      {item.category}
                    </span>
                  )}
                </td>
                <td className="py-3 px-4 text-right">
                  <div className="flex justify-end gap-2">
                    <Button variant="ghost" size="sm" onClick={() => openEdit(item)}>
                      수정
                    </Button>
                    <Button variant="danger" size="sm" onClick={() => handleDelete(item.id)}>
                      삭제
                    </Button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {filtered.length === 0 && (
          <p className="text-gray-500 text-center py-8">용어가 없습니다</p>
        )}
      </div>

      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title={editing ? "용어 수정" : "새 용어 추가"}
      >
        <div className="space-y-4">
          <div>
            <label className="block text-sm text-gray-400 mb-1">용어</label>
            <Input
              value={form.term}
              onChange={(e) => setForm({ ...form, term: e.target.value })}
              placeholder="연차휴가"
            />
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1">설명</label>
            <textarea
              value={form.definition}
              onChange={(e) => setForm({ ...form, definition: e.target.value })}
              rows={3}
              className="w-full rounded-xl bg-surface border border-surface-border px-4 py-2.5 text-gray-200 placeholder-gray-500 focus:outline-none focus:border-purple-500 text-sm"
              placeholder="용어에 대한 설명"
            />
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1">별칭 (쉼표로 구분)</label>
            <Input
              value={form.aliases}
              onChange={(e) => setForm({ ...form, aliases: e.target.value })}
              placeholder="야근,초과근무,시간외근무"
            />
            <p className="text-xs text-gray-500 mt-1">사용자가 이 별칭으로 검색하면 해당 용어와 연결됩니다</p>
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1">카테고리</label>
            <Input
              value={form.category}
              onChange={(e) => setForm({ ...form, category: e.target.value })}
              placeholder="휴가"
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
