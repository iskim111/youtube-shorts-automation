"use client";

import { FormEvent, useEffect, useState } from "react";

import { api, type Character } from "@/lib/api";

const EMPTY_FORM = {
  name: "",
  role: "",
  heygen_avatar_id: "",
  elevenlabs_voice_id: "",
  speech_style: "",
  language_primary: "ko",
};

export function CharacterManager() {
  const [chars, setChars] = useState<Character[]>([]);
  const [saving, setSaving] = useState<string | null>(null);
  const [adding, setAdding] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [newChar, setNewChar] = useState(EMPTY_FORM);
  const [error, setError] = useState<string | null>(null);

  function load() {
    api.characters().then(setChars).catch(() => setError("캐릭터 목록 로드 실패"));
  }

  useEffect(() => {
    load();
  }, []);

  async function save(char: Character) {
    setSaving(char.code);
    setError(null);
    try {
      await api.updateCharacter(char.code, {
        name: char.name,
        role: char.role,
        heygen_avatar_id: char.heygen_avatar_id,
        elevenlabs_voice_id: char.elevenlabs_voice_id,
        speech_style: char.speech_style,
        language_primary: char.language_primary,
        is_active: char.is_active,
      });
      load();
    } catch {
      setError("저장 실패");
    } finally {
      setSaving(null);
    }
  }

  async function handleAdd(e: FormEvent) {
    e.preventDefault();
    if (!newChar.name.trim() || !newChar.role.trim()) return;
    setAdding(true);
    setError(null);
    try {
      await api.createCharacter({
        name: newChar.name.trim(),
        role: newChar.role.trim(),
        heygen_avatar_id: newChar.heygen_avatar_id.trim(),
        elevenlabs_voice_id: newChar.elevenlabs_voice_id.trim(),
        speech_style: newChar.speech_style.trim(),
        language_primary: newChar.language_primary || "ko",
      });
      setNewChar(EMPTY_FORM);
      setShowForm(false);
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message.replace(/^API error: \d+ /, "") : "추가 실패");
    } finally {
      setAdding(false);
    }
  }

  async function deactivate(char: Character) {
    if (!confirm(`「${char.name}」을(를) 비활성화할까요?`)) return;
    setSaving(char.code);
    try {
      await api.updateCharacter(char.code, { is_active: false });
      load();
    } catch {
      setError("비활성화 실패");
    } finally {
      setSaving(null);
    }
  }

  function updateLocal(code: string, patch: Partial<Character>) {
    setChars((prev) => prev.map((x) => (x.code === code ? { ...x, ...patch } : x)));
  }

  const activeChars = chars.filter((c) => c.is_active);
  const inactiveChars = chars.filter((c) => !c.is_active);

  return (
    <section style={{ marginBottom: 32 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
        <h2 style={{ fontSize: "1rem", margin: 0 }}>AI 캐릭터 (주인공)</h2>
        <button
          type="button"
          onClick={() => setShowForm((v) => !v)}
          style={{
            padding: "8px 14px",
            borderRadius: 8,
            border: "none",
            background: "var(--accent)",
            color: "#fff",
            fontWeight: 600,
            cursor: "pointer",
            fontSize: "0.85rem",
          }}
        >
          {showForm ? "취소" : "+ 주인공 추가"}
        </button>
      </div>
      <p style={{ color: "var(--muted)", fontSize: "0.85rem", marginBottom: 16 }}>
        주인공을 추가하고 HeyGen Avatar ID · ElevenLabs Voice ID를 등록하면 시리즈에 고정 적용됩니다.
      </p>

      {error && <p style={{ color: "var(--danger)", marginBottom: 12 }}>{error}</p>}

      {showForm && (
        <form
          onSubmit={handleAdd}
          style={{
            padding: 16,
            marginBottom: 20,
            background: "var(--surface)",
            border: "1px solid var(--accent)",
            borderRadius: 12,
            display: "grid",
            gap: 10,
          }}
        >
          <div style={{ fontWeight: 600, marginBottom: 4 }}>새 주인공</div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
            <input
              required
              placeholder="이름 (예: 순자 할머니)"
              value={newChar.name}
              onChange={(e) => setNewChar({ ...newChar, name: e.target.value })}
              style={inputStyle}
            />
            <input
              required
              placeholder="역할 (예: grandmother, youth, host)"
              value={newChar.role}
              onChange={(e) => setNewChar({ ...newChar, role: e.target.value })}
              style={inputStyle}
            />
          </div>
          <input
            placeholder="HeyGen Avatar ID"
            value={newChar.heygen_avatar_id}
            onChange={(e) => setNewChar({ ...newChar, heygen_avatar_id: e.target.value })}
            style={inputStyle}
          />
          <input
            placeholder="ElevenLabs Voice ID"
            value={newChar.elevenlabs_voice_id}
            onChange={(e) => setNewChar({ ...newChar, elevenlabs_voice_id: e.target.value })}
            style={inputStyle}
          />
          <input
            placeholder="말투 규칙 (예: 따뜻한 존댓말)"
            value={newChar.speech_style}
            onChange={(e) => setNewChar({ ...newChar, speech_style: e.target.value })}
            style={inputStyle}
          />
          <select
            value={newChar.language_primary}
            onChange={(e) => setNewChar({ ...newChar, language_primary: e.target.value })}
            style={inputStyle}
          >
            <option value="ko">한국어</option>
            <option value="en">영어</option>
            <option value="mixed">한국어+영어</option>
          </select>
          <button
            type="submit"
            disabled={adding}
            style={{
              padding: "10px 16px",
              borderRadius: 8,
              border: "none",
              background: "var(--accent)",
              color: "#fff",
              fontWeight: 600,
              cursor: adding ? "wait" : "pointer",
              width: "fit-content",
            }}
          >
            {adding ? "추가 중…" : "주인공 등록"}
          </button>
        </form>
      )}

      <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
        {activeChars.map((c) => (
          <CharacterCard
            key={c.code}
            char={c}
            saving={saving === c.code}
            onChange={(patch) => updateLocal(c.code, patch)}
            onSave={() => save(c)}
            onDeactivate={() => deactivate(c)}
          />
        ))}
        {activeChars.length === 0 && !showForm && (
          <p style={{ color: "var(--muted)", fontSize: "0.9rem" }}>등록된 주인공이 없습니다. 위에서 추가하세요.</p>
        )}
      </div>

      {inactiveChars.length > 0 && (
        <details style={{ marginTop: 20 }}>
          <summary style={{ cursor: "pointer", color: "var(--muted)", fontSize: "0.85rem" }}>
            비활성 캐릭터 ({inactiveChars.length})
          </summary>
          <div style={{ display: "flex", flexDirection: "column", gap: 12, marginTop: 12 }}>
            {inactiveChars.map((c) => (
              <div key={c.code} style={{ padding: 12, color: "var(--muted)", fontSize: "0.85rem" }}>
                {c.name} ({c.role})
                <button
                  type="button"
                  style={{ marginLeft: 12, fontSize: "0.8rem", cursor: "pointer" }}
                  onClick={() => {
                    updateLocal(c.code, { is_active: true });
                    save({ ...c, is_active: true });
                  }}
                >
                  다시 활성화
                </button>
              </div>
            ))}
          </div>
        </details>
      )}
    </section>
  );
}

function CharacterCard({
  char: c,
  saving,
  onChange,
  onSave,
  onDeactivate,
}: {
  char: Character;
  saving: boolean;
  onChange: (patch: Partial<Character>) => void;
  onSave: () => void;
  onDeactivate: () => void;
}) {
  return (
    <div
      style={{
        padding: 16,
        background: "var(--surface)",
        border: "1px solid var(--border)",
        borderRadius: 12,
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 10 }}>
        <span style={{ fontSize: "0.75rem", color: "var(--muted)" }}>{c.code}</span>
        <button
          type="button"
          onClick={onDeactivate}
          style={{
            fontSize: "0.75rem",
            color: "var(--muted)",
            background: "none",
            border: "none",
            cursor: "pointer",
            textDecoration: "underline",
          }}
        >
          비활성화
        </button>
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8, marginBottom: 8 }}>
        <input
          placeholder="이름"
          value={c.name}
          onChange={(e) => onChange({ name: e.target.value })}
          style={inputStyle}
        />
        <input
          placeholder="역할 (grandmother, youth, host…)"
          value={c.role}
          onChange={(e) => onChange({ role: e.target.value })}
          style={inputStyle}
        />
      </div>
      <div style={{ display: "grid", gap: 8 }}>
        <input
          placeholder="HeyGen Avatar ID"
          value={c.heygen_avatar_id}
          onChange={(e) => onChange({ heygen_avatar_id: e.target.value })}
          style={inputStyle}
        />
        <input
          placeholder="ElevenLabs Voice ID"
          value={c.elevenlabs_voice_id}
          onChange={(e) => onChange({ elevenlabs_voice_id: e.target.value })}
          style={inputStyle}
        />
        <input
          placeholder="말투 규칙"
          value={c.speech_style}
          onChange={(e) => onChange({ speech_style: e.target.value })}
          style={inputStyle}
        />
        <button
          type="button"
          onClick={onSave}
          disabled={saving}
          style={{
            padding: "8px 12px",
            borderRadius: 8,
            border: "none",
            background: "var(--accent)",
            color: "#fff",
            cursor: saving ? "wait" : "pointer",
            width: "fit-content",
          }}
        >
          {saving ? "저장 중…" : "저장"}
        </button>
      </div>
    </div>
  );
}

const inputStyle: React.CSSProperties = {
  padding: "8px 12px",
  borderRadius: 8,
  border: "1px solid var(--border)",
  background: "var(--bg)",
  color: "inherit",
};
