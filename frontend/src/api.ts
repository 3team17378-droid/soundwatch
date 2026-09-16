import axios from "axios";
export const api = axios.create({ baseURL: "/api/v1", timeout: 90000 });
api.interceptors.request.use((config) => {
  const token = sessionStorage.getItem("soundwatch-token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});
api.interceptors.response.use(
  (r) => r,
  (error) => {
    if (
      error.response?.status === 401 &&
      !error.config?.url?.includes("/auth/login")
    ) {
      sessionStorage.removeItem("soundwatch-token");
      window.dispatchEvent(new Event("soundwatch-expired"));
    }
    return Promise.reject(error);
  },
);
export function errorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) return detail.map((x) => x.msg).join(" · ");
    return error.response
      ? "요청을 처리하지 못했습니다. 다시 시도하세요."
      : "서버에 연결할 수 없습니다. 백엔드 실행 상태를 확인하세요.";
  }
  return error instanceof Error ? error.message : "오류가 발생했습니다.";
}
