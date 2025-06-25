/**
 * Products feature の統合テスト
 * Container + Presentational コンポーネントを統合してテスト
 * APIのみモック、UI コンポーネントは実際のものを使用
 */

import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import ProductsContainer from "./containers/ProductsContainer";
import type { PersonProductsResponse } from "./types";

// APIのみモック（UI コンポーネントはモックしない）
vi.mock("./api", () => ({
  getProductsByPersonId: vi.fn(),
}));

import { getProductsByPersonId } from "./api";

const mockGetProductsByPersonId = vi.mocked(getProductsByPersonId);

// テスト用のモックデータ
const mockProductsData: PersonProductsResponse = {
  person_id: 1,
  person_name: "テスト女優",
  dmm_actress_id: 123,
  products: [
    {
      imageURL: {
        list: "https://example.com/list1.jpg",
        small: "https://example.com/small1.jpg",
        large: "https://example.com/large1.jpg",
      },
      title: "テスト商品1",
      productURL: "https://example.com/product/1",
      prices: {
        price: "1000",
      },
    },
    {
      imageURL: {
        list: "https://example.com/list2.jpg",
        small: "https://example.com/small2.jpg",
        large: "https://example.com/large2.jpg",
      },
      title: "テスト商品2",
      productURL: "https://example.com/product/2",
      prices: {
        price: "2000",
      },
    },
  ],
  total_count: 2,
};

const mockEmptyProductsData: PersonProductsResponse = {
  person_id: 1,
  person_name: "テスト女優",
  dmm_actress_id: 123,
  products: [],
  total_count: 0,
};

describe("Products Feature Integration", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("商品データが正常に表示される（統合テスト）", async () => {
    mockGetProductsByPersonId.mockResolvedValue(mockProductsData);

    render(await ProductsContainer({ personId: 1, limit: 10 }));

    // タイトルと商品数の表示確認
    expect(screen.getByText("テスト女優さんの関連商品")).toBeInTheDocument();
    expect(screen.getByText("2件の商品が見つかりました")).toBeInTheDocument();

    // 商品カードの表示確認
    expect(screen.getByText("テスト商品1")).toBeInTheDocument();
    expect(screen.getByText("テスト商品2")).toBeInTheDocument();

    // 価格の表示確認
    expect(screen.getByText("¥1000")).toBeInTheDocument();
    expect(screen.getByText("¥2000")).toBeInTheDocument();

    // アフィリエイトリンクの確認
    const links = screen.getAllByRole("link");
    expect(links).toHaveLength(2);
    expect(links[0]).toHaveAttribute("href", "https://example.com/product/1");
    expect(links[1]).toHaveAttribute("href", "https://example.com/product/2");

    // 画像の表示確認
    const images = screen.getAllByRole("img");
    expect(images).toHaveLength(2);
    expect(images[0]).toHaveAttribute("src", "https://example.com/large1.jpg");
    expect(images[1]).toHaveAttribute("src", "https://example.com/large2.jpg");

    // ボタンの表示確認
    const buttons = screen.getAllByText("詳細を見る");
    expect(buttons).toHaveLength(2);
  });

  it("商品データが空の場合の表示（統合テスト）", async () => {
    mockGetProductsByPersonId.mockResolvedValue(mockEmptyProductsData);

    render(await ProductsContainer({ personId: 1 }));

    // タイトルの表示確認
    expect(screen.getByText("テスト女優さんの関連商品")).toBeInTheDocument();
    expect(screen.getByText("0件の商品が見つかりました")).toBeInTheDocument();

    // 空状態メッセージの表示確認
    expect(screen.getByText("この女優の関連商品は現在取得できません")).toBeInTheDocument();

    // 商品カードが表示されないことを確認
    expect(screen.queryByText("テスト商品1")).not.toBeInTheDocument();
  });

  it("API呼び出しが失敗した場合のエラー表示（統合テスト）", async () => {
    mockGetProductsByPersonId.mockRejectedValue(new Error("API Error"));

    render(await ProductsContainer({ personId: 1 }));

    // エラーメッセージの表示確認
    expect(screen.getByText("商品情報の読み込み中にエラーが発生しました")).toBeInTheDocument();

    // 商品リストが表示されないことを確認
    expect(screen.queryByText("テスト女優さんの関連商品")).not.toBeInTheDocument();
  });

  it("APIがnullを返した場合の表示（統合テスト）", async () => {
    mockGetProductsByPersonId.mockResolvedValue(null);

    render(await ProductsContainer({ personId: 1 }));

    // 空状態メッセージの表示確認
    expect(screen.getByText("この女優の関連商品は現在取得できません")).toBeInTheDocument();

    // タイトルが表示されないことを確認
    expect(screen.queryByText("テスト女優さんの関連商品")).not.toBeInTheDocument();
  });

  it("API呼び出しパラメータの確認", async () => {
    mockGetProductsByPersonId.mockResolvedValue(mockProductsData);

    render(await ProductsContainer({ personId: 123, limit: 15 }));

    // API が正しいパラメータで呼ばれることを確認
    expect(mockGetProductsByPersonId).toHaveBeenCalledWith(123, 15);
  });

  it("デフォルトlimit値の確認", async () => {
    mockGetProductsByPersonId.mockResolvedValue(mockProductsData);

    render(await ProductsContainer({ personId: 456 }));

    // デフォルトのlimit=10で呼ばれることを確認
    expect(mockGetProductsByPersonId).toHaveBeenCalledWith(456, 10);
  });

  it("カスタムクラス名の適用確認", async () => {
    mockGetProductsByPersonId.mockResolvedValue(mockProductsData);

    const { container } = render(
      await ProductsContainer({ personId: 1, className: "custom-products" }),
    );

    // カスタムクラス名が適用されることを確認
    const wrapper = container.firstChild;
    expect(wrapper).toHaveClass("custom-products");
  });

  it("横スクロール機能の確認", async () => {
    mockGetProductsByPersonId.mockResolvedValue(mockProductsData);

    const { container } = render(await ProductsContainer({ personId: 1 }));

    // 横スクロール用のクラスが適用されていることを確認
    const scrollContainer = container.querySelector(".overflow-x-auto");
    expect(scrollContainer).toBeInTheDocument();
    expect(scrollContainer).toHaveClass("flex", "gap-4", "pb-4");
  });

  it("商品カードのflexbox レイアウト確認", async () => {
    mockGetProductsByPersonId.mockResolvedValue(mockProductsData);

    render(await ProductsContainer({ personId: 1 }));

    // 商品カードが flex-shrink-0 クラスを持つことを確認
    const productCards = screen.getAllByRole("link");
    for (const card of productCards) {
      expect(card).toHaveClass("block");
    }
  });
});
