/**
 * Actress Detail feature の統合テスト
 * Container + Presentational コンポーネントを統合してテスト
 * APIのみモック、UI コンポーネントは実際のものを使用
 */

import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { ActressDetail } from "./api";
import ActressDetailContainer from "./containers/ActressDetailContainer";

// APIのみモック（UI コンポーネントはモックしない）
vi.mock("./api", () => ({
  getActressDetail: vi.fn(),
}));

// Next.js notFoundのモック
vi.mock("next/navigation", () => ({
  notFound: vi.fn(() => {
    throw new Error("Not Found");
  }),
}));

import { notFound } from "next/navigation";
import { getActressDetail } from "./api";

const mockGetActressDetail = vi.mocked(getActressDetail);
const mockNotFound = vi.mocked(notFound);

// テスト用のモックデータ
const mockActress: ActressDetail = {
  person_id: 1,
  name: "テスト女優",
  image_path: "https://example.com/actress.jpg",
  search_count: 42,
};

const mockActressWithoutImage: ActressDetail = {
  person_id: 2,
  name: "画像なし女優",
  image_path: "",
  search_count: 5,
};

const mockActressWithLongName: ActressDetail = {
  person_id: 3,
  name: "非常に長い名前の女優さんでテスト用",
  image_path: "https://example.com/long-name-actress.jpg",
  search_count: 100,
};

const mockActressWithZeroSearches: ActressDetail = {
  person_id: 4,
  name: "検索回数ゼロ女優",
  image_path: "https://example.com/zero-search-actress.jpg",
  search_count: 0,
};

const mockActressWithDmmUrl: ActressDetail = {
  person_id: 5,
  name: "FANZA URL付き女優",
  image_path: "https://example.com/actress.jpg",
  search_count: 25,
  dmm_list_url_digital: "https://al.dmm.co.jp/?lurl=https%3A%2F%2Fwww.dmm.co.jp%2F"
};

const mockActressWithoutDmmUrl: ActressDetail = {
  person_id: 6,
  name: "FANZA URLなし女優",
  image_path: "https://example.com/actress.jpg",
  search_count: 15,
  dmm_list_url_digital: undefined
};

