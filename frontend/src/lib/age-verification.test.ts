import { cookies } from "next/headers";
import { beforeEach, describe, expect, it, vi } from "vitest";
import {
  AGE_VERIFICATION_VALUE,
  clearAgeVerification,
  isAgeVerified,
  setAgeVerified,
} from "./age-verification";

// next/headers モックを作成
vi.mock("next/headers", () => ({
  cookies: vi.fn(),
}));

// logger モックを作成
vi.mock("@/lib/logger", () => ({
  createLogger: () => ({
    info: vi.fn(),
    debug: vi.fn(),
    warn: vi.fn(),
    error: vi.fn(),
  }),
}));

describe("age-verification", () => {
  const mockCookieStore = {
    get: vi.fn(),
    set: vi.fn(),
    delete: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
    (cookies as vi.MockedFunction<typeof cookies>).mockResolvedValue(mockCookieStore);
  });

  describe("isAgeVerified", () => {
    it("年齢認証Cookieが正しい値の場合はtrueを返す", async () => {
      mockCookieStore.get.mockReturnValue({
        value: AGE_VERIFICATION_VALUE,
      });

      const result = await isAgeVerified();
      expect(result).toBe(true);
      expect(mockCookieStore.get).toHaveBeenCalledWith("age_verified");
    });

    it("年齢認証Cookieが存在しない場合はfalseを返す", async () => {
      mockCookieStore.get.mockReturnValue(undefined);

      const result = await isAgeVerified();
      expect(result).toBe(false);
    });

    it("年齢認証Cookieの値が間違っている場合はfalseを返す", async () => {
      mockCookieStore.get.mockReturnValue({
        value: "invalid_value",
      });

      const result = await isAgeVerified();
      expect(result).toBe(false);
    });

    it("エラーが発生した場合はfalseを返す", async () => {
      mockCookieStore.get.mockRejectedValue(new Error("Cookie error"));

      const result = await isAgeVerified();
      expect(result).toBe(false);
    });
  });

  describe("setAgeVerified", () => {
    it("年齢認証Cookieを正しく設定する", async () => {
      await setAgeVerified();

      expect(mockCookieStore.set).toHaveBeenCalledWith("age_verified", AGE_VERIFICATION_VALUE, {
        httpOnly: false,
        secure: false, // NODE_ENV が production でない場合
        sameSite: "strict",
        maxAge: 365 * 24 * 60 * 60, // 1年
        path: "/",
      });
    });

    it("production環境ではsecureフラグがtrueになる", async () => {
      const originalEnv = process.env.NODE_ENV;
      process.env.NODE_ENV = "production";

      await setAgeVerified();

      expect(mockCookieStore.set).toHaveBeenCalledWith(
        "age_verified",
        AGE_VERIFICATION_VALUE,
        expect.objectContaining({
          secure: true,
        }),
      );

      process.env.NODE_ENV = originalEnv;
    });

    it("エラーが発生した場合は例外を投げる", async () => {
      (cookies as vi.MockedFunction<typeof cookies>).mockRejectedValue(new Error("Cookie set error"));

      await expect(setAgeVerified()).rejects.toThrow("年齢認証の設定に失敗しました");
    });
  });

  describe("clearAgeVerification", () => {
    it("年齢認証Cookieを削除する", async () => {
      await clearAgeVerification();

      expect(mockCookieStore.delete).toHaveBeenCalledWith("age_verified");
    });

    it("エラーが発生した場合は例外を投げる", async () => {
      (cookies as vi.MockedFunction<typeof cookies>).mockRejectedValue(new Error("Cookie delete error"));

      await expect(clearAgeVerification()).rejects.toThrow("年齢認証のクリアに失敗しました");
    });
  });
});
