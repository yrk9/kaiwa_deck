"use client";

import type { User } from "@supabase/supabase-js";
import { useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";

import {
  getLoginRedirectError,
  linkGoogle,
  type LoginRedirectError,
  signInWithGoogle,
  signOut,
} from "@/lib/auth";
import { supabase } from "@/lib/supabase";

type AuthState =
  | { status: "loading" }
  // まだ一度も使っていない(LPを開いただけ)、またはログアウトした直後
  | { status: "signedOut" }
  | {
      status: "ready";
      userId: string;
      // true ならゲスト。Googleアカウントをつなぐと false になる
      isAnonymous: boolean;
      email: string | null;
    };

function toState(user: User | undefined): AuthState {
  if (!user) return { status: "signedOut" };
  return {
    status: "ready",
    userId: user.id,
    isAnonymous: user.is_anonymous ?? false,
    email: user.email ?? null,
  };
}

// ログインの状態を返す。ログイン・ログアウトすると、自動で新しい状態になる
// 見るだけで、ゲストのログインは始めない(LPを開いただけでユーザーを作らないため)
export function useAuth(): AuthState {
  const [state, setState] = useState<AuthState>({ status: "loading" });

  useEffect(() => {
    // 登録した直後に、今の状態も1回届く
    const { data } = supabase.auth.onAuthStateChange((_event, session) => {
      setState(toState(session?.user));
    });
    return () => data.subscription.unsubscribe();
  }, []);

  return state;
}

// ログイン・ログアウトの操作。linkGoogle と signInWithGoogle はGoogleの画面へ移動する
export function useAuthActions() {
  const queryClient = useQueryClient();
  return {
    linkGoogle,
    signInWithGoogle,
    signOut: async () => {
      await signOut();
      // 前のユーザーのデッキが表示に残らないよう、取り直す
      await queryClient.resetQueries();
    },
  };
}

// Googleの画面から戻ってきたときの失敗。ヘッダーなど1か所で使う
export function useLoginRedirectError(): LoginRedirectError | null {
  const [error, setError] = useState<LoginRedirectError | null>(null);

  useEffect(() => {
    getLoginRedirectError().then(setError);
  }, []);

  return error;
}
