"use client";

import { useEffect, useState } from "react";

import { api, type ApiKeysConfig } from "@/lib/api";

type FieldDef = {
  key: keyof ApiKeysConfig;
  label: string;
  required?: boolean;
  description: string;
  usedIn: string[];
  cost?: string;
  link?: string;
};

const FIELDS: FieldDef[] = [
  {
    key: "openai_api_key",
    label: "OpenAI API Key",
    required: true,
    description:
      "대본·시나리오·주제 생성, 참조 Shorts 구조 분석, AI 채팅 대본 수정에 사용합니다. Topic Lab의 AI 주제 생성과 Job 채팅 수정도 이 키를 씁니다.",
    usedIn: ["AI 주제 생성", "시나리오 작성", "참조 URL 분석", "채팅 대본 수정"],
    cost: "종량제 (토큰당 과금, 월 1~3만 원 수준부터)",
    link: "https://platform.openai.com/api-keys",
  },
  {
    key: "youtube_api_key",
    label: "YouTube Data API Key",
    required: true,
    description:
      "Topic Lab의 인기 검색어 기반 Shorts 수집에 사용합니다. Google·네이버 키워드로 YouTube를 검색해 최근 7일 인기 Shorts를 가져옵니다. OAuth와는 별도 키입니다.",
    usedIn: ["인기 검색어 TOP 100", "키워드별 Shorts 검색", "참조 영상 메타데이터"],
    cost: "무료 (일일 10,000 units 한도)",
    link: "https://console.cloud.google.com/apis/credentials",
  },
  {
    key: "elevenlabs_api_key",
    label: "ElevenLabs API Key",
    required: true,
    description:
      "AI 음성(TTS) 생성에 사용합니다. 시리즈 캐릭터 대화형 영상에서 캐릭터별 보이스를 합성할 때 필요합니다. Settings에 등록한 elevenlabs_voice_id와 함께 씁니다.",
    usedIn: ["캐릭터 음성 합성", "대화형 시리즈 TTS"],
    cost: "월 구독 + 문자 수 (Creator $22/월부터)",
    link: "https://elevenlabs.io/app/settings/api-keys",
  },
  {
    key: "heygen_api_key",
    label: "HeyGen API Key",
    required: true,
    description:
      "AI 캐릭터 영상(아바타 립싱크) 생성에 사용합니다. 영상 모드가 ai_character일 때 HeyGen 아바타로 말하는 영상을 만듭니다. Character Manager의 heygen_avatar_id와 연동됩니다.",
    usedIn: ["AI 캐릭터 영상", "시리즈 에피소드 렌더", "아바타 립싱크"],
    cost: "종량제 (분당 약 $1, 월 10~40만 원 수준)",
    link: "https://app.heygen.com/settings?nav=API",
  },
  {
    key: "pexels_api_key",
    label: "Pexels API Key",
    description:
      "무료 스톡 영상·이미지를 Job 렌더에 넣을 때 사용합니다. ASSET_STRATEGY=free_only 또는 hybrid일 때 장면별 B-roll로 활용됩니다. 키 없으면 단색 배경으로 대체됩니다.",
    usedIn: ["스톡 B-roll", "free_only 렌더", "장면별 배경 영상"],
    cost: "무료",
    link: "https://www.pexels.com/api/",
  },
  {
    key: "pixabay_api_key",
    label: "Pixabay API Key",
    description:
      "Pexels와 동일하게 무료 스톡 에셋 검색용입니다. Pexels에서 못 찾을 때 fallback으로 사용됩니다. 둘 다 없어도 파이프라인은 동작하지만 영상 품질이 떨어집니다.",
    usedIn: ["스톡 B-roll (보조)", "에셋 fallback"],
    cost: "무료",
    link: "https://pixabay.com/api/docs/",
  },
  {
    key: "youtube_client_id",
    label: "YouTube OAuth Client ID",
    description:
      "YouTube 채널 연동·비공개/공개 업로드에 사용합니다. Google Cloud Console에서 OAuth 2.0 클라이언트 ID입니다. Data API Key와는 용도가 다릅니다.",
    usedIn: ["채널 OAuth 연결", "Shorts 업로드", "채널 정보 조회"],
    cost: "무료",
    link: "https://console.cloud.google.com/apis/credentials",
  },
  {
    key: "youtube_client_secret",
    label: "YouTube OAuth Client Secret",
    description:
      "OAuth Client ID와 쌍으로 사용하는 비밀 키입니다. 서버가 YouTube에 업로드할 때 토큰을 갱신하는 데 필요합니다. .env에 저장하거나 여기서 덮어쓸 수 있습니다.",
    usedIn: ["OAuth 토큰 갱신", "업로드 인증"],
    cost: "무료",
  },
];

