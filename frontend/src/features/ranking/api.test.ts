import { http, HttpResponse } from "msw";
import { beforeEach, describe, expect, it } from "vitest";
import { server } from "../../test/mocks/server";
import { getRankingData } from "./api";

// Logger is not mocked - let it output naturally

describe("getRankingData", () => {
  beforeEach(() => {
    // Reset MSW handlers to default state
    server.resetHandlers();
  });

  it("ランキングデータを正常に取得できる", async () => {
    // Use default MSW handler - no need to override
    const result = await getRankingData();

    expect(result).toBeDefined();
    expect(result?.ranking).toBeDefined();
    expect(Array.isArray(result?.ranking)).toBe(true);
  });

  it("APIレスポンスがエラーの場合nullを返す", async () => {
    // Override MSW handler for this test
    server.use(
      http.get("http://backend:10000/api/ranking", () => {
        return new HttpResponse(null, { status: 500, statusText: "Internal Server Error" });
      }),
    );

    const result = await getRankingData();

    expect(result).toBeNull();
  });

  it("ネットワークエラーの場合nullを返す", async () => {
    // Override MSW handler to simulate network error
    server.use(
      http.get("http://backend:10000/api/ranking", () => {
        return HttpResponse.error();
      }),
    );

    const result = await getRankingData();

    expect(result).toBeNull();
  });

  it("環境変数API_BASE_URLが設定されている場合そのURLを使用する", async () => {
    const originalEnv = process.env.API_BASE_URL;
    process.env.API_BASE_URL = "http://custom-backend:8080";

    // Override MSW handler for custom URL
    server.use(
      http.get("http://custom-backend:8080/api/ranking", () => {
        return HttpResponse.json({ ranking: [] });
      }),
    );

    const result = await getRankingData();

    expect(result).toBeDefined();
    expect(result?.ranking).toEqual([]);

    process.env.API_BASE_URL = originalEnv;
  });
});
