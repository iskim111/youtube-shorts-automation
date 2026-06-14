"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { api, type RightsQueueItem } from "@/lib/api";

type Props = {
  item: RightsQueueItem;
};

export function RightsReview({ item }: Props) {
  const router = useRouter();
  const [loading, setLoading] = useState(false);

  if (!item.job_id) {
    return <span className="badge badge-muted">주제 검수 (Job 미생성)</span>;
  }

  async function review(action: "approve" | "reject") {
    setLoading(true);
    try {
      await api.reviewJob(item.job_id!, action);
      router.refresh();
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ display: "flex", gap: 8 }}>
      <button
        onClick={() => review("approve")}
        disabled={loading}
        style={{
          padding: "4px 10px",
          borderRadius: 6,
          border: "none",
          background: "var(--success)",
          color: "#fff",
          fontSize: "0.75rem",
          cursor: "pointer",
        }}
      >
        승인
      </button>
      <button
        onClick={() => review("reject")}
        disabled={loading}
        style={{
          padding: "4px 10px",
          borderRadius: 6,
          border: "1px solid var(--danger)",
          background: "transparent",
          color: "var(--danger)",
          fontSize: "0.75rem",
          cursor: "pointer",
        }}
      >
        거부
      </button>
    </div>
  );
}
