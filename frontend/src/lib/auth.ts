import {
  isAuthImplicitGrantRedirectError,
  type Session,
} from "@supabase/supabase-js";

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

// ゲストのまま、Googleアカウントをつなぐ。作ったデッキはそのまま引き継がれる
// Googleの画面へ移動し、終わると今のページに戻ってくる
export async function linkGoogle(): Promise<void> {
  await ensureSession();
  const { error } = await supabase.auth.linkIdentity({
    provider: "google",
    options: { redirectTo: window.location.href },
  });
  if (error) throw error;
}

// 登録済みの人が、Googleアカウントでログインする(別の端末で使うときなど)
// その端末でゲストとして作ったものは、引き継がれない
export async function signInWithGoogle(): Promise<void> {
  const { error } = await supabase.auth.signInWithOAuth({
    provider: "google",
    options: { redirectTo: window.location.href },
  });
  if (error) throw error;
}

export async function signOut(): Promise<void> {
  const { error } = await supabase.auth.signOut();
  if (error) throw error;
}

// already_registered: つなごうとしたGoogleアカウントが、すでに別のユーザーで登録済み
export type LoginRedirectError = "already_registered" | "failed";

// Googleの画面から戻ってきたときの失敗を返す。失敗していなければ null
export async function getLoginRedirectError(): Promise<LoginRedirectError | null> {
  const { error } = await supabase.auth.initialize();
  if (!isAuthImplicitGrantRedirectError(error)) return null;

  // 再読み込みで同じ失敗を出さないよう、URLから取り除く
  window.history.replaceState(null, "", window.location.pathname);
  return error.details?.code === "identity_already_exists"
    ? "already_registered"
    : "failed";
}
