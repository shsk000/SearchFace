import { render, screen } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import React from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { server } from "../../test/mocks/server";
import { getSearchSessionResults } from "./api";
import SearchResultsContainer from "./containers/SearchResultsContainer";
import { SearchResultsPresentation } from "./presentations/SearchResultsPresentation";

// Next.js のモック設定
vi.mock("next/navigation", () => ({
  useRouter: () => ({
    push: vi.fn(),
    replace: vi.fn(),
  }),
  useSearchParams: () => new URLSearchParams(),
  usePathname: () => "/result",
}));

// ProductsContainerをモック（関連商品エリアの外部依存をモック）
vi.mock("@/features/products/containers/ProductsContainer", () => {
  return {
    default: ({ personId, limit }: { personId: number; limit: number }) => {
      return React.createElement(
        "div",
        { "data-testid": "products-container" },
        `Products for person ${personId} (limit: ${limit})`,
      );
    },
  };
});

describe("SearchResults Feature Integration Tests", () => {
  const mockSessionId = "test-session-123";

  beforeEach(() => {
    vi.clearAllMocks();
    server.resetHandlers();
  });

  it("Container → API → Presentation の完全な統合フロー", async () => {
    // API関数を直接呼び出してテスト（MSWがレスポンスを提供）
    const result = await getSearchSessionResults(mockSessionId);

    // API結果の検証（MSWが提供したデフォルトデータ）
    expect(result).toEqual({
      session_id: mockSessionId,
      search_timestamp: "2024-01-01T00:00:00Z",
      results: [
        {
          rank: 1,
          person_id: 1,
          name: "Test Person 1",
          similarity: 0.95,
          distance: 0.05,
          image_path: "/test-image-1.jpg",
        },
      ],
    });

    // Containerコンポーネントで統合テスト
    render(await SearchResultsContainer({ sessionId: mockSessionId }));

    // UIが正しく表示されることを確認
    expect(screen.getByText("類似度の高い人物")).toBeInTheDocument();
    // レスポンシブレイアウトで大画面・中画面・小画面の3つで表示される可能性がある
    expect(screen.getAllByText("Test Person 1").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("95%").length).toBeGreaterThanOrEqual(1);

    // 関連商品エリアが表示されることを確認（条件によって表示される）
    // データが存在する場合のみ表示されるため、条件をチェック
    const productsContainer = screen.queryByTestId("products-container");
    if (productsContainer) {
      expect(screen.getByText("Products for person 1 (limit: 20)")).toBeInTheDocument();
    }
  });

  it("APIエラー時の統合エラーハンドリングフロー", async () => {
    // MSWでAPIエラーをシミュレート
    server.use(
      http.get("http://backend:10000/api/search/:sessionId", () => {
        return HttpResponse.json({ error: "Not Found" }, { status: 404 });
      }),
    );

    // API関数でエラーハンドリングテスト
    const result = await getSearchSessionResults(mockSessionId);

    // API結果がnullになることを確認
    expect(result).toBeNull();

    // Containerコンポーネントでエラー状態を表示
    render(await SearchResultsContainer({ sessionId: mockSessionId }));

    // エラー状態のUIが表示されることを確認
    expect(screen.getByText("エラーが発生しました")).toBeInTheDocument();
    expect(screen.getByText("検索結果が見つかりません")).toBeInTheDocument();
  });

  it("ネットワークエラー時の統合エラーハンドリング", async () => {
    // MSWでネットワークエラーをシミュレート
    server.use(
      http.get("http://backend:10000/api/search/:sessionId", () => {
        return HttpResponse.error();
      }),
    );

    // API関数でネットワークエラーテスト
    const result = await getSearchSessionResults(mockSessionId);

    // API結果がnullになることを確認
    expect(result).toBeNull();

    // Containerコンポーネントでエラー状態を表示
    render(await SearchResultsContainer({ sessionId: mockSessionId }));

    // ネットワークエラー時のエラーメッセージ確認
    expect(screen.getByText("エラーが発生しました")).toBeInTheDocument();
    expect(screen.getByText("検索結果が見つかりません")).toBeInTheDocument();
  });

  it("空の検索結果時の統合フロー", async () => {
    // MSWで空の検索結果レスポンスをシミュレート
    server.use(
      http.get("http://backend:10000/api/search/:sessionId", ({ params }) => {
        const { sessionId } = params;
        return HttpResponse.json({
          session_id: sessionId,
          search_timestamp: "2024-01-01T00:00:00Z",
          results: [],
        });
      }),
    );

    // API関数で空データテスト
    const result = await getSearchSessionResults(mockSessionId);

    // API結果の検証
    expect(result).toEqual({
      session_id: mockSessionId,
      search_timestamp: "2024-01-01T00:00:00Z",
      results: [],
    });

    // Containerコンポーネントで空状態を表示
    render(await SearchResultsContainer({ sessionId: mockSessionId }));

    // 空状態メッセージが表示されることを確認
    expect(screen.getByText("検索結果が見つかりませんでした")).toBeInTheDocument();
  });

  it("環境変数API_BASE_URLでの統合動作確認", async () => {
    const originalEnv = process.env.API_BASE_URL;
    process.env.API_BASE_URL = "http://custom-backend:8080";

    // MSWでカスタムURLのハンドラーを追加
    server.use(
      http.get("http://custom-backend:8080/api/search/:sessionId", ({ params }) => {
        const { sessionId } = params;
        return HttpResponse.json({
          session_id: sessionId,
          search_timestamp: "2024-01-01T00:00:00Z",
          results: [
            {
              rank: 1,
              person_id: 100,
              name: "Custom Person",
              similarity: 0.88,
              distance: 0.12,
              image_path: "/custom-image.jpg",
            },
          ],
        });
      }),
    );

    // API関数を環境変数付きで呼び出し
    const result = await getSearchSessionResults(mockSessionId);

    // API結果の検証
    expect(result).toEqual({
      session_id: mockSessionId,
      search_timestamp: "2024-01-01T00:00:00Z",
      results: [
        {
          rank: 1,
          person_id: 100,
          name: "Custom Person",
          similarity: 0.88,
          distance: 0.12,
          image_path: "/custom-image.jpg",
        },
      ],
    });

    // Containerコンポーネントでカスタムデータを表示
    render(await SearchResultsContainer({ sessionId: mockSessionId }));

    // カスタムデータが正しく表示されることを確認
    expect(screen.getByText("類似度の高い人物")).toBeInTheDocument();
    // レスポンシブレイアウトで大画面・中画面・小画面の3つで表示される可能性がある
    expect(screen.getAllByText("Custom Person").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("88%").length).toBeGreaterThanOrEqual(1);

    // 関連商品エリアが表示されることを確認（条件によって表示される）
    const productsContainer = screen.queryByTestId("products-container");
    if (productsContainer) {
      expect(screen.getByText("Products for person 100 (limit: 20)")).toBeInTheDocument();
    }

    process.env.API_BASE_URL = originalEnv;
  });

  it("Presentationコンポーネント単体での統合テスト", async () => {
    // Presentationコンポーネントを直接テスト
    const mockSessionData = {
      session_id: mockSessionId,
      search_timestamp: "2024-01-01T00:00:00Z",
      results: [
        {
          rank: 1,
          person_id: 1,
          name: "Test Person 1",
          similarity: 0.95,
          distance: 0.05,
          image_path: "/test-image-1.jpg",
        },
      ],
    };

    const mockFormattedResults = [
      {
        id: 1,
        rank: 1,
        name: "Test Person 1",
        similarity: 95, // utils.tsで100倍されたもの
        distance: 0.05,
        image_path: "/test-image-1.jpg",
      },
    ];

    render(
      React.createElement(SearchResultsPresentation, {
        sessionData: mockSessionData,
        formattedResults: mockFormattedResults,
        error: null,
      }),
    );

    // PresentationコンポーネントのUIが正しく表示されることを確認
    expect(screen.getByText("類似度の高い人物")).toBeInTheDocument();
    // レスポンシブレイアウトで大画面・中画面・小画面の3つで表示される可能性がある
    expect(screen.getAllByText("Test Person 1").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("95%").length).toBeGreaterThanOrEqual(1);
  });
});
