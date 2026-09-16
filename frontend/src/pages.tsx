import { useEffect, useRef, useState, type FormEvent } from "react";
import {
  Link,
  NavLink,
  Outlet,
  useNavigate,
  useParams,
} from "react-router-dom";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Activity,
  ArrowRight,
  AudioLines,
  BarChart3,
  CheckCircle2,
  ChevronRight,
  ClipboardCheck,
  FileAudio,
  LayoutDashboard,
  LogOut,
  MapPinned,
  Plus,
  Radio,
  Settings,
  ShieldCheck,
  UploadCloud,
  Users,
  Waves,
} from "lucide-react";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { api, errorMessage } from "./api";
import { useAuth } from "./auth";
import {
  Badge,
  FilterBar,
  Logo,
  Notice,
  Pagination,
  QueryState,
  number,
} from "./components";
import {
  CLASSES,
  STAGES,
  type Analysis,
  type Count,
  type Filters,
  type Job,
  type ModelStatus,
  type NoiseRecord,
  type Summary,
  type User,
} from "./types";

const COLORS = [
  "#12877f",
  "#23465a",
  "#51b0a1",
  "#d6a43b",
  "#7190aa",
  "#a481ab",
  "#dc8368",
  "#587873",
  "#89b65a",
  "#929da5",
];
export function Layout() {
  const { user, logout } = useAuth();
  const model = useQuery({
    queryKey: ["model"],
    queryFn: async () =>
      (await api.get<ModelStatus>("/system/model-status")).data,
    staleTime: 60000,
  });
  const links = [
    ["/app", "Overview", LayoutDashboard],
    ["/app/upload", "새 음성 분석", Plus],
    ["/app/records", "내 분석 기록", FileAudio],
    ["/app/map", "소음 지도", MapPinned],
    ["/app/statistics", "통계 대시보드", BarChart3],
  ] as const;
  const admins = [
    ["/app/admin/reviews", "검토 목록", ClipboardCheck],
    ["/app/admin/users", "사용자 관리", Users],
    ["/app/admin/audit", "감사 로그", ShieldCheck],
    ["/app/admin/system", "시스템 상태", Settings],
  ] as const;
  return (
    <div className="shell">
      <aside className="sidebar">
        <Logo />
        <div className="workspace-label">URBAN SOUND INTELLIGENCE</div>
        <nav aria-label="주 메뉴">
          {links.map(([to, label, Icon]) => (
            <NavLink end={to === "/app"} to={to} key={to}>
              <Icon size={18} />
              {label}
            </NavLink>
          ))}
          {user?.role === "ADMIN" && (
            <>
              <div className="nav-section">ADMINISTRATION</div>
              {admins.map(([to, label, Icon]) => (
                <NavLink to={to} key={to}>
                  <Icon size={18} />
                  {label}
                </NavLink>
              ))}
            </>
          )}
        </nav>
        <div className="sidebar-bottom">
          <div className="environment">
            <span className="dot" />
            LOCAL WORKSPACE <Badge status={model.data?.mode || "연결 중"} />
          </div>
          <p>
            도시의 소리를 기록하고
            <br />더 나은 환경을 만듭니다.
          </p>
          <div className="profile">
            <div className="avatar">{user?.name.slice(0, 1)}</div>
            <div>
              <strong>{user?.name}</strong>
              <small>
                {user?.role === "ADMIN" ? "Administrator" : "Community member"}
              </small>
            </div>
            <button aria-label="로그아웃" onClick={logout}>
              <LogOut size={17} />
            </button>
          </div>
        </div>
      </aside>
      <div className="main-wrap">
        <header className="topbar">
          <span>
            SOUNDWATCH <ChevronRight size={14} /> 환경 소음 모니터링
          </span>
          <div>
            <span className="dot" />{" "}
            {model.data?.ready ? "분석 엔진 준비됨" : "엔진 상태 확인"}{" "}
            <Badge status={model.data?.mode || "연결 중"} />
          </div>
        </header>
        <main className="content">
          <Outlet />
        </main>
        <footer>
          <Notice />
          <span>© 2026 SOUNDWATCH · Smart city, better living.</span>
        </footer>
      </div>
    </div>
  );
}

export function Landing() {
  return (
    <div className="landing">
      <header>
        <Logo />
        <div>
          <Link to="/login">로그인</Link>
          <Link className="button" to="/register">
            시작하기 <ArrowRight size={16} />
          </Link>
        </div>
      </header>
      <section className="hero">
        <div className="eyebrow">
          <span className="dot" /> LISTEN TO YOUR CITY
        </div>
        <h1>
          도시의 소리를,
          <br />
          <em>의미 있는 데이터로.</em>
        </h1>
        <p>
          어디서, 어떤 소음이 발생했을까요?
          <br />
          소리를 기록하고 분석해 우리 도시의 환경을 함께 이해합니다.
        </p>
        <div className="hero-actions">
          <Link to="/app/upload" className="button">
            소음 분석 시작하기 <ArrowRight size={17} />
          </Link>
          <Link to="/app/map" className="button secondary">
            소음 지도 둘러보기
          </Link>
        </div>
        <div className="sound-visual" aria-hidden="true">
          {Array.from({ length: 72 }, (_, i) => (
            <span
              key={i}
              style={{
                height: `${15 + Math.abs(Math.sin(i * 0.32) * Math.cos(i * 0.17)) * 100}px`,
              }}
            />
          ))}
        </div>
        <span className="caption">RECORD · ANALYZE · UNDERSTAND</span>
      </section>
      <section className="feature-grid">
        {[
          [
            FileAudio,
            "01 / RECORD",
            "소리를 기록하세요",
            "WAV, MP3, M4A, FLAC, OGG 파일과 발생 위치를 등록합니다.",
          ],
          [
            Waves,
            "02 / ANALYZE",
            "특징을 확인하세요",
            "파형, 스펙트로그램, 상대 음량과 분류 결과를 확인합니다.",
          ],
          [
            MapPinned,
            "03 / EXPLORE",
            "도시를 이해하세요",
            "지도와 통계에서 소음의 공간·시간 분포를 살펴봅니다.",
          ],
        ].map(([Icon, n, title, desc]) => {
          const I = Icon as typeof FileAudio;
          return (
            <article key={String(n)}>
              <I size={25} />
              <small>{String(n)}</small>
              <h2>{String(title)}</h2>
              <p>{String(desc)}</p>
            </article>
          );
        })}
      </section>
      <Notice />
      <footer>
        특징 기반 DEMO와 호환 ONNX MODEL을 명확하게 구분합니다. 외부 AI API 키가
        필요하지 않습니다.
      </footer>
    </div>
  );
}

