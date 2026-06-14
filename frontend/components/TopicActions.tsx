"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { api } from "@/lib/api";

type Props = {
  topicId: string;
  status: string;
};

export function TopicActions({ topicId, status }: Props) {
  const router = useRouter();
  const [loading, setLoading] = useState(false);

  if (!["recommended", "generated", "review_required"].includes(status)) {
    return <span className="badge badge-muted">{status}</span>;
  }

  async function handleApprove() {
    setLoading(true);
    try {
      const res = await api.approveTopic(topicId);
      router.push(`/jobs/${res.job_id}`);
    } catch {
      setLoading(false);
    }
  }

  return (
    <button
      onClick={handleApprove}
      disabled={loading}
      style={{
        padding: "6px 12px",
        borderRadius: 6,
        border: "none",
        background: "var(--accent)",
        color: "#fff",
        fontSize: "0.8rem",
        cursor: loading ? "wait" : "pointer",
      }}
    >
      {loading ? "…" : "승인"}
    </button>
  );
}
