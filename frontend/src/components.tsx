import type { ReactNode } from "react";
import { Link } from "react-router-dom";
import { AudioLines, ArrowUpRight } from "lucide-react";
import { CLASSES, STATUSES, type Filters } from "./types";
import { errorMessage } from "./api";
export function Logo() {
  return (
    <Link to="/" className="logo">
      <span>
        <AudioLines size={25} />
      </span>
      SOUND<span className="logo-watch">WATCH</span>
    </Link>
  );
}
export function Badge({ status }: { status: string }) {
  return (
    <span className={`badge ${status.toLowerCase()}`}>
      {STATUSES[status] || status}
    </span>
  );
}
export function Notice() {
  return (
    <p className="notice">
      AI 결과는 환경소음 분류를 보조하는 참고 정보이며 법적·행정적 판정이
      아닙니다. 음량은 실제 장비 보정 없는 <strong>dBFS 기반 상대 음량</strong>
      입니다.
    </p>
  );
}
export function QueryState({
  loading,
  error,
  empty = false,
  children,
}: {
  loading: boolean;
  error: unknown;
  empty?: boolean;
  children: ReactNode;
}) {
  if (loading)
    return (
      <div className="state" role="status">
        데이터를 불러오는 중…
      </div>
    );
  if (error)
    return (
      <div className="state error" role="alert">
        {errorMessage(error)}
      </div>
    );
  if (empty)
    return (
      <div className="state">
        아직 기록이 없습니다.
        <br />
        <Link to="/app/upload">
          첫 소음 분석 등록하기 <ArrowUpRight size={14} />
        </Link>
      </div>
    );
  return <>{children}</>;
}
export function FilterBar({
  value,
  onChange,
  admin = false,
  map = false,
}: {
  value: Filters;
  onChange: (x: Filters) => void;
  admin?: boolean;
  map?: boolean;
}) {
  const set = (key: keyof Filters, v: string) =>
    onChange({ ...value, [key]: v || undefined });
  return (
    <div className="filters">
      <label>
        시작일 (UTC)
        <input
          type="date"
          value={value.start?.slice(0, 10) || ""}
          onChange={(e) =>
            set("start", e.target.value ? `${e.target.value}T00:00:00Z` : "")
          }
        />
      </label>
      <label>
        종료일 (UTC)
        <input
          type="date"
          value={value.end?.slice(0, 10) || ""}
          onChange={(e) =>
            set("end", e.target.value ? `${e.target.value}T23:59:59.999Z` : "")
          }
        />
      </label>
      <label>
        소음 유형
        <select
          value={value.noise_type || ""}
          onChange={(e) => set("noise_type", e.target.value)}
        >
          <option value="">전체 유형</option>
          {CLASSES.map((x) => (
            <option key={x}>{x}</option>
          ))}
        </select>
      </label>
      <label>
        검토 상태
        <select
          value={value.status || ""}
          onChange={(e) => set("status", e.target.value)}
        >
          <option value="">전체 상태</option>
          {Object.entries(STATUSES)
            .filter(([k]) => k !== "DELETED")
            .map(([k, v]) => (
              <option value={k} key={k}>
                {v}
              </option>
            ))}
        </select>
      </label>
      {!map && (
        <label>
          지역
          <input
            placeholder="장소명 검색"
            value={value.region || ""}
            onChange={(e) => set("region", e.target.value)}
          />
        </label>
      )}
      {admin && !map && (
        <label>
          사용자 ID
          <input
            placeholder="전체 사용자"
            value={value.user_id || ""}
            onChange={(e) => set("user_id", e.target.value)}
          />
        </label>
      )}
      <button className="button subtle" onClick={() => onChange({})}>
        초기화
      </button>
    </div>
  );
}
export function Pagination({
  page,
  total,
  size = 20,
  onChange,
}: {
  page: number;
  total: number;
  size?: number;
  onChange: (n: number) => void;
}) {
  return (
    <div className="pagination">
      <span>
        총 {total}건 · {page} / {Math.max(1, Math.ceil(total / size))} 페이지
      </span>
      <button disabled={page === 1} onClick={() => onChange(page - 1)}>
        이전
      </button>
      <button
        disabled={page * size >= total}
        onClick={() => onChange(page + 1)}
      >
        다음
      </button>
    </div>
  );
}
export const number = (
  n: number | null | undefined,
  suffix = "",
  digits = 1,
) =>
  n == null
    ? "측정 전"
    : `${n.toLocaleString("ko-KR", { maximumFractionDigits: digits })}${suffix}`;
