export type User = {
  id: string;
  email: string;
  name: string;
  role: "USER" | "ADMIN";
  is_active: boolean;
};
export type Analysis = {
  id: string;
  predicted_class: string | null;
  confidence: number | null;
  top_predictions_json: { class: string; probability: number }[];
  inference_mode: "DEMO" | "MODEL";
  model_name: string;
  model_version: string;
  inference_time_ms: number | null;
  average_dbfs: number;
  maximum_dbfs: number;
  rms: number;
  peak_amplitude: number;
  silence_ratio: number;
  low_confidence: boolean;
  error_message: string | null;
  features_json?: {
    waveform: number[];
    log_mel: number[][];
    sample_rate: number;
  };
  provenance_json?: Record<string, unknown>;
};
export type NoiseRecord = {
  id: string;
  title: string;
  description: string;
  occurred_at: string;
  latitude: number;
  longitude: number;
  address: string;
  status: string;
  duration: number;
  original_deleted_at: string | null;
  public_consent: boolean;
  deletion_requested_at: string | null;
  current_job_id: string;
  confirmed_class: string | null;
  analysis: Analysis | null;
  reviews: {
    id: string;
    previous_class: string;
    confirmed_class: string;
    comment: string;
    created_at: string;
  }[];
  analysis_history: Analysis[];
};
export type Job = {
  id: string;
  noise_record_id: string;
  stage: string;
  progress: number;
  events_json: { stage: string; at: string }[];
  error: string | null;
};
export type Filters = {
  start?: string;
  end?: string;
  noise_type?: string;
  status?: string;
  region?: string;
  user_id?: string;
  search?: string;
};
export type Count = { name: string; count: number };
export type Summary = {
  total: number;
  today: number;
  review_required: number;
  failed: number;
  average_inference_ms: number | null;
  average_dbfs: number | null;
  maximum_dbfs: number | null;
  agreement_rate: number | null;
  review_required_rate: number | null;
  upload_processing_success_rate: number | null;
  average_processing_ms: number | null;
  categories: Count[];
  hourly: Count[];
  weekday: Count[];
  regions: Count[];
  timeseries: Count[];
  scope: string;
  metrics: { note: string };
};
export type ModelStatus = {
  mode: string;
  name: string;
  version: string;
  ready: boolean;
  notice: string;
  classes: string[];
  max_upload_mb: number;
  max_duration_seconds: number;
  original_retention_days: number;
  result_retention_days: number;
};
export const CLASSES = [
  "자동차 경적",
  "엔진 및 차량",
  "공사 및 드릴",
  "사이렌",
  "개 짖는 소리",
  "음악",
  "사람 대화",
  "총성 또는 폭발음",
  "빗소리",
  "기타 환경음",
];
export const STATUSES: Record<string, string> = {
  PENDING: "분석 중",
  ANALYZED: "분석 완료",
  REVIEW_REQUIRED: "검토 필요",
  CONFIRMED: "확정",
  CORRECTED: "수정 완료",
  FAILED: "분석 실패",
  DELETED: "삭제됨",
};
export const STAGES: Record<string, string> = {
  UPLOADED: "업로드 완료",
  VALIDATING: "파일 검증",
  PREPROCESSING: "오디오 전처리",
  INFERENCING: "AI 추론",
  SAVING: "결과 저장",
  COMPLETED: "분석 완료",
  FAILED: "분석 실패",
};
