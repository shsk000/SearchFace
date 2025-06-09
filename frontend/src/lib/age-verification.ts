import { createLogger } from "@/lib/logger";
import { cookies } from "next/headers";

const logger = createLogger("AgeVerificationLib");

const AGE_VERIFICATION_COOKIE_NAME = "age_verified";
const COOKIE_MAX_AGE = 365 * 24 * 60 * 60; // 1年（秒単位）

/**
 * 年齢認証のCookie値
 */
export const AGE_VERIFICATION_VALUE = "confirmed";

/**
 * 年齢認証の状態を確認する
 * @returns 年齢認証済みかどうか
 */
export async function isAgeVerified(): Promise<boolean> {
  try {
    const cookieStore = await cookies();
    const ageVerificationCookie = cookieStore.get(AGE_VERIFICATION_COOKIE_NAME);

    const isVerified = ageVerificationCookie?.value === AGE_VERIFICATION_VALUE;

    logger.debug("Age verification status checked", {
      isVerified,
      cookieValue: ageVerificationCookie?.value || "not_found",
    });

    return isVerified;
  } catch (error) {
    logger.error("Failed to check age verification status", error);
    return false;
  }
}

/**
 * 年齢認証を設定する
 */
export async function setAgeVerified(): Promise<void> {
  try {
    const cookieStore = await cookies();

    cookieStore.set(AGE_VERIFICATION_COOKIE_NAME, AGE_VERIFICATION_VALUE, {
      httpOnly: false,
      secure: process.env.NODE_ENV === "production",
      sameSite: "strict",
      maxAge: COOKIE_MAX_AGE,
      path: "/",
    });

    logger.info("Age verification cookie set successfully");
  } catch (error) {
    logger.error("Failed to set age verification cookie", error);
    throw new Error("年齢認証の設定に失敗しました");
  }
}

/**
 * 年齢認証をクリアする（テスト用途など）
 */
export async function clearAgeVerification(): Promise<void> {
  try {
    const cookieStore = await cookies();
    cookieStore.delete(AGE_VERIFICATION_COOKIE_NAME);

    logger.info("Age verification cookie cleared");
  } catch (error) {
    logger.error("Failed to clear age verification cookie", error);
    throw new Error("年齢認証のクリアに失敗しました");
  }
}
