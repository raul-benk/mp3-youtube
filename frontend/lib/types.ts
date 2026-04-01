export type SourceType = "playlist" | "search" | "manual";

export type LinkItem = {
  id: string;
  url: string;
  selected: boolean;
};

export type CollectResponse = {
  urls: string[];
  invalid_count: number;
  duplicate_count: number;
};

export type DownloadResponse = {
  job_id: string;
  total_urls: number;
  invalid_count: number;
  duplicate_count: number;
};

export type DestinationOption = {
  label: string;
  path: string;
};

export type DestinationsResponse = {
  default_output_path: string;
  options: DestinationOption[];
};

export type SelectDirectoryResponse = {
  selected_path?: string | null;
  canceled: boolean;
};

export type JobItem = {
  url: string;
  status: "pending" | "downloading" | "done" | "error";
  message?: string | null;
};

export type JobStatus = {
  job_id: string;
  state: "queued" | "running" | "completed" | "completed_with_errors";
  total: number;
  completed: number;
  success: number;
  errors: number;
  progress: number;
  started_at: string;
  finished_at?: string | null;
  items: JobItem[];
};