const VIDEO_MODE_INFO = {
  ai_character: {
    label: "AI 캐릭터 (HeyGen)",
    description:
      "HeyGen 아바타 + ElevenLabs 음성으로 말하는 캐릭터 영상을 생성합니다. 시리즈 캐릭터·대화형 쇼츠에 적합합니다. HeyGen·ElevenLabs·OpenAI 키가 필요합니다.",
  },
  stock_broll: {
    label: "스톡 B-roll",
    description:
      "Pexels/Pixabay 무료 스톡 영상 + TTS + 자막으로 영상을 만듭니다. AI 캐릭터 없이 빠르고 저렴하게 운영할 때 선택합니다.",
  },
};

function FieldRow({
  field,
  value,
  onChange,
}: {
  field: FieldDef;
  value: string;
  onChange: (v: string) => void;
}) {
  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "minmax(220px, 1fr) minmax(280px, 1.4fr)",
        gap: 20,
        padding: "16px 0",
        borderBottom: "1px solid var(--border)",
        alignItems: "start",
      }}
    >
      <div>
        <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
          <span style={{ fontWeight: 600, fontSize: "0.9rem" }}>{field.label}</span>
          {field.required ? (
            <span className="badge badge-danger" style={{ fontSize: "0.7rem" }}>
              필수
            </span>
          ) : (
            <span className="badge badge-muted" style={{ fontSize: "0.7rem" }}>
              선택
            </span>
          )}
        </div>
        <input
          type="password"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder="키 입력 (변경 없으면 비워두기)"
          style={{
            width: "100%",
            padding: "10px 12px",
            borderRadius: 8,
            border: "1px solid var(--border)",
            background: "var(--bg)",
            color: "inherit",
            fontSize: "0.9rem",
          }}
        />
        {field.link && (
          <a
            href={field.link}
            target="_blank"
            rel="noopener noreferrer"
            style={{ fontSize: "0.75rem", color: "var(--accent)", marginTop: 6, display: "inline-block" }}
          >
            키 발급 페이지 →
          </a>
        )}
      </div>

      <div style={{ fontSize: "0.85rem", lineHeight: 1.65, color: "var(--muted)" }}>
        <p style={{ color: "var(--text)", marginBottom: 8 }}>{field.description}</p>
        <div style={{ marginBottom: 6 }}>
          <strong style={{ color: "var(--text)", fontSize: "0.8rem" }}>사용 기능</strong>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginTop: 4 }}>
            {field.usedIn.map((item) => (
              <span
                key={item}
                style={{
                  padding: "2px 8px",
                  borderRadius: 4,
                  background: "rgba(255,255,255,0.06)",
                  border: "1px solid var(--border)",
                  fontSize: "0.75rem",
                }}
              >
                {item}
              </span>
            ))}
          </div>
        </div>
        {field.cost && (
          <p style={{ fontSize: "0.8rem", marginTop: 4 }}>
            <strong style={{ color: "var(--text)" }}>비용</strong> · {field.cost}
          </p>
        )}
      </div>
    </div>
  );
}