export function AuthPage({ register = false }: { register?: boolean }) {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [error, setError] = useState(""),
    [busy, setBusy] = useState(false);
  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const data = new FormData(e.currentTarget);
    setBusy(true);
    setError("");
    try {
      const email = String(data.get("email")),
        password = String(data.get("password"));
      if (register)
        await api.post("/auth/register", {
          email,
          password,
          name: data.get("name"),
        });
      await login(email, password);
      navigate("/app");
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  }
  return (
    <div className="auth-page">
      <div className="auth-brand">
        <Logo />
        <h1>
          더 조용한 도시를 위한
          <br />첫 번째 기록.
        </h1>
        <AudioLines size={110} strokeWidth={0.8} />
        <p>Understand the sound around you.</p>
      </div>
      <div className="auth-form">
        <span className="eyebrow">WELCOME TO SOUNDWATCH</span>
        <h1>{register ? "새 계정 만들기" : "다시 만나 반갑습니다"}</h1>
        <p>도시 소음 데이터를 한곳에서 확인하세요.</p>
        <form onSubmit={submit}>
          {register && (
            <label>
              이름
              <input name="name" required maxLength={80} autoComplete="name" />
            </label>
          )}
          <label>
            이메일
            <input type="email" name="email" required autoComplete="email" />
          </label>
          <label>
            비밀번호
            <input
              type="password"
              name="password"
              required
              minLength={register ? 12 : 1}
              maxLength={128}
              autoComplete={register ? "new-password" : "current-password"}
            />
          </label>
          {register && (
            <small>
              12자 이상 비밀번호를 사용하세요. 공개 데이터 제공은 업로드할 때
              별도로 선택합니다.
            </small>
          )}
          {error && (
            <p role="alert" className="error">
              {error}
            </p>
          )}
          <button className="button" disabled={busy}>
            {busy ? "처리 중…" : register ? "가입하고 시작하기" : "로그인"}{" "}
            <ArrowRight size={16} />
          </button>
        </form>
        <p>
          {register ? "이미 계정이 있나요?" : "처음 방문하셨나요?"}{" "}
          <Link to={register ? "/login" : "/register"}>
            {register ? "로그인" : "회원가입"}
          </Link>
        </p>
      </div>
    </div>
  );
}

