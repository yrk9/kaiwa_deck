"use client";

import { useState } from "react";

import { Button } from "@/components/ui/button";
import {
  useAuth,
  useAuthActions,
  useLoginRedirectError,
} from "@/hooks/useAuth";

// Googleの画面から戻ってきたときの失敗の文言
const redirectErrorMessages = {
  already_registered:
    "このGoogleアカウントは登録済みです。「ログイン」から入ってください",
  failed: "ログインに失敗しました。もう一度お試しください",
};

// ヘッダーに置く、ログインの状態に合わせたボタン
export function AuthButton() {
  const auth = useAuth();
  const { linkGoogle, signInWithGoogle, signOut } = useAuthActions();
  const redirectError = useLoginRedirectError();
  const [isPending, setIsPending] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  async function startGoogle(action: () => Promise<void>) {
    setIsPending(true);
    setActionError(null);
    try {
      // 成功するとGoogleの画面へ移動するので、ボタンは押せないままにする
      await action();
    } catch {
      setActionError("Googleの画面を開けませんでした。もう一度お試しください");
      setIsPending(false);
    }
  }

  async function handleSignOut() {
    setIsPending(true);
    setActionError(null);
    try {
      await signOut();
    } catch {
      setActionError("ログアウトできませんでした。もう一度お試しください");
    } finally {
      setIsPending(false);
    }
  }

  if (auth.status === "loading") {
    return null;
  }

  let buttons;
  if (auth.status === "signedOut") {
    buttons = (
      <Button
        size="sm"
        onClick={() => startGoogle(signInWithGoogle)}
        disabled={isPending}
      >
        Googleでログイン
      </Button>
    );
  } else if (auth.isAnonymous) {
    buttons = (
      <>
        <Button
          size="sm"
          variant="outline"
          onClick={() => startGoogle(signInWithGoogle)}
          disabled={isPending}
        >
          ログイン
        </Button>
        <Button
          size="sm"
          onClick={() => startGoogle(linkGoogle)}
          disabled={isPending}
          title="ゲストで作ったデッキを、Googleアカウントに引き継ぎます"
        >
          Googleで保存
        </Button>
      </>
    );
  } else {
    buttons = (
      <>
        <span className="hidden max-w-48 truncate text-sm text-muted-foreground sm:inline">
          {auth.email}
        </span>
        <Button
          size="sm"
          variant="outline"
          onClick={handleSignOut}
          disabled={isPending}
        >
          ログアウト
        </Button>
      </>
    );
  }

  const message =
    actionError ?? (redirectError && redirectErrorMessages[redirectError]);

  return (
    <div className="flex flex-col items-end gap-1">
      <div className="flex items-center gap-2">{buttons}</div>
      {message && (
        <p role="alert" className="max-w-64 text-right text-xs text-destructive">
          {message}
        </p>
      )}
    </div>
  );
}
