import { render, screen } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { server } from "../../test/mocks/server";
import SearchRanking from "./SearchRanking";
import { getRankingData } from "./api";

// Next.js のモック設定
vi.mock("next/navigation", () => ({
  useRouter: () => ({
    push: vi.fn(),
    replace: vi.fn(),
  }),
  useSearchParams: () => new URLSearchParams(),
  usePathname: () => "/",
}));

describe("Ranking Feature Integration Tests", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    server.resetHandlers();
  });

  it("API → Component の完全な統合フロー", async () => {
    // API関数を直接呼び出してテスト（MSWがレスポンスを提供）
    const result = await getRankingData();

    // API結果の検証（MSWが提供したデフォルトデータ）
    expect(result).toEqual({
      ranking: [
        {
          rank: 1,
          person_id: 1,
          name: "Test Person 1",
          win_count: 150,
          last_win_date: "2024-01-01T00:00:00Z",
          image_path: "/test-image-1.jpg",
        },
        {
          rank: 2,
          person_id: 2,
          name: "Test Person 2",
          win_count: 120,
          last_win_date: "2024-01-02T00:00:00Z",
          image_path: "/test-image-2.jpg",
        },
      ],
      total_count: 2,
    });

    // Server Componentを直接テストはできないため、コンポーネントの描画をテスト
    // （実際のプロジェクトではContainer/Presentationalパターンを推奨）
    render(await SearchRanking());

    // UIが正しく表示されることを確認
    expect(screen.getByText("検索ランキング TOP2")).toBeInTheDocument();
    expect(screen.getByText("Test Person 1")).toBeInTheDocument();
    expect(screen.getByText("Test Person 2")).toBeInTheDocument();
    expect(screen.getByText("検索回数:150回")).toBeInTheDocument();
    expect(screen.getByText("検索回数:120回")).toBeInTheDocument();
  });

  it("APIエラー時の統合エラーハンドリングフロー", async () => {
    // MSWでAPIエラーをシミュレート
    server.use(
      http.get("http://backend:10000/api/ranking", () => {
        return HttpResponse.json({ error: "Internal Server Error" }, { status: 500 });
      }),
    );

    // API関数でエラーハンドリングテスト
    const result = await getRankingData();

    // API結果がnullになることを確認
    expect(result).toBeNull();

    // コンポーネントでエラー状態を表示
    render(await SearchRanking());

    // エラー状態のUIが表示されることを確認
    expect(screen.getByText("検索ランキング")).toBeInTheDocument();
    expect(screen.getByText("ランキングデータがありません")).toBeInTheDocument();
  });

  it("ネットワークエラー時の統合エラーハンドリング", async () => {
    // MSWでネットワークエラーをシミュレート
    server.use(
      http.get("http://backend:10000/api/ranking", () => {
        return HttpResponse.error();
      }),
    );

    // API関数でネットワークエラーテスト
    const result = await getRankingData();

    // API結果がnullになることを確認
    expect(result).toBeNull();

    // コンポーネントでエラー状態を表示
    render(await SearchRanking());

    // ネットワークエラー時のエラーメッセージ確認
    expect(screen.getByText("ランキングデータがありません")).toBeInTheDocument();
  });

  it("空データ時の統合フロー", async () => {
    // MSWで空データレスポンスをシミュレート
    server.use(
      http.get("http://backend:10000/api/ranking", () => {
        return HttpResponse.json({
          ranking: [],
          total_count: 0,
        });
      }),
    );

    // API関数で空データテスト
    const result = await getRankingData();

    // API結果の検証
    expect(result).toEqual({
      ranking: [],
      total_count: 0,
    });

    // コンポーネントで空状態を表示
    render(await SearchRanking());

    // 空状態メッセージが表示されることを確認
    expect(screen.getByText("検索ランキング")).toBeInTheDocument();
    expect(screen.getByText("ランキングデータがありません")).toBeInTheDocument();
  });

  it("環境変数API_BASE_URLでの統合動作確認", async () => {
    const originalEnv = process.env.API_BASE_URL;
    process.env.API_BASE_URL = "http://custom-backend:8080";

    // MSWでカスタムURLのハンドラーを追加
    server.use(
      http.get("http://custom-backend:8080/api/ranking", () => {
        return HttpResponse.json({
          ranking: [
            {
              rank: 1,
              person_id: 100,
              name: "Custom Person",
              win_count: 300,
              last_win_date: "2024-01-01T00:00:00Z",
              image_path: "/custom-image.jpg",
            },
          ],
          total_count: 1,
        });
      }),
    );

    // API関数を環境変数付きで呼び出し
    const result = await getRankingData();

    // API結果の検証
    expect(result).toEqual({
      ranking: [
        {
          rank: 1,
          person_id: 100,
          name: "Custom Person",
          win_count: 300,
          last_win_date: "2024-01-01T00:00:00Z",
          image_path: "/custom-image.jpg",
        },
      ],
      total_count: 1,
    });

    // コンポーネントでカスタムデータを表示
    render(await SearchRanking());

    // カスタムデータが正しく表示されることを確認
    expect(screen.getByText("検索ランキング TOP1")).toBeInTheDocument();
    expect(screen.getByText("Custom Person")).toBeInTheDocument();
    expect(screen.getByText("検索回数:300回")).toBeInTheDocument();

    process.env.API_BASE_URL = originalEnv;
  });
});
