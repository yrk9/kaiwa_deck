"use client";

import { useEffect, useState } from "react";

import { ensureSession } from "@/lib/auth";

type AuthState =
  | { status: "loading" }
  | { status: "ready"; userId: string }
  | { status: "error"; error: Error };

// ゲストログインの状態と、自分のuser_idを返す(作成者かどうかの判定などに使う)
export function useAuth(): AuthState {
  const [state, setState] = useState<AuthState>({ status: "loading" });

  useEffect(() => {
    let active = true;
    ensureSession()
      .then((session) => {
        if (active) setState({ status: "ready", userId: session.user.id });
      })
      .catch((error: Error) => {
        if (active) setState({ status: "error", error });
      });
    return () => {
      active = false;
    };
  }, []);

  return state;
}
