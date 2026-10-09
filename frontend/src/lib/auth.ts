import type { Session } from "@supabase/supabase-js";

import { supabase } from "@/lib/supabase";

let pending: Promise<Session> | null = null;

// ログイン済みならそのセッションを、まだならゲストとしてログインして返す
export function ensureSession(): Promise<Session> {
  // 同時に呼ばれても、ゲストログインは1回だけにする(ユーザーが増えるのを防ぐ)
  pending ??= loadSession().finally(() => {
    pending = null;
  });
  return pending;
}

export async function getAccessToken(): Promise<string> {
  return (await ensureSession()).access_token;
}

async function loadSession(): Promise<Session> {
  // 期限が切れていれば、ここで自動的に更新される
  const { data } = await supabase.auth.getSession();
  if (data.session) return data.session;

  const { data: signedIn, error } = await supabase.auth.signInAnonymously();
  if (error || !signedIn.session) {
    throw new Error(
      `ゲストログインに失敗しました: ${error?.message ?? "セッションがありません"}`,
    );
  }
  return signedIn.session;
}
