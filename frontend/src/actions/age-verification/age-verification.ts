"use server";

import { clearAgeVerification, setAgeVerified } from "@/lib/age-verification";
import { createLogger } from "@/lib/logger";
import { redirect } from "next/navigation";

const logger = createLogger("AgeVerificationActions");

/**
 * 年齢認証を確認するサーバーアクション
 */
export async function confirmAgeVerification(): Promise<void> {
  try {
    logger.info("Age verification confirmation action triggered");
    await setAgeVerified();
    logger.info("Age verification confirmed successfully");
  } catch (error) {
    logger.error("Failed to confirm age verification", error);
    throw new Error("年齢認証の確認に失敗しました");
  }
}

/**
 * 年齢認証を拒否する場合のサーバーアクション
 */
export async function declineAgeVerification(): Promise<never> {
  try {
    logger.info("Age verification declined by user");
    await clearAgeVerification();

    // ブロックページまたは外部サイトにリダイレクト
    // 今回は適切な外部サイト（例：Google）にリダイレクト
    redirect("https://www.google.com");
  } catch (error) {
    logger.error("Failed to handle age verification decline", error);
    // エラーが発生してもGoogleにリダイレクト
    redirect("https://www.google.com");
  }
}
