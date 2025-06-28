import { server } from "@/test/mocks/server";
import { render, screen } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { beforeEach, describe, expect, it, vi } from "vitest";

// Next.js のモック設定
const mockPush = vi.fn();
const mockReplace = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({
    push: mockPush,
    replace: mockReplace,
  }),
  useSearchParams: () => new URLSearchParams(),
  usePathname: () => "/actresses",
}));

describe("ActressList Feature Integration Tests", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("Container → API → Presentation の完全な統合フロー", async () => {
    // Server Component を直接テストするのではなく、API関数とPresentation Componentを統合テスト
    const { getActressList } = await import("./api");
    const { ActressListPresentation } = await import("./presentations/ActressListPresentation");

    // API関数を直接呼び出してテスト
    const result = await getActressList();

    // API結果の検証（MSWが提供するデフォルトレスポンス）
    expect(result).toEqual({
      persons: [
        {
          person_id: 1,
          name: "AIKA",
          image_path: "http://pics.dmm.co.jp/mono/actjpgs/aika3.jpg",
          dmm_actress_id: 1008887,
        },
        {
          person_id: 2,
          name: "AIKA（三浦あいか）",
          image_path: "http://pics.dmm.co.jp/mono/actjpgs/miura_aika.jpg",
          dmm_actress_id: 1105,
        },
        {
          person_id: 3,
          name: "愛上みお",
          image_path: "http://pics.dmm.co.jp/mono/actjpgs/aiue_mio.jpg",
          dmm_actress_id: 1075314,
        },
      ],
      total_count: 13010,
      has_more: true,
    });

    // Presentation Component で結果を表示
    render(
      <ActressListPresentation
        actresses={result?.persons || []}
        totalCount={result?.total_count || 0}
        currentPage={1}
        itemsPerPage={20}
        searchQuery=""
        sortBy="name"
        isLoading={false}
        error={null}
      />,
    );

    // データが正しく表示されることを確認
    expect(screen.getByText("女優一覧")).toBeInTheDocument();
    expect(screen.getByText("AIKA")).toBeInTheDocument();
    expect(screen.getByText("AIKA（三浦あいか）")).toBeInTheDocument();
    expect(screen.getByText("愛上みお")).toBeInTheDocument();

    // 総数の表示確認
    expect(screen.getByText("13010名の女優が登録されています")).toBeInTheDocument();

    // ページネーション情報の確認
    expect(screen.getByText("1-20件 / 全13010件")).toBeInTheDocument();
    expect(screen.getByText("次へ")).toBeInTheDocument();
  });

  it("検索パラメータありでの統合フロー", async () => {
    // API関数を検索パラメータ付きで呼び出し
    const { getActressList } = await import("./api");
    const { ActressListPresentation } = await import("./presentations/ActressListPresentation");

    const result = await getActressList({ search: "AIKA", sort_by: "name" });

    // API結果の検証（MSWが検索パラメータに応じてフィルタリング）
    expect(result).toEqual({
      persons: [
        {
          person_id: 1,
          name: "AIKA",
          image_path: "http://pics.dmm.co.jp/mono/actjpgs/aika3.jpg",
          dmm_actress_id: 1008887,
        },
        {
          person_id: 2,
          name: "AIKA（三浦あいか）",
          image_path: "http://pics.dmm.co.jp/mono/actjpgs/miura_aika.jpg",
          dmm_actress_id: 1105,
        },
      ],
      total_count: 2,
      has_more: false,
    });

    // Presentation Component で結果を表示
    render(
      <ActressListPresentation
        actresses={result?.persons || []}
        totalCount={result?.total_count || 0}
        currentPage={1}
        itemsPerPage={20}
        searchQuery="AIKA"
        sortBy="name"
        isLoading={false}
        error={null}
      />,
    );

    // 検索結果のみが表示されることを確認
    expect(screen.getByText("女優一覧")).toBeInTheDocument();
    expect(screen.getByText("AIKA")).toBeInTheDocument();
    expect(screen.getByText("AIKA（三浦あいか）")).toBeInTheDocument();
    expect(screen.queryByText("愛上みお")).not.toBeInTheDocument();

    // 検索結果数の表示確認
    expect(screen.getByText("2名の女優が登録されています")).toBeInTheDocument();
  });

  it("ページネーション統合フロー", async () => {
    // API関数を2ページ目のパラメータで呼び出し
    const { getActressList } = await import("./api");
    const { ActressListPresentation } = await import("./presentations/ActressListPresentation");

    const result = await getActressList({ offset: 20 });

    // API結果の検証（MSWがオフセットに応じて異なるデータを返す）
    expect(result).toEqual({
      persons: [
        {
          person_id: 21,
          name: "テスト女優21",
          image_path: "http://example.com/test21.jpg",
          dmm_actress_id: 21,
        },
        {
          person_id: 22,
          name: "テスト女優22",
          image_path: "http://example.com/test22.jpg",
          dmm_actress_id: 22,
        },
      ],
      total_count: 13010,
      has_more: true,
    });

    // Presentation Component で結果を表示
    render(
      <ActressListPresentation
        actresses={result?.persons || []}
        totalCount={result?.total_count || 0}
        currentPage={2}
        itemsPerPage={20}
        searchQuery=""
        sortBy="name"
        isLoading={false}
        error={null}
      />,
    );

    // 2ページ目のデータが表示されることを確認
    expect(screen.getByText("女優一覧")).toBeInTheDocument();
    expect(screen.getByText("テスト女優21")).toBeInTheDocument();
    expect(screen.getByText("テスト女優22")).toBeInTheDocument();

    // ページネーション情報が正しく表示されることを確認
    expect(screen.getByText("21-40件 / 全13010件")).toBeInTheDocument();
  });

  it("API エラー時の統合エラーハンドリングフロー", async () => {
    // MSWでAPIエラーをシミュレート
    server.use(
      http.get("http://backend:10000/api/persons", () => {
        return HttpResponse.json({ error: "Internal Server Error" }, { status: 500 });
      }),
    );

    // API関数でエラーハンドリングテスト
    const { getActressList } = await import("./api");
    const { ActressListPresentation } = await import("./presentations/ActressListPresentation");

    const result = await getActressList();

    // API結果がnullになることを確認
    expect(result).toBeNull();

    // Presentation Component でエラー状態を表示
    render(
      <ActressListPresentation
        actresses={[]}
        totalCount={0}
        currentPage={1}
        itemsPerPage={20}
        searchQuery=""
        sortBy="name"
        isLoading={false}
        error="データの取得に失敗しました。しばらく時間をおいて再度お試しください。"
      />,
    );

    // エラーメッセージが表示されることを確認
    expect(screen.getByText("エラーが発生しました")).toBeInTheDocument();
    expect(
      screen.getByText("データの取得に失敗しました。しばらく時間をおいて再度お試しください。"),
    ).toBeInTheDocument();

    // データが表示されないことを確認
    expect(screen.queryByText("AIKA")).not.toBeInTheDocument();
  });

  it("空データ時の統合フロー", async () => {
    // MSWで空データレスポンスをシミュレート
    server.use(
      http.get("http://backend:10000/api/persons", () => {
        return HttpResponse.json({
          persons: [],
          total_count: 0,
          has_more: false,
        });
      }),
    );

    // API関数で空データテスト
    const { getActressList } = await import("./api");
    const { ActressListPresentation } = await import("./presentations/ActressListPresentation");

    const result = await getActressList();

    // API結果の検証
    expect(result).toEqual({
      persons: [],
      total_count: 0,
      has_more: false,
    });

    // Presentation Component で空状態を表示
    render(
      <ActressListPresentation
        actresses={result?.persons || []}
        totalCount={result?.total_count || 0}
        currentPage={1}
        itemsPerPage={20}
        searchQuery=""
        sortBy="name"
        isLoading={false}
        error={null}
      />,
    );

    // 空状態メッセージが表示されることを確認
    expect(screen.getByText("女優一覧")).toBeInTheDocument();
    expect(screen.getByText("女優が見つかりませんでした")).toBeInTheDocument();
    expect(screen.getByText("女優が登録されていません")).toBeInTheDocument();
  });

  it("ネットワークエラー時の統合エラーハンドリング", async () => {
    // MSWでネットワークエラーをシミュレート
    server.use(
      http.get("http://backend:10000/api/persons", () => {
        return HttpResponse.error();
      }),
    );

    // API関数でネットワークエラーテスト
    const { getActressList } = await import("./api");
    const { ActressListPresentation } = await import("./presentations/ActressListPresentation");

    const result = await getActressList();

    // API結果がnullになることを確認
    expect(result).toBeNull();

    // Presentation Component でエラー状態を表示
    render(
      <ActressListPresentation
        actresses={[]}
        totalCount={0}
        currentPage={1}
        itemsPerPage={20}
        searchQuery=""
        sortBy="name"
        isLoading={false}
        error="データの取得に失敗しました。しばらく時間をおいて再度お試しください。"
      />,
    );

    // ネットワークエラー時のエラーメッセージ確認
    expect(screen.getByText("エラーが発生しました")).toBeInTheDocument();
    expect(
      screen.getByText("データの取得に失敗しました。しばらく時間をおいて再度お試しください。"),
    ).toBeInTheDocument();
  });

  it("複数パラメータでの統合動作確認", async () => {
    // API関数を複数パラメータで呼び出し
    const { getActressList } = await import("./api");
    const { ActressListPresentation } = await import("./presentations/ActressListPresentation");

    const result = await getActressList({
      search: "あいだ",
      sort_by: "person_id",
    });

    // API結果の検証（MSWが検索パラメータに応じてフィルタリング）
    expect(result).toEqual({
      persons: [
        {
          person_id: 5,
          name: "あいだ希空",
          image_path: "http://pics.dmm.co.jp/mono/actjpgs/aida_noa.jpg",
          dmm_actress_id: 1080439,
        },
      ],
      total_count: 1,
      has_more: false,
    });

    // Presentation Component で結果を表示
    render(
      <ActressListPresentation
        actresses={result?.persons || []}
        totalCount={result?.total_count || 0}
        currentPage={1}
        itemsPerPage={20}
        searchQuery="あいだ"
        sortBy="person_id"
        isLoading={false}
        error={null}
      />,
    );

    // 結果が正しく表示されることを確認
    expect(screen.getByText("女優一覧")).toBeInTheDocument();
    expect(screen.getByText("あいだ希空")).toBeInTheDocument();
    expect(screen.getByText("1名の女優が登録されています")).toBeInTheDocument();
  });
});