export function ApiKeysForm() {
  const [form, setForm] = useState<ApiKeysConfig | null>(null);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.getApiKeys().then(setForm).catch(() => setError("API 키를 불러오지 못했습니다."));
  }, []);

  if (!form) return <p style={{ color: "var(--muted)" }}>로딩…</p>;

  async function save() {
    setSaving(true);
    setError(null);
    setMessage(null);
    try {
      const updated = await api.updateApiKeys(form);
      setForm(updated);
      setMessage("저장되었습니다.");
    } catch (e) {
      setError(e instanceof Error ? e.message : "저장 실패");
    } finally {
      setSaving(false);
    }
  }

  const modeInfo = VIDEO_MODE_INFO[form.video_mode as keyof typeof VIDEO_MODE_INFO] ?? VIDEO_MODE_INFO.ai_character;

  return (
    <section style={{ marginBottom: 32 }}>
      <h2 style={{ fontSize: "1rem", marginBottom: 8 }}>API 키</h2>
      <p style={{ color: "var(--muted)", fontSize: "0.85rem", marginBottom: 16 }}>
        왼쪽에 키를 입력하고, 오른쪽에서 각 항목의 용도를 확인하세요. 비어 있으면 .env 값을 사용합니다.
      </p>

      <div
        style={{
          background: "var(--surface)",
          border: "1px solid var(--border)",
          borderRadius: 12,
          padding: "0 20px 16px",
        }}
      >
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "minmax(220px, 1fr) minmax(280px, 1.4fr)",
            gap: 20,
            padding: "12px 0",
            borderBottom: "1px solid var(--border)",
            fontSize: "0.75rem",
            fontWeight: 600,
            color: "var(--muted)",
            textTransform: "uppercase",
            letterSpacing: "0.04em",
          }}
        >
          <span>키 입력</span>
          <span>용도 · 기능 설명</span>
        </div>

        {FIELDS.map((field) => (
          <FieldRow
            key={field.key}
            field={field}
            value={(form[field.key] as string) || ""}
            onChange={(v) => setForm({ ...form, [field.key]: v })}
          />
        ))}

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "minmax(220px, 1fr) minmax(280px, 1.4fr)",
            gap: 20,
            padding: "16px 0",
            alignItems: "start",
          }}
        >
          <div>
            <div style={{ fontWeight: 600, fontSize: "0.9rem", marginBottom: 8 }}>영상 모드</div>
            <select
              value={form.video_mode}
              onChange={(e) => setForm({ ...form, video_mode: e.target.value })}
              style={{
                width: "100%",
                padding: "10px 12px",
                borderRadius: 8,
                border: "1px solid var(--border)",
                background: "var(--bg)",
                color: "inherit",
                fontSize: "0.9rem",
              }}
            >
              <option value="ai_character">{VIDEO_MODE_INFO.ai_character.label}</option>
              <option value="stock_broll">{VIDEO_MODE_INFO.stock_broll.label}</option>
            </select>
          </div>
          <div style={{ fontSize: "0.85rem", lineHeight: 1.65, color: "var(--muted)" }}>
            <p style={{ color: "var(--text)", marginBottom: 8 }}>{modeInfo.description}</p>
          </div>
        </div>

        {form.configured && (
          <div
            style={{
              fontSize: "0.8rem",
              color: "var(--muted)",
              padding: "12px 0",
              borderTop: "1px solid var(--border)",
            }}
          >
            <strong style={{ color: "var(--text)" }}>연결 상태</strong> ·{" "}
            {Object.entries(form.configured)
              .map(([k, v]) => `${k}: ${v ? "✓" : "✗"}`)
              .join(" · ")}
          </div>
        )}

        <div style={{ paddingTop: 12 }}>
          <button
            type="button"
            onClick={save}
            disabled={saving}
            style={{
              padding: "10px 16px",
              borderRadius: 8,
              border: "none",
              background: "var(--accent)",
              color: "#fff",
              fontWeight: 600,
              cursor: saving ? "wait" : "pointer",
            }}
          >
            {saving ? "저장 중…" : "API 키 저장"}
          </button>
          {message && <p style={{ color: "var(--success)", fontSize: "0.85rem", marginTop: 8 }}>{message}</p>}
          {error && <p style={{ color: "var(--danger)", fontSize: "0.85rem", marginTop: 8 }}>{error}</p>}
        </div>
      </div>
    </section>
  );
}
