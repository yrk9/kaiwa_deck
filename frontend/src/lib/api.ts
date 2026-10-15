import { getAccessToken } from "@/lib/auth";

const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;

if (!baseUrl) {
  throw new Error(
    "NEXT_PUBLIC_API_BASE_URL を frontend/.env.local に設定してください",
  );
}

// APIがエラーを返したときの例外。status で 403 や 409 などを見分ける
export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

type RequestOptions = {
  method?: "GET" | "POST" | "PUT" | "DELETE";
  body?: unknown;
};

// APIを呼ぶ。ログイン(ゲストログイン含む)とトークンの付与は、ここで行う
// パスは必ず末尾に / を付ける(例: "/deck/")。付けないとリダイレクトされ、CORSで失敗する
export async function api<T>(
  path: string,
  { method = "GET", body }: RequestOptions = {},
): Promise<T> {
  const token = await getAccessToken();
  const hasBody = body !== undefined;

  const res = await fetch(`${baseUrl}${path}`, {
    method,
    headers: {
      Authorization: `Bearer ${token}`,
      ...(hasBody && { "Content-Type": "application/json" }),
    },
    body: hasBody ? JSON.stringify(body) : undefined,
  });

  if (!res.ok) {
    throw new ApiError(res.status, await readErrorMessage(res));
  }
  // 削除(204)は、返す中身が無い
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

async function readErrorMessage(res: Response): Promise<string> {
  try {
    const detail = (await res.json())?.detail;
    if (typeof detail === "string") return detail;
    // 入力チェックのエラー(422)は、項目ごとのメッセージの配列で返ってくる
    if (Array.isArray(detail)) return detail.map((d) => d.msg).join(", ");
  } catch {
    // JSONでないときは、下のステータスの文言を使う
  }
  return res.statusText || `HTTP ${res.status}`;
}
