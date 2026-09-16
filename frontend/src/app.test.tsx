import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import { AuthContext, Guard } from "./auth";
import { FilterBar, QueryState } from "./components";
import { AnalysisView, validateFile } from "./pages";
import type { Analysis } from "./types";

describe("authorization", () => {
  it("redirects unauthenticated users", () => {
    render(
      <AuthContext.Provider
        value={{
          user: null,
          loading: false,
          login: async () => {},
          logout: () => {},
        }}
      >
        <MemoryRouter initialEntries={["/private"]}>
          <Routes>
            <Route element={<Guard />}>
              <Route path="/private" element={<p>private</p>} />
            </Route>
            <Route path="/login" element={<p>로그인 화면</p>} />
          </Routes>
        </MemoryRouter>
      </AuthContext.Provider>,
    );
    expect(screen.getByText("로그인 화면")).toBeInTheDocument();
  });
  it("blocks users from admin routes", () => {
    render(
      <AuthContext.Provider
        value={{
          user: {
            id: "1",
            name: "user",
            email: "u@example.com",
            role: "USER",
            is_active: true,
          },
          loading: false,
          login: async () => {},
          logout: () => {},
        }}
      >
        <MemoryRouter>
          <Guard admin />
        </MemoryRouter>
      </AuthContext.Provider>,
    );
    expect(screen.getByRole("alert")).toHaveTextContent("관리자 권한");
  });
});
describe("file validation", () => {
  it("rejects unsupported and empty audio", () => {
    expect(validateFile(new File(["abc"], "file.exe"))).toContain(
      "파일을 선택",
    );
    expect(validateFile(new File([], "file.wav"))).toContain("빈 파일");
    expect(validateFile(new File(["abc"], "file.wav"))).toBe("");
  });
  it("rejects oversized files", () =>
    expect(
      validateFile(new File([new Uint8Array(1024 * 1024 + 1)], "x.mp3"), 1),
    ).toContain("1MB"));
});
it("emits actual filter values", () => {
  const change = vi.fn();
  render(<FilterBar value={{}} onChange={change} />);
  fireEvent.change(screen.getByLabelText("소음 유형"), {
    target: { value: "빗소리" },
  });
  expect(change).toHaveBeenCalledWith({ noise_type: "빗소리" });
  fireEvent.click(screen.getByText("초기화"));
  expect(change).toHaveBeenLastCalledWith({});
});
it("shows API errors instead of an empty success view", () => {
  render(
    <QueryState loading={false} error={new Error("연결 실패")}>
      success
    </QueryState>,
  );
  expect(screen.getByRole("alert")).toHaveTextContent("연결 실패");
  expect(screen.queryByText("success")).not.toBeInTheDocument();
});
it("labels demo scores explicitly", () => {
  const a = {
    id: "x",
    inference_mode: "DEMO",
    predicted_class: "빗소리",
    top_predictions_json: [{ class: "빗소리", probability: 0.4 }],
    model_name: "demo",
    model_version: "1",
    inference_time_ms: 1,
    average_dbfs: -20,
    maximum_dbfs: -10,
    rms: 0.1,
    peak_amplitude: 0.3,
    silence_ratio: 0,
    low_confidence: true,
  } as Analysis;
  render(<AnalysisView a={a} />);
  expect(screen.getByText(/보정되지 않은 시연 점수/)).toBeInTheDocument();
  expect(screen.getByText("검토 필요")).toBeInTheDocument();
  expect(screen.getByText("-20 dBFS")).toBeInTheDocument();
});
