import { http, HttpResponse } from "msw";
import { beforeEach, describe, expect, it } from "vitest";
import { server } from "../../test/mocks/server";
import { getSearchSessionResults } from "./api";

// Logger is not mocked - let it output naturally

describe("getSearchSessionResults", () => {
  const mockSessionId = "test-session-123";

  beforeEach(() => {
    // Reset MSW handlers to default state
    server.resetHandlers();
  });

  it("検索セッション結果を正常に取得できる", async () => {
    // Use default MSW handler - no need to override
    const result = await getSearchSessionResults(mockSessionId);

    expect(result).toBeDefined();
    expect(result?.session_id).toBe(mockSessionId);
    expect(result?.results).toBeDefined();
    expect(Array.isArray(result?.results)).toBe(true);
  });

  it("APIレスポンスがエラーの場合nullを返す", async () => {
    // Override MSW handler for this test
    server.use(
      http.get("http://backend:10000/api/search/:sessionId", () => {
        return new HttpResponse(null, { status: 404, statusText: "Not Found" });
      }),
    );

    const result = await getSearchSessionResults(mockSessionId);

    expect(result).toBeNull();
  });

  it("ネットワークエラーの場合nullを返す", async () => {
    // Override MSW handler to simulate network error
    server.use(
      http.get("http://backend:10000/api/search/:sessionId", () => {
        return HttpResponse.error();
      }),
    );

    const result = await getSearchSessionResults(mockSessionId);

    expect(result).toBeNull();
  });

  it("環境変数API_BASE_URLが設定されている場合そのURLを使用する", async () => {
    const originalEnv = process.env.API_BASE_URL;
    process.env.API_BASE_URL = "http://custom-backend:8080";

    // Override MSW handler for custom URL
    server.use(
      http.get("http://custom-backend:8080/api/search/:sessionId", ({ params }) => {
        const { sessionId } = params;
        return HttpResponse.json({
          session_id: sessionId,
          results: [],
          created_at: "2024-01-01T00:00:00Z",
        });
      }),
    );

    const result = await getSearchSessionResults(mockSessionId);

    expect(result).toBeDefined();
    expect(result?.session_id).toBe(mockSessionId);
    expect(result?.results).toEqual([]);

    process.env.API_BASE_URL = originalEnv;
  });

  it("空のsessionIdでも正常に処理される", async () => {
    const emptySessionId = "";

    // Set environment variable to ensure API base URL is defined
    const originalEnv = process.env.API_BASE_URL;
    process.env.API_BASE_URL = "http://backend:10000";

    // Override MSW handler for empty session ID
    server.use(
      http.get("http://backend:10000/api/search/", () => {
        return HttpResponse.json({
          session_id: emptySessionId,
          results: [],
          created_at: "2024-01-01T00:00:00Z",
        });
      }),
    );

    const result = await getSearchSessionResults(emptySessionId);

    expect(result).toBeDefined();
    expect(result?.session_id).toBe(emptySessionId);
    expect(result?.results).toEqual([]);

    // Clean up
    process.env.API_BASE_URL = originalEnv;
  });
});