function Chart({
  data,
  type = "bar",
}: {
  data: Count[];
  type?: "bar" | "area" | "pie";
}) {
  if (!data.length)
    return <div className="chart-empty">표시할 데이터가 없습니다.</div>;
  return (
    <ResponsiveContainer width="100%" height={235}>
      {type === "pie" ? (
        <PieChart>
          <Pie
            data={data}
            dataKey="count"
            nameKey="name"
            innerRadius={65}
            outerRadius={90}
            paddingAngle={3}
          >
            {data.map((_, i) => (
              <Cell key={i} fill={COLORS[i % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip />
        </PieChart>
      ) : type === "area" ? (
        <AreaChart data={data}>
          <defs>
            <linearGradient id="area" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#168c81" stopOpacity={0.3} />
              <stop offset="100%" stopColor="#168c81" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid vertical={false} stroke="#e7eeef" />
          <XAxis dataKey="name" fontSize={11} />
          <YAxis allowDecimals={false} width={30} fontSize={11} />
          <Tooltip />
          <Area
            dataKey="count"
            name="기록 수"
            type="monotone"
            stroke="#168c81"
            fill="url(#area)"
            strokeWidth={2.5}
          />
        </AreaChart>
      ) : (
        <BarChart data={data}>
          <CartesianGrid vertical={false} stroke="#e7eeef" />
          <XAxis dataKey="name" fontSize={10} />
          <YAxis allowDecimals={false} width={30} fontSize={11} />
          <Tooltip />
          <Bar
            dataKey="count"
            name="기록 수"
            fill="#168c81"
            radius={[4, 4, 0, 0]}
          />
        </BarChart>
      )}
    </ResponsiveContainer>
  );
}

export function Dashboard({ statistics = false }: { statistics?: boolean }) {
  const { user } = useAuth();
  const [filters, setFilters] = useState<Filters>({});
  const query = useQuery({
    queryKey: ["summary", filters],
    queryFn: async () =>
      (await api.get<Summary>("/dashboard/summary", { params: filters })).data,
  });
  const recent = useQuery({
    queryKey: ["recent"],
    queryFn: async () =>
      (
        await api.get<{ items: NoiseRecord[] }>("/noise-records", {
          params: { page_size: 5 },
        })
      ).data,
  });
  const d = query.data;
  return (
    <>
      <div className="page-heading">
        <div>
          <div className="eyebrow">
            {statistics ? "DATA & INSIGHTS" : "YOUR CITY, AT A GLANCE"}
          </div>
          <h1>{statistics ? "소음 통계 대시보드" : "도시 소음 모니터링"}</h1>
          <p>
            {user?.role === "ADMIN"
              ? "전체 분석 기록"
              : "내가 등록한 분석 기록"}
            을 통해 주변의 소리를 이해하세요.
          </p>
        </div>
        <Link className="button" to="/app/upload">
          <Plus size={17} /> 새 음성 분석
        </Link>
      </div>
      <div className="info-banner">
        <Radio size={21} />
        <div>
          <strong>소리에서 시작하는 도시의 변화</strong>
          <span>
            분류 결과는 모델 모드와 함께 표시됩니다. DEMO 결과는 포트폴리오
            시연용입니다.
          </span>
        </div>
        <Link to="/app/map">
          지도 보기 <ArrowRight size={16} />
        </Link>
      </div>
      <FilterBar
        value={filters}
        onChange={setFilters}
        admin={user?.role === "ADMIN"}
      />
      <QueryState loading={query.isLoading} error={query.error}>
        {d && (
          <>
            <div className="kpi-grid">
              {[
                [FileAudio, "전체 분석", d.total, "건"],
                [Activity, "오늘 분석", d.today, "건"],
                [ClipboardCheck, "검토 필요", d.review_required, "건"],
                [Waves, "평균 상대 음량", d.average_dbfs, " dBFS"],
              ].map(([Icon, label, value, unit]) => {
                const I = Icon as typeof FileAudio;
                return (
                  <article className="kpi" key={String(label)}>
                    <div>
                      <span>{String(label)}</span>
                      <I size={19} />
                    </div>
                    <strong>
                      {number(value as number | null, "", 1)}{" "}
                      <small>{value != null ? String(unit) : ""}</small>
                    </strong>
                    <span className="kpi-caption">
                      {label === "평균 상대 음량"
                        ? "장비 보정 없는 상대값"
                        : label === "오늘 분석"
                          ? "UTC 기준 오늘"
                          : "현재 필터 기준"}
                    </span>
                  </article>
                );
              })}
            </div>
            <div className="chart-grid">
              <section className="card">
                <div className="card-heading">
                  <div>
                    <h2>소음 발생 추이</h2>
                    <p>발생 일자별 등록 건수 · UTC</p>
                  </div>
                  <span className="tag">DAILY</span>
                </div>
                <Chart data={d.timeseries} type="area" />
              </section>
              <section className="card">
                <div className="card-heading">
                  <div>
                    <h2>소음 유형 분포</h2>
                    <p>관리자 확정값 우선 적용</p>
                  </div>
                  <span className="tag">CATEGORY</span>
                </div>
                <div className="donut-layout">
                  <Chart data={d.categories} type="pie" />
                  <div className="legend">
                    {d.categories.map((x, i) => (
                      <div key={x.name}>
                        <i style={{ background: COLORS[i % COLORS.length] }} />
                        <span>{x.name}</span>
                        <strong>{x.count}</strong>
                      </div>
                    ))}
                  </div>
                </div>
              </section>
            </div>
            {statistics ? (
              <>
                <div className="chart-grid">
                  {[
                    ["시간대별 발생", d.hourly],
                    ["요일별 발생 (월=0)", d.weekday],
                    ["지역별 발생", d.regions],
                  ].map(([title, data]) => (
                    <section className="card" key={String(title)}>
                      <h2>{String(title)}</h2>
                      <Chart data={data as Count[]} />
                    </section>
                  ))}
                </div>
                <section className="card">
                  <h2>운영·포트폴리오 성과 지표</h2>
                  <div className="metric-grid">
                    {[
                      ["분석 실패", number(d.failed, "건")],
                      ["평균 추론 시간", number(d.average_inference_ms, " ms")],
                      [
                        "평균 파일 처리 시간",
                        number(d.average_processing_ms, " ms"),
                      ],
                      [
                        "업로드 처리 성공률",
                        number(
                          d.upload_processing_success_rate == null
                            ? null
                            : d.upload_processing_success_rate * 100,
                          "%",
                        ),
                      ],
                      [
                        "검토 필요 비율",
                        number(
                          d.review_required_rate == null
                            ? null
                            : d.review_required_rate * 100,
                          "%",
                        ),
                      ],
                      [
                        "예측·관리자 일치율",
                        number(
                          d.agreement_rate == null
                            ? null
                            : d.agreement_rate * 100,
                          "%",
                        ),
                      ],
                      ["최대 상대 음량", number(d.maximum_dbfs, " dBFS")],
                      ["분류 정확도 / macro F1", "측정 전"],
                      ["API 테스트 통과율", "측정 전 · 테스트 보고서 참조"],
                      ["테스트 커버리지", "측정 전 · 테스트 보고서 참조"],
                    ].map(([k, v]) => (
                      <div key={k}>
                        <span>{k}</span>
                        <strong>{v}</strong>
                      </div>
                    ))}
                  </div>
                  <p className="muted">
                    {d.metrics.note} 처리 성공률은 서버가 수락한 분석 작업
                    기준이며, 시간은 분석 작업 내부 처리 구간입니다.
                  </p>
                </section>
              </>
            ) : (
              <section className="card">
                <div className="card-heading">
                  <div>
                    <h2>최근 분석 기록</h2>
                    <p>가장 최근에 등록한 소음을 확인하세요.</p>
                  </div>
                  <Link to="/app/records">
                    전체 보기 <ArrowRight size={15} />
                  </Link>
                </div>
                <QueryState
                  loading={recent.isLoading}
                  error={recent.error}
                  empty={!recent.data?.items.length}
                >
                  <RecordTable records={recent.data?.items || []} />
                </QueryState>
              </section>
            )}
          </>
        )}
      </QueryState>
    </>
  );
}

export function RecordTable({
  records,
  admin = false,
}: {
  records: NoiseRecord[];
  admin?: boolean;
}) {
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>분석 기록</th>
            <th>소음 유형</th>
            <th>상대 음량</th>
            <th>검토 상태</th>
            <th>발생 일시</th>
            <th />
          </tr>
        </thead>
        <tbody>
          {records.map((r) => (
            <tr key={r.id}>
              <td>
                <Link
                  className="record-title"
                  to={`${admin ? "/app/admin/reviews" : "/app/records"}/${r.id}`}
                >
                  <span className="file-icon">
                    <FileAudio size={19} />
                  </span>
                  <span>
                    <strong>{r.title}</strong>
                    <small>
                      {r.address || "장소 미지정"}
                      {r.deletion_requested_at ? " · 삭제 요청 접수" : ""}
                    </small>
                  </span>
                </Link>
              </td>
              <td>
                {r.confirmed_class || r.analysis?.predicted_class || "—"}{" "}
                {r.analysis && <Badge status={r.analysis.inference_mode} />}
              </td>
              <td>{number(r.analysis?.average_dbfs, " dBFS")}</td>
              <td>
                <Badge status={r.status} />
              </td>
              <td>{new Date(r.occurred_at).toLocaleString("ko-KR")}</td>
              <td>
                <Link
                  aria-label={`${r.title} 상세`}
                  to={`${admin ? "/app/admin/reviews" : "/app/records"}/${r.id}`}
                >
                  <ChevronRight size={16} />
                </Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function Records({ admin = false }: { admin?: boolean }) {
  const [filters, setFilters] = useState<Filters>({}),
    [page, setPage] = useState(1),
    [sort, setSort] = useState("newest");
  const query = useQuery({
    queryKey: ["records", admin, filters, page, sort],
    queryFn: async () =>
      (
        await api.get<{ items: NoiseRecord[]; total: number }>(
          admin ? "/admin/noise-records" : "/noise-records",
          { params: { ...filters, page, sort } },
        )
      ).data,
  });
  return (
    <>
      <div className="page-heading">
        <div>
          <div className="eyebrow">
            {admin ? "REVIEW WORKSPACE" : "SOUND LIBRARY"}
          </div>
          <h1>{admin ? "관리자 검토 목록" : "내 분석 기록"}</h1>
          <p>
            {admin
              ? "분류 결과를 확인하고 검토 의견을 기록하세요."
              : "내 주변의 소리를 기록한 타임라인입니다."}
          </p>
        </div>
        <Link to="/app/upload" className="button">
          <Plus size={16} />새 음성 분석
        </Link>
      </div>
      <FilterBar
        value={filters}
        onChange={(x) => {
          setFilters(x);
          setPage(1);
        }}
        admin={admin}
      />
      <section className="card">
        <div className="list-toolbar">
          <input
            aria-label="기록 검색"
            placeholder="제목 또는 장소 검색"
            value={filters.search || ""}
            onChange={(e) => {
              setFilters({ ...filters, search: e.target.value });
              setPage(1);
            }}
          />
          <select
            aria-label="정렬"
            value={sort}
            onChange={(e) => {
              setSort(e.target.value);
              setPage(1);
            }}
          >
            <option value="newest">최신 등록순</option>
            <option value="oldest">오래된 등록순</option>
            <option value="occurred">발생 일시순</option>
          </select>
        </div>
        <QueryState
          loading={query.isLoading}
          error={query.error}
          empty={!query.data?.items.length}
        >
          <RecordTable records={query.data?.items || []} admin={admin} />
        </QueryState>
        <Pagination
          page={page}
          total={query.data?.total || 0}
          onChange={setPage}
        />
      </section>
    </>
  );
}

export function validateFile(file: File, maxMB = 20) {
  if (!/\.(wav|mp3|m4a|flac|ogg)$/i.test(file.name))
    return "WAV, MP3, M4A, FLAC, OGG 파일을 선택하세요.";
  if (file.size === 0) return "빈 파일은 업로드할 수 없습니다.";
  if (file.size > maxMB * 1024 * 1024)
    return `파일 크기는 ${maxMB}MB 이하여야 합니다.`;
  return "";
}
export function Upload() {
  const navigate = useNavigate();
  const cache = useQueryClient();
  const [file, setFile] = useState<File | null>(null),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false),
    [progress, setProgress] = useState(0);
  const model = useQuery({
    queryKey: ["model"],
    queryFn: async () =>
      (await api.get<ModelStatus>("/system/model-status")).data,
  });
  const fileInput = useRef<HTMLInputElement>(null);
  function selectFile(f?: File) {
    if (!f) return;
    setFile(f);
    setError(validateFile(f, model.data?.max_upload_mb));
  }
  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!file) {
      setError("음성 파일을 선택하세요.");
      return;
    }
    const issue = validateFile(file, model.data?.max_upload_mb);
    if (issue) {
      setError(issue);
      return;
    }
    const data = new FormData(e.currentTarget);
    data.set("file", file);
    data.set(
      "occurred_at",
      new Date(String(data.get("occurred_at"))).toISOString(),
    );
    data.set("public_consent", data.get("public_consent") ? "true" : "false");
    setBusy(true);
    setError("");
    try {
      const result = await api.post("/noise-records", data, {
        onUploadProgress: (e) =>
          setProgress(Math.round((e.loaded / (e.total || 1)) * 100)),
      });
      await cache.invalidateQueries();
      navigate("/app/jobs/" + result.data.job_id);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <div className="page-heading">
        <div>
          <div className="eyebrow">NEW SOUND RECORD</div>
          <h1>새 음성 분석</h1>
          <p>소음 파일과 발생 정보를 입력하면 분석을 시작합니다.</p>
        </div>
        <Badge status={model.data?.mode || "확인 중"} />
      </div>
      <form className="upload-grid" onSubmit={submit}>
        <section className="card">
          <h2>01. 음성 파일</h2>
          <div
            className="dropzone"
            onDragOver={(e) => e.preventDefault()}
            onDrop={(e) => {
              e.preventDefault();
              selectFile(e.dataTransfer.files[0]);
            }}
          >
            <UploadCloud size={42} />
            <h3>{file ? file.name : "음성 파일을 여기에 놓아주세요"}</h3>
            <p>
              {file
                ? `${(file.size / 1024 / 1024).toFixed(2)} MB`
                : `WAV · MP3 · M4A · FLAC · OGG / 최대 ${model.data?.max_upload_mb || 20} MB`}
            </p>
            <button
              type="button"
              className="button secondary"
              onClick={() => fileInput.current?.click()}
            >
              파일 선택
            </button>
            <input
              ref={fileInput}
              type="file"
              aria-label="음성 파일"
              accept=".wav,.mp3,.m4a,.flac,.ogg"
              onChange={(e) => selectFile(e.target.files?.[0])}
              hidden
            />
          </div>
          <p className="muted">
            최대 {model.data?.max_duration_seconds || 120}초. 다른 사람의 대화나
            개인정보가 포함되지 않은 음성을 사용하세요.
          </p>
          <h2>02. 기록 정보</h2>
          <label>
            제목
            <input
              name="title"
              required
              maxLength={160}
              placeholder="예: 사거리에서 들리는 차량 소음"
            />
          </label>
          <label>
            설명
            <textarea
              name="description"
              maxLength={2000}
              rows={3}
              placeholder="소음이 발생한 상황을 간단히 기록하세요."
            />
          </label>
        </section>
        <section className="card">
          <h2>03. 위치와 시간</h2>
          <label>
            장소명
            <input
              name="address"
              maxLength={300}
              placeholder="예: 시청 광장 일대"
            />
          </label>
          <div className="two-col">
            <label>
              위도
              <input
                name="latitude"
                type="number"
                step="any"
                required
                min={-90}
                max={90}
                placeholder="37.5665"
              />
            </label>
            <label>
              경도
              <input
                name="longitude"
                type="number"
                step="any"
                required
                min={-180}
                max={180}
                placeholder="126.9780"
              />
            </label>
          </div>
          <label>
            발생 시각 (내 기기 시간대)
            <input type="datetime-local" name="occurred_at" required />
          </label>
          <div className="consent">
            <label>
              <input name="public_consent" type="checkbox" />
              비식별 데이터의 공개 지도·통계 활용에 동의합니다.
            </label>
            <p>
              공개 좌표는 소수점 둘째 자리로 반올림됩니다.
              제목·설명·상세주소·원본 음성은 공개되지 않습니다.
            </p>
          </div>
          <div className="retention">
            <ShieldCheck size={20} />
            <p>
              원본 기본 {model.data?.original_retention_days || 7}일, 결과{" "}
              {model.data?.result_retention_days || 90}일 보존. 비동의 기록은
              원본 삭제 시 특징과 메타데이터도 삭제됩니다.
            </p>
          </div>
          {error && (
            <p className="error" role="alert">
              {error}
            </p>
          )}
          {busy && (
            <p role="status">
              {progress < 100 ? `업로드 ${progress}%` : "파일 검증 중…"}
            </p>
          )}
          <button className="button full" disabled={busy}>
            {busy ? "처리 중…" : "분석 시작하기"}
            <ArrowRight size={17} />
          </button>
          <small className="muted">
            DEMO는 학습된 AI 모델이 아닌 특징 기반 시연용 분류입니다.
          </small>
        </section>
      </form>
    </>
  );
}

export function Progress() {
  const { id } = useParams();
  const [live, setLive] = useState<Job | null>(null);
  const query = useQuery({
    queryKey: ["job", id],
    queryFn: async () => (await api.get<Job>("/analysis/jobs/" + id)).data,
    refetchInterval: (q) =>
      ["COMPLETED", "FAILED"].includes(q.state.data?.stage || "")
        ? false
        : 1500,
  });
  useEffect(() => {
    const ws = new WebSocket(
      `${location.protocol === "https:" ? "wss:" : "ws:"}//${location.host}/api/v1/ws/analysis/${id}`,
    );
    ws.onopen = () =>
      ws.send(
        JSON.stringify({ token: sessionStorage.getItem("soundwatch-token") }),
      );
    ws.onmessage = (e) => setLive(JSON.parse(e.data));
    return () => ws.close();
  }, [id]);
  const job =
    query.data && ["COMPLETED", "FAILED"].includes(query.data.stage)
      ? query.data
      : live || query.data;
  return (
    <>
      <div className="page-heading">
        <div>
          <div className="eyebrow">ANALYSIS PIPELINE</div>
          <h1>소리를 분석하고 있습니다</h1>
          <p>이 화면을 새로고침해도 저장된 작업 상태를 다시 불러옵니다.</p>
        </div>
      </div>
      <section className="card progress-card">
        <QueryState loading={query.isLoading && !live} error={query.error}>
          {job && (
            <>
              <AudioLines size={50} />
              <h2>{STAGES[job.stage]}</h2>
              <progress max={100} value={job.progress} />
              <ol className="stages">
                {Object.entries(STAGES)
                  .filter(([k]) => k !== "FAILED")
                  .map(([key, label]) => (
                    <li
                      key={key}
                      className={
                        job.events_json.some((e) => e.stage === key)
                          ? "complete"
                          : ""
                      }
                    >
                      <CheckCircle2 size={20} />
                      {label}
                    </li>
                  ))}
              </ol>
              {job.error && (
                <p className="error" role="alert">
                  {job.error}
                </p>
              )}
              {["COMPLETED", "FAILED"].includes(job.stage) && (
                <Link
                  className="button"
                  to={"/app/records/" + job.noise_record_id}
                >
                  분석 결과 확인
                  <ArrowRight size={16} />
                </Link>
              )}
              <p className="muted">
                WebSocket 연결이 끊기면 API 조회로 자동 보완합니다.
              </p>
            </>
          )}
        </QueryState>
      </section>
    </>
  );
}

function Spectrogram({ values }: { values: number[][] }) {
  const ref = useRef<HTMLCanvasElement>(null);
  useEffect(() => {
    const canvas = ref.current;
    if (!canvas || !values.length) return;
    canvas.width = values[0].length;
    canvas.height = values.length;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    values.forEach((row, y) =>
      row.forEach((v, x) => {
        const a = Math.max(0, Math.min(1, (v + 80) / 80));
        ctx.fillStyle = `rgb(${Math.round(15 + a * 220)},${Math.round(35 + a * 170)},${Math.round(55 + a * 50)})`;
        ctx.fillRect(x, values.length - y - 1, 1, 1);
      }),
    );
  }, [values]);
  return (
    <canvas
      ref={ref}
      className="spectrogram"
      role="img"
      aria-label="시간에 따른 64개 멜 주파수 대역의 로그 스펙트로그램"
    />
  );
}
export function AnalysisView({ a }: { a: Analysis }) {
  return (
    <>
      <section className="card">
        <div className="card-heading">
          <h2>분류 결과</h2>
          <Badge status={a.inference_mode} />
        </div>
        {a.inference_mode === "DEMO" && (
          <p className="demo-note">
            특징 기반 포트폴리오 DEMO입니다. 아래 확률은 보정되지 않은 시연
            점수이며 실제 분류 신뢰도를 의미하지 않습니다.
          </p>
        )}
        <h3 className="prediction">{a.predicted_class || "분석 실패"}</h3>
        {a.error_message && <p className="error">{a.error_message}</p>}
        {a.top_predictions_json.map((p) => (
          <div className="prediction-row" key={p.class}>
            <div>
              <span>{p.class}</span>
              <strong>{number(p.probability * 100, "%")}</strong>
            </div>
            <progress max={1} value={p.probability} />
          </div>
        ))}
        <p className="muted">
          {a.model_name} · v{a.model_version} · 추론{" "}
          {number(a.inference_time_ms, " ms")}
        </p>
        {a.low_confidence && <Badge status="REVIEW_REQUIRED" />}
      </section>
      <section className="card">
        <h2>오디오 특징</h2>
        <div className="metric-grid">
          {[
            ["평균 상대 음량", number(a.average_dbfs, " dBFS")],
            ["최대 상대 음량", number(a.maximum_dbfs, " dBFS")],
            ["RMS", number(a.rms, "", 5)],
            ["피크 진폭", number(a.peak_amplitude, "", 5)],
            ["무음 비율", number(a.silence_ratio * 100, "%")],
          ].map(([k, v]) => (
            <div key={k}>
              <span>{k}</span>
              <strong>{v}</strong>
            </div>
          ))}
        </div>
        {a.features_json?.waveform && a.features_json?.log_mel && (
          <>
            <h3>파형</h3>
            <ResponsiveContainer width="100%" height={140}>
              <AreaChart
                data={a.features_json.waveform.map((v, i) => ({ i, v }))}
              >
                <YAxis domain={[-1, 1]} width={30} fontSize={10} />
                <Tooltip />
                <Area
                  dataKey="v"
                  name="진폭"
                  stroke="#11877e"
                  fill="#d6f0e9"
                  isAnimationActive={false}
                />
              </AreaChart>
            </ResponsiveContainer>
            <h3>Log-mel spectrogram</h3>
            <Spectrogram values={a.features_json.log_mel} />
            <small>가로: 시간 / 세로: 저주파 → 고주파 (64 mel bands)</small>
          </>
        )}
      </section>
    </>
  );
}

export function Detail({ admin = false }: { admin?: boolean }) {
  const { id } = useParams();
  const { user } = useAuth();
  const navigate = useNavigate();
  const cache = useQueryClient();
  const [error, setError] = useState(""),
    [message, setMessage] = useState(""),
    [busy, setBusy] = useState(false),
    [audio, setAudio] = useState("");
  const query = useQuery({
    queryKey: ["record", id],
    queryFn: async () =>
      (await api.get<NoiseRecord>("/noise-records/" + id)).data,
  });
  const r = query.data;
  useEffect(
    () => () => {
      if (audio) URL.revokeObjectURL(audio);
    },
    [audio],
  );
  async function action(kind: string, reason: string) {
    setBusy(true);
    setError("");
    try {
      if (kind === "play") {
        const response = await api.get("/noise-records/" + id + "/audio", {
          responseType: "blob",
        });
        setAudio(URL.createObjectURL(response.data));
        return;
      }
      if (kind === "reanalyze") {
        const response = await api.post("/noise-records/" + id + "/reanalyze", {
          reason,
        });
        navigate("/app/jobs/" + response.data.job_id);
        return;
      }
      const response = await api.delete(
        "/noise-records/" + id + (kind === "audio" ? "/audio" : ""),
        { data: { reason } },
      );
      if (kind === "audio") setAudio("");
      if (response.data.status === "DELETED") {
        navigate("/app/records");
      } else {
        setMessage(
          kind === "audio"
            ? "원본 음성을 삭제했습니다."
            : "기록 삭제 요청이 접수되었습니다. 공개 지도에서 즉시 제외됩니다.",
        );
      }
      await cache.invalidateQueries();
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  }
  async function submitReview(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setBusy(true);
    setError("");
    const form = new FormData(e.currentTarget);
    try {
      await api.post(
        "/admin/noise-records/" + id + "/review",
        Object.fromEntries(form),
      );
      setMessage("검토 결과와 감사 로그가 저장되었습니다.");
      await cache.invalidateQueries();
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  }
  return (
    <QueryState loading={query.isLoading} error={query.error}>
      {r && (
        <>
          <div className="page-heading">
            <div>
              <Link to={admin ? "/app/admin/reviews" : "/app/records"}>
                ← 목록으로
              </Link>
              <h1>{r.title}</h1>
              <p>
                {r.address || "장소 미지정"} ·{" "}
                {new Date(r.occurred_at).toLocaleString("ko-KR")} ·{" "}
                {number(r.duration, "초")}
              </p>
            </div>
            <Badge status={r.status} />
          </div>
          {r.status === "PENDING" && (
            <Link className="button" to={"/app/jobs/" + r.current_job_id}>
              진행 상태 보기
            </Link>
          )}
          {r.deletion_requested_at && (
            <div className="info-banner">
              삭제 요청 접수:{" "}
              {new Date(r.deletion_requested_at).toLocaleString()}
            </div>
          )}
          <p>{r.description}</p>
          <div className="chart-grid">
            {r.analysis && <AnalysisView a={r.analysis} />}
          </div>
          <section className="card">
            <h2>원본 및 기록 관리</h2>
            <p>
              위치: {r.latitude}, {r.longitude} · 공개 데이터 활용{" "}
              {r.public_consent ? "동의" : "비동의"}
            </p>
            <div className="actions">
              <button
                disabled={busy || !!r.original_deleted_at}
                onClick={() => action("play", "")}
              >
                원본 음성 불러오기
              </button>
              <button
                disabled={
                  busy || !!r.original_deleted_at || r.status === "PENDING"
                }
                onClick={() => {
                  if (
                    window.confirm(
                      r.public_consent
                        ? "원본 음성을 영구 삭제할까요?"
                        : "비동의 기록이므로 원본·분석 특징·메타데이터를 함께 삭제할까요?",
                    )
                  )
                    void action("audio", "원본 삭제");
                }}
              >
                원본 삭제
              </button>
              <button
                disabled={busy || r.status === "PENDING"}
                onClick={() => {
                  const reason = window.prompt(
                    user?.role === "ADMIN"
                      ? "기록을 영구 삭제할 사유 (3자 이상)"
                      : "분석 기록 삭제 요청 사유 (3자 이상)",
                  );
                  if (reason && reason.length >= 3)
                    void action("record", reason);
                }}
              >
                {user?.role === "ADMIN" ? "기록 삭제 처리" : "기록 삭제 요청"}
              </button>
              {user?.role === "ADMIN" && r.status === "FAILED" && (
                <button
                  disabled={busy || !!r.original_deleted_at}
                  onClick={() => {
                    const reason = window.prompt("재분석 사유 (3자 이상)");
                    if (reason && reason.length >= 3)
                      void action("reanalyze", reason);
                  }}
                >
                  재분석
                </button>
              )}
            </div>
            {audio && <audio controls src={audio} preload="metadata" />}
            {r.original_deleted_at && <p>원본 음성은 삭제되었습니다.</p>}
          </section>
          {admin && r.analysis?.predicted_class && (
            <form className="card" onSubmit={submitReview}>
              <h2>관리자 검토</h2>
              <div className="two-col">
                <label>
                  확정 소음 유형
                  <select
                    name="confirmed_class"
                    defaultValue={
                      r.confirmed_class || r.analysis.predicted_class
                    }
                  >
                    {CLASSES.map((c) => (
                      <option key={c}>{c}</option>
                    ))}
                  </select>
                </label>
                <label>
                  검토 상태
                  <select name="status">
                    <option value="CONFIRMED">
                      확정 (유형이 바뀌면 수정 완료)
                    </option>
                    <option value="REVIEW_REQUIRED">추가 검토 필요</option>
                  </select>
                </label>
              </div>
              <label>
                검토 의견 / 수정 사유
                <textarea
                  name="comment"
                  required
                  minLength={3}
                  maxLength={2000}
                />
              </label>
              <button className="button" disabled={busy}>
                검토 저장
              </button>
            </form>
          )}
          {error && (
            <p role="alert" className="error">
              {error}
            </p>
          )}
          {message && (
            <p role="status" className="success">
              {message}
            </p>
          )}
          <section className="card">
            <h2>검토·분석 이력</h2>
            {!r.reviews.length && (
              <p className="muted">아직 관리자 검토가 없습니다.</p>
            )}
            {r.reviews.map((v) => (
              <article key={v.id} className="history">
                <strong>
                  {v.previous_class} → {v.confirmed_class}
                </strong>
                <p>{v.comment}</p>
                <small>{new Date(v.created_at).toLocaleString()}</small>
              </article>
            ))}
            <details>
              <summary>
                분석 시도 {r.analysis_history.length}건 · 모델 및 전처리 재현
                정보
              </summary>
              {r.analysis_history.map((a) => (
                <div key={a.id}>
                  <Badge status={a.inference_mode} />
                  {a.model_name} / {a.model_version} /{" "}
                  {a.predicted_class || a.error_message}
                  <pre>{JSON.stringify(a.provenance_json, null, 2)}</pre>
                </div>
              ))}
            </details>
          </section>
        </>
      )}
    </QueryState>
  );
}

export function UsersPage() {
  const [page, setPage] = useState(1),
    [search, setSearch] = useState(""),
    [error, setError] = useState("");
  const cache = useQueryClient();
  const { user } = useAuth();
  const query = useQuery({
    queryKey: ["users", page, search],
    queryFn: async () =>
      (
        await api.get<{ items: User[]; total: number }>("/admin/users", {
          params: { page, search },
        })
      ).data,
  });
  async function change(u: User, patch: object) {
    const reason = window.prompt("변경 사유를 입력하세요 (3자 이상)");
    if (!reason || reason.length < 3) return;
    try {
      await api.patch("/admin/users/" + u.id, { ...patch, reason });
      await cache.invalidateQueries({ queryKey: ["users"] });
    } catch (e) {
      setError(errorMessage(e));
    }
  }
  return (
    <>
      <div className="page-heading">
        <div>
          <div className="eyebrow">ACCESS MANAGEMENT</div>
          <h1>사용자 관리</h1>
          <p>
            역할과 계정 활성 상태를 관리합니다. 모든 변경은 감사 로그에
            남습니다.
          </p>
        </div>
      </div>
      <section className="card">
        <input
          placeholder="이름 또는 이메일 검색"
          aria-label="사용자 검색"
          value={search}
          onChange={(e) => {
            setSearch(e.target.value);
            setPage(1);
          }}
        />
        {error && (
          <p className="error" role="alert">
            {error}
          </p>
        )}
        <QueryState loading={query.isLoading} error={query.error}>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>이름 / ID</th>
                  <th>이메일</th>
                  <th>역할</th>
                  <th>상태</th>
                  <th>관리</th>
                </tr>
              </thead>
              <tbody>
                {query.data?.items.map((u) => (
                  <tr key={u.id}>
                    <td>
                      {u.name}
                      <small className="block">{u.id}</small>
                    </td>
                    <td>{u.email}</td>
                    <td>{u.role}</td>
                    <td>{u.is_active ? "활성" : "비활성"}</td>
                    <td>
                      <div className="actions">
                        <button
                          disabled={u.id === user?.id}
                          onClick={() => change(u, { is_active: !u.is_active })}
                        >
                          {u.is_active ? "비활성화" : "활성화"}
                        </button>
                        <button
                          disabled={u.id === user?.id}
                          onClick={() =>
                            change(u, {
                              role: u.role === "ADMIN" ? "USER" : "ADMIN",
                            })
                          }
                        >
                          역할 변경
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </QueryState>
        <Pagination
          page={page}
          total={query.data?.total || 0}
          onChange={setPage}
        />
      </section>
    </>
  );
}

export function AuditPage() {
  const [page, setPage] = useState(1),
    [search, setSearch] = useState("");
  type Audit = {
    id: string;
    actor_id: string;
    action: string;
    target_id: string;
    before_json: object;
    after_json: object;
    reason: string;
    request_id: string;
    ip_address: string;
    created_at: string;
  };
  const q = useQuery({
    queryKey: ["audit", page, search],
    queryFn: async () =>
      (
        await api.get<{ items: Audit[]; total: number }>("/admin/audit-logs", {
          params: { page, search },
        })
      ).data,
  });
  return (
    <>
      <div className="page-heading">
        <div>
          <div className="eyebrow">ACCOUNTABILITY</div>
          <h1>감사 로그</h1>
          <p>누가, 언제, 어떤 이유로 변경했는지 추적합니다.</p>
        </div>
      </div>
      <section className="card">
        <input
          value={search}
          placeholder="작업 종류 또는 대상 ID 검색"
          aria-label="감사 로그 검색"
          onChange={(e) => {
            setSearch(e.target.value);
            setPage(1);
          }}
        />
        <QueryState
          loading={q.isLoading}
          error={q.error}
          empty={!q.data?.items.length}
        >
          {q.data?.items.map((a) => (
            <article className="history" key={a.id}>
              <strong>{a.action}</strong>
              <span className="muted">
                {" "}
                · {new Date(a.created_at).toLocaleString()}
              </span>
              <p>{a.reason}</p>
              <small>
                작업자 {a.actor_id || "SYSTEM"} · 대상 {a.target_id}
                <br />
                요청 {a.request_id} · IP {a.ip_address}
              </small>
              <details>
                <summary>변경 전후 확인</summary>
                <div className="two-col">
                  <pre>{JSON.stringify(a.before_json, null, 2)}</pre>
                  <pre>{JSON.stringify(a.after_json, null, 2)}</pre>
                </div>
              </details>
            </article>
          ))}
        </QueryState>
        <Pagination page={page} total={q.data?.total || 0} onChange={setPage} />
      </section>
    </>
  );
}

export function SystemPage() {
  const q = useQuery({
    queryKey: ["system"],
    queryFn: async () => ({
      model: (await api.get<ModelStatus>("/system/model-status")).data,
      health: (await api.get("/health", { baseURL: "" })).data,
      ready: (await api.get("/ready", { baseURL: "" })).data,
    }),
  });
  return (
    <>
      <div className="page-heading">
        <div>
          <div className="eyebrow">SYSTEM & MODEL</div>
          <h1>시스템 상태</h1>
        </div>
        <button onClick={() => q.refetch()}>새로고침</button>
      </div>
      <QueryState loading={q.isLoading} error={q.error}>
        {q.data && (
          <section className="card">
            <h2>
              분석 엔진 <Badge status={q.data.model.mode} />
            </h2>
            <p>{q.data.model.notice}</p>
            <div className="metric-grid">
              {Object.entries({
                API: q.data.health.status,
                DB: q.data.ready.status,
                모델: q.data.model.name,
                버전: q.data.model.version,
                "모델 준비": q.data.model.ready
                  ? "준비됨"
                  : "모델 파일·계약 확인 필요",
                "원본 보존": `${q.data.model.original_retention_days}일`,
                "결과 보존": `${q.data.model.result_retention_days}일`,
              }).map(([k, v]) => (
                <div key={k}>
                  <span>{k}</span>
                  <strong>{String(v)}</strong>
                </div>
              ))}
            </div>
            <p>
              작업 큐: 단일 프로세스의 제한된 스레드 풀 · 모델 파일 부재 시 서버
              유지 및 분석 실패 기록
            </p>
            <a
              href="http://localhost:8000/docs"
              target="_blank"
              rel="noreferrer"
            >
              로컬 API 문서 열기
            </a>
          </section>
        )}
      </QueryState>
    </>
  );
}

export function NotFound() {
  return (
    <div className="state">
      <span className="eyebrow">404</span>
      <h1>페이지를 찾을 수 없습니다</h1>
      <Link className="button" to="/app">
        대시보드로 돌아가기
      </Link>
    </div>
  );
}
