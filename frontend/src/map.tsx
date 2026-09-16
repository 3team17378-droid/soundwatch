import { useEffect, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import L from "leaflet";
import "leaflet.markercluster";
import "leaflet/dist/leaflet.css";
import "leaflet.markercluster/dist/MarkerCluster.css";
import "leaflet.markercluster/dist/MarkerCluster.Default.css";
import { api } from "./api";
import { FilterBar, Pagination, QueryState } from "./components";
import { CLASSES, type Filters } from "./types";
const COLORS = [
  "#12877f",
  "#23465a",
  "#b27917",
  "#b65579",
  "#8261a2",
  "#397ab0",
  "#3e775d",
  "#b74b32",
  "#557c93",
  "#6c7c84",
];
type Event = {
  id: string | null;
  latitude: number;
  longitude: number;
  class: string;
  average_dbfs: number;
  inference_mode: string;
  date: string;
  status: string;
};
export function MapPage() {
  const [filters, setFilters] = useState<Filters>({}),
    [bounds, setBounds] = useState({
      south: 37.45,
      north: 37.65,
      west: 126.85,
      east: 127.15,
    }),
    [page, setPage] = useState(1),
    [tileError, setTileError] = useState(false);
  const ref = useRef<HTMLDivElement>(null),
    map = useRef<L.Map | null>(null),
    cluster = useRef<L.MarkerClusterGroup | null>(null);
  const q = useQuery({
    queryKey: ["map", filters, bounds, page],
    queryFn: async () =>
      (
        await api.get<{ items: Event[]; total: number; anonymized: boolean }>(
          "/map/noise-events",
          { params: { ...filters, ...bounds, page } },
        )
      ).data,
  });
  useEffect(() => {
    if (!ref.current) return;
    const m = L.map(ref.current).setView([37.558, 126.987], 12);
    map.current = m;
    const tiles = L.tileLayer(
      "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
      {
        attribution:
          '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        maxZoom: 19,
      },
    ).addTo(m);
    tiles.on("tileerror", () => setTileError(true));
    const group = L.markerClusterGroup();
    cluster.current = group;
    m.addLayer(group);
    const update = () => {
      const b = m.getBounds();
      setBounds({
        south: Math.max(-90, b.getSouth()),
        north: Math.min(90, b.getNorth()),
        west: Math.max(-180, b.getWest()),
        east: Math.min(180, b.getEast()),
      });
      setPage(1);
    };
    m.on("moveend", update);
    update();
    return () => {
      m.remove();
      map.current = null;
      cluster.current = null;
    };
  }, []);
  useEffect(() => {
    const g = cluster.current;
    if (!g) return;
    g.clearLayers();
    q.data?.items.forEach((e) => {
      const color = COLORS[Math.max(0, CLASSES.indexOf(e.class))];
      const icon = L.divIcon({
        className: "noise-marker",
        html: `<span style="background:${color}"></span>`,
        iconSize: [24, 24],
      });
      const popup = document.createElement("div");
      const title = document.createElement("strong");
      title.textContent = e.class;
      popup.appendChild(title);
      const p = document.createElement("p");
      p.textContent = `${e.date} · ${e.average_dbfs.toFixed(1)} dBFS · ${e.inference_mode}`;
      popup.appendChild(p);
      if (e.id) {
        const a = document.createElement("a");
        a.href = "/app/admin/reviews/" + e.id;
        a.textContent = "검토 상세 보기";
        popup.appendChild(a);
      }
      L.marker([e.latitude, e.longitude], { icon }).bindPopup(popup).addTo(g);
    });
  }, [q.data]);
  return (
    <>
      <div className="page-heading">
        <div>
          <div className="eyebrow">SOUND AROUND YOU</div>
          <h1>도시 소음 지도</h1>
          <p>
            {q.data?.anonymized
              ? "공개 동의 기록 · 반올림 좌표 (소수점 2자리)"
              : "관리자 지도 · 원본 좌표"}{" "}
            · 지도를 이동하면 현재 영역을 조회합니다.
          </p>
        </div>
      </div>
      <FilterBar
        value={filters}
        onChange={(f) => {
          setFilters(f);
          setPage(1);
        }}
        map
      />
      <section className="card map-card">
        <div
          ref={ref}
          className="map-canvas"
          aria-label="도시 소음 발생 지도"
        />
        {tileError && (
          <p className="error">
            배경 지도 타일을 불러오지 못했습니다. 인터넷 연결을 확인하세요. 기록
            좌표 조회는 계속 사용할 수 있습니다.
          </p>
        )}
        <QueryState loading={q.isLoading} error={q.error}>
          <p className="muted">
            현재 영역 {q.data?.total || 0}건.{" "}
            {q.data?.items.length
              ? "마커를 눌러 분석 요약을 확인하세요."
              : "조건에 맞는 기록이 없습니다. 영역 또는 필터를 변경하세요."}
          </p>
        </QueryState>
        <Pagination
          page={page}
          total={q.data?.total || 0}
          size={500}
          onChange={setPage}
        />
        <div className="map-legend">
          {CLASSES.map((c, i) => (
            <span key={c}>
              <i style={{ background: COLORS[i] }} />
              {c}
            </span>
          ))}
        </div>
      </section>
    </>
  );
}
