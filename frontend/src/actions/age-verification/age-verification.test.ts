import { clearAgeVerification, setAgeVerified } from "@/lib/age-verification";
import { redirect } from "next/navigation";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { confirmAgeVerification, declineAgeVerification } from "./age-verification";

// 依存関係をモック化
vi.mock("@/lib/age-verification", () => ({
  setAgeVerified: vi.fn(),
  clearAgeVerification: vi.fn(),
}));

vi.mock("next/navigation", () => ({
  redirect: vi.fn(),
}));

vi.mock("@/lib/logger", () => ({
  createLogger: () => ({
    info: vi.fn(),
    debug: vi.fn(),
    warn: vi.fn(),
    error: vi.fn(),
  }),
}));

describe("age-verification actions", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("confirmAgeVerification", () => {
    it("年齢認証を正常に確認する", async () => {
      (setAgeVerified as vi.MockedFunction<typeof setAgeVerified>).mockResolvedValue(undefined);

      await expect(confirmAgeVerification()).resolves.toBeUndefined();
      expect(setAgeVerified).toHaveBeenCalledTimes(1);
    });

    it("エラーが発生した場合は例外を投げる", async () => {
      const error = new Error("Cookie setting failed");
      (setAgeVerified as vi.MockedFunction<typeof setAgeVerified>).mockRejectedValue(error);

      await expect(confirmAgeVerification()).rejects.toThrow("年齢認証の確認に失敗しました");
      expect(setAgeVerified).toHaveBeenCalledTimes(1);
    });
  });

  describe("declineAgeVerification", () => {
    it("年齢認証を拒否してリダイレクトする", async () => {
      (clearAgeVerification as vi.MockedFunction<typeof clearAgeVerification>).mockResolvedValue(
        undefined,
      );
      (redirect as vi.MockedFunction<typeof redirect>).mockImplementation(() => {
        throw new Error("REDIRECT"); // redirectは例外を投げてフローを止める
      });

      await expect(declineAgeVerification()).rejects.toThrow("REDIRECT");
      expect(clearAgeVerification).toHaveBeenCalledTimes(1);
      expect(redirect).toHaveBeenCalledWith("https://www.google.com");
    });

    it("clearAgeVerificationでエラーが発生してもリダイレクトする", async () => {
      const error = new Error("Clear cookie failed");
      (clearAgeVerification as vi.MockedFunction<typeof clearAgeVerification>).mockRejectedValue(
        error,
      );
      (redirect as vi.MockedFunction<typeof redirect>).mockImplementation(() => {
        throw new Error("REDIRECT");
      });

      await expect(declineAgeVerification()).rejects.toThrow("REDIRECT");
      expect(clearAgeVerification).toHaveBeenCalledTimes(1);
      expect(redirect).toHaveBeenCalledWith("https://www.google.com");
    });
  });
});