describe("Actress Detail Feature Integration", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("女優詳細情報が正常に表示される（統合テスト）", async () => {
    mockGetActressDetail.mockResolvedValue(mockActress);

    render(await ActressDetailContainer({ personId: 1 }));

    // 女優名の表示確認
    expect(screen.getByText("テスト女優")).toBeInTheDocument();
    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent("テスト女優");

    // 検索回数の表示確認
    expect(screen.getByText("42回")).toBeInTheDocument();
    expect(screen.getByText("検索回数:")).toBeInTheDocument();

    // バッジの表示確認
    expect(screen.getByText("人気女優")).toBeInTheDocument();

    // プロフィール文の表示確認
    expect(screen.getByText(/人気急上昇中の注目女優です/)).toBeInTheDocument();
    expect(screen.getByText(/検索回数も42回を記録しています/)).toBeInTheDocument();

    // 画像の表示確認
    const image = screen.getByAltText("テスト女優");
    expect(image).toHaveAttribute("src", "https://example.com/actress.jpg");
    expect(image).toHaveClass("w-full", "max-w-md", "mx-auto", "rounded-xl");
  });

  it("画像がない場合のフォールバック表示（統合テスト）", async () => {
    mockGetActressDetail.mockResolvedValue(mockActressWithoutImage);

    render(await ActressDetailContainer({ personId: 2 }));

    // 女優名の表示確認
    expect(screen.getByText("画像なし女優")).toBeInTheDocument();

    // NO IMAGEフォールバックの表示確認
    expect(screen.getByText("NO IMAGE")).toBeInTheDocument();

    // フォールバック要素のスタイル確認
    const fallbackDiv = screen.getByText("NO IMAGE").parentElement;
    expect(fallbackDiv).toHaveClass(
      "w-full",
      "max-w-md",
      "mx-auto",
      "h-96",
      "rounded-xl",
      "bg-zinc-700",
    );

    // 検索回数の表示確認
    expect(screen.getByText("5回")).toBeInTheDocument();
  });

  it("API呼び出しが失敗した場合notFoundが呼ばれる（統合テスト）", async () => {
    mockGetActressDetail.mockRejectedValue(new Error("API Error"));

    await expect(async () => {
      render(await ActressDetailContainer({ personId: 999 }));
    }).rejects.toThrow("Not Found");

    // notFoundが呼ばれることを確認
    expect(mockNotFound).toHaveBeenCalled();
  });

  it("正しいパラメータでAPI関数が呼ばれる", async () => {
    mockGetActressDetail.mockResolvedValue(mockActress);

    render(await ActressDetailContainer({ personId: 123 }));

    // API が正しいパラメータで呼ばれることを確認
    expect(mockGetActressDetail).toHaveBeenCalledWith(123);
  });

  it("HTML構造とアクセシビリティが適切に設定される（統合テスト）", async () => {
    mockGetActressDetail.mockResolvedValue(mockActress);

    render(await ActressDetailContainer({ personId: 1 }));

    // 主要な見出しの確認
    const mainHeading = screen.getByRole("heading", { level: 1 });
    expect(mainHeading).toHaveTextContent("テスト女優");
    expect(mainHeading).toHaveClass("text-4xl", "font-bold", "text-white");

    // サブ見出しの確認
    const subHeading = screen.getByRole("heading", { level: 3 });
    expect(subHeading).toHaveTextContent("プロフィール");
    expect(subHeading).toHaveClass("text-lg", "font-semibold", "text-white");
  });

  it("カードコンポーネントのスタイリング確認（統合テスト）", async () => {
    mockGetActressDetail.mockResolvedValue(mockActress);

    const { container } = render(await ActressDetailContainer({ personId: 1 }));

    // Cardコンポーネントの確認
    const card = container.querySelector(".bg-zinc-800\\/90");
    expect(card).toBeInTheDocument();
    expect(card).toHaveClass("border-zinc-700");
  });

  it("レスポンシブグリッドレイアウトの確認（統合テスト）", async () => {
    mockGetActressDetail.mockResolvedValue(mockActress);

    const { container } = render(await ActressDetailContainer({ personId: 1 }));

    // グリッドレイアウトの確認
    const gridContainer = container.querySelector(".grid.md\\:grid-cols-2");
    expect(gridContainer).toBeInTheDocument();
    expect(gridContainer).toHaveClass("gap-8", "items-center");
  });

  it("アイコンコンポーネントの表示確認（統合テスト）", async () => {
    mockGetActressDetail.mockResolvedValue(mockActress);

    const { container } = render(await ActressDetailContainer({ personId: 1 }));

    // SVGアイコンが表示されることを確認
    const svgElements = container.querySelectorAll("svg");
    expect(svgElements.length).toBeGreaterThanOrEqual(2); // Heart + Search icons
  });

  it("バッジコンポーネントのスタイリング確認（統合テスト）", async () => {
    mockGetActressDetail.mockResolvedValue(mockActress);

    render(await ActressDetailContainer({ personId: 1 }));

    // バッジの表示とスタイル確認
    const badge = screen.getByText("人気女優").closest(".bg-pink-500");
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveClass("text-white", "hover:bg-pink-600");
  });

  it("検索回数が0の場合の表示確認（統合テスト）", async () => {
    mockGetActressDetail.mockResolvedValue(mockActressWithZeroSearches);

    render(await ActressDetailContainer({ personId: 4 }));

    // 検索回数0の表示確認
    expect(screen.getByText("0回")).toBeInTheDocument();
    expect(screen.getByText(/検索回数も0回を記録しています/)).toBeInTheDocument();
  });

  it("長い名前の女優の表示確認（統合テスト）", async () => {
    mockGetActressDetail.mockResolvedValue(mockActressWithLongName);

    render(await ActressDetailContainer({ personId: 3 }));

    // 長い名前が適切に表示される確認
    expect(screen.getByText("非常に長い名前の女優さんでテスト用")).toBeInTheDocument();
    expect(screen.getByText("100回")).toBeInTheDocument();
  });

  it("グラデーション装飾の確認（統合テスト）", async () => {
    mockGetActressDetail.mockResolvedValue(mockActress);

    const { container } = render(await ActressDetailContainer({ personId: 1 }));

    // グラデーション装飾の確認
    const gradientDiv = container.querySelector(".bg-gradient-to-t.from-black\\/20");
    expect(gradientDiv).toBeInTheDocument();
    expect(gradientDiv).toHaveClass("to-transparent", "rounded-xl");
  });

  it("dmm_list_url_digitalがある場合FANZA商品一覧ボタンが表示される", async () => {
    mockGetActressDetail.mockResolvedValue(mockActressWithDmmUrl);

    render(await ActressDetailContainer({ personId: 5 }));

    // FANZA商品一覧ボタンの表示確認
    const fanzaButton = screen.getByRole("link", { name: /FANZA商品一覧へ/ });
    expect(fanzaButton).toBeInTheDocument();
    expect(fanzaButton).toHaveAttribute("href", "https://al.dmm.co.jp/?lurl=https%3A%2F%2Fwww.dmm.co.jp%2F");
    expect(fanzaButton).toHaveAttribute("target", "_blank");
    expect(fanzaButton).toHaveAttribute("rel", "noopener noreferrer");
  });

  it("dmm_list_url_digitalがない場合FANZA商品一覧ボタンが表示されない", async () => {
    mockGetActressDetail.mockResolvedValue(mockActressWithoutDmmUrl);

    render(await ActressDetailContainer({ personId: 6 }));

    // FANZA商品一覧ボタンが表示されないことを確認
    const fanzaButton = screen.queryByRole("link", { name: /FANZA商品一覧へ/ });
    expect(fanzaButton).not.toBeInTheDocument();
  });

  it("FANZA商品一覧ボタンのアクセシビリティ確認", async () => {
    mockGetActressDetail.mockResolvedValue(mockActressWithDmmUrl);

    render(await ActressDetailContainer({ personId: 5 }));

    // ボタンのアクセシビリティ属性確認
    const fanzaButton = screen.getByRole("link", { name: /FANZA商品一覧へ/ });
    expect(fanzaButton).toHaveClass("bg-pink-600", "hover:bg-pink-700");
    
    // アイコンの表示確認
    const externalLinkIcon = fanzaButton.querySelector("svg");
    expect(externalLinkIcon).toBeInTheDocument();
  });

  it("FANZA商品一覧ボタンのスタイリング確認", async () => {
    mockGetActressDetail.mockResolvedValue(mockActressWithDmmUrl);

    render(await ActressDetailContainer({ personId: 5 }));

    // ボタンのスタイル確認
    const fanzaButton = screen.getByRole("link", { name: /FANZA商品一覧へ/ });
    expect(fanzaButton).toHaveClass(
      "inline-flex",
      "items-center",
      "gap-2",
      "bg-pink-600",
      "text-white",
      "px-4",
      "py-2",
      "rounded-lg",
      "font-medium",
      "transition-colors",
      "hover:bg-pink-700"
    );
  });

  it("dmm_list_url_digitalが空文字列の場合FANZA商品一覧ボタンが表示されない", async () => {
    mockGetActressDetail.mockResolvedValue({
      ...mockActressWithDmmUrl,
      dmm_list_url_digital: ""
    });

    render(await ActressDetailContainer({ personId: 5 }));

    // FANZA商品一覧ボタンが表示されないことを確認
    const fanzaButton = screen.queryByRole("link", { name: /FANZA商品一覧へ/ });
    expect(fanzaButton).not.toBeInTheDocument();
  });
});
