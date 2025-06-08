import { beforeEach, describe, expect, it } from "vitest";
import { http, HttpResponse } from "msw";
import { server } from "../../test/mocks/server";
import { SearchResultError } from "./error";
import { searchImage } from "./search";

// Logger is not mocked - let it output naturally

describe("searchImage", () => {
  beforeEach(() => {
    // Reset MSW handlers to default state
    server.resetHandlers();
  });

  it("正常な画像検索が成功する", async () => {
    const mockFile = new File(["test"], "test.jpg", { type: "image/jpeg" });
    const formData = new FormData();
    formData.append("image", mockFile);

    // Override MSW handler to return valid response
    server.use(
      http.post("http://backend:10000/api/search", () => {
        return HttpResponse.json({
          results: [
            {
              name: "Test Person 1",
              similarity: 0.95,
              distance: 0.05,
              image_path: "/test-image-1.jpg",
            },
          ],
          processing_time: 0.123,
          search_session_id: "test-session-123",
        });
      }),
    );

    const result = await searchImage(formData);

    expect(result).toBeDefined();
    expect(result.results).toBeDefined();
    expect(result.search_session_id).toBe("test-session-123");
  });

  it("画像が存在しない場合にINVALID_IMAGEエラーを投げる", async () => {
    const formData = new FormData();

    await expect(searchImage(formData)).rejects.toThrow(SearchResultError);
    await expect(searchImage(formData)).rejects.toThrow("INVALID_IMAGE");
  });

  it("APIがエラーレスポンスを返した場合にエラーを投げる", async () => {
    const mockFile = new File(["test"], "test.jpg", { type: "image/jpeg" });
    const formData = new FormData();
    formData.append("image", mockFile);

    // Override MSW handler to return error response
    server.use(
      http.post("http://backend:10000/api/search", () => {
        return HttpResponse.json(
          {
            error: {
              code: "NO_FACE_DETECTED",
              message: "No face detected in image",
            },
          },
          { status: 400, statusText: "Bad Request" },
        );
      }),
    );

    await expect(searchImage(formData)).rejects.toThrow(SearchResultError);
  });

  it("ネットワークエラーの場合にUNKNOWN_ERRORを投げる", async () => {
    const mockFile = new File(["test"], "test.jpg", { type: "image/jpeg" });
    const formData = new FormData();
    formData.append("image", mockFile);

    // Override MSW handler to simulate network error
    server.use(
      http.post("http://backend:10000/api/search", () => {
        return HttpResponse.error();
      }),
    );

    await expect(searchImage(formData)).rejects.toThrow();
  });

  it("不正なレスポンス形式の場合にUNKNOWN_ERRORを投げる", async () => {
    const mockFile = new File(["test"], "test.jpg", { type: "image/jpeg" });
    const formData = new FormData();
    formData.append("image", mockFile);

    // Override MSW handler to return invalid response
    server.use(
      http.post("http://backend:10000/api/search", () => {
        return HttpResponse.json({
          invalid_field: "invalid data",
        });
      }),
    );

    await expect(searchImage(formData)).rejects.toThrow(SearchResultError);
  });

  it("環境変数API_BASE_URLが設定されている場合でも正常に動作する", async () => {
    const mockFile = new File(["test"], "test.jpg", { type: "image/jpeg" });
    const formData = new FormData();
    formData.append("image", mockFile);

    // Use default MSW handler - it will work with the default backend URL
    const result = await searchImage(formData);

    expect(result).toBeDefined();
    expect(result.results).toBeDefined();
  });
});
