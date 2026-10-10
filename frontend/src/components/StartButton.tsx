"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "./ui/button";
import { ensureSession } from "@/lib/auth";

export function StartButton(props: { buttonName: string }) {
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const router = useRouter();

  async function handleButtonClick() {
    setIsProcessing(true);
    setErrorMessage(null);
    try {
      await ensureSession();
      router.push("/decks");
    } catch {
      setErrorMessage("ゲストログインに失敗しました。もう一度お試しください。");
      setIsProcessing(false);
    }
  }

  return (
    <div>
      <Button onClick={handleButtonClick} disabled={isProcessing}>
        {isProcessing ? "準備中" : props.buttonName}
      </Button>
      {errorMessage != null && (
        <p className="text-red-600 py-2">{errorMessage}</p>
      )}
    </div>
  );
}
