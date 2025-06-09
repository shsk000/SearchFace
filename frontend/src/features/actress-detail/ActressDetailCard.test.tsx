import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ActressDetailCard } from "./ActressDetailCard";
import type { ActressDetail, AffiliateProduct } from "./api";

const mockActress: ActressDetail = {
  person_id: 1,
  name: "Test Actress",
  image_path: "/test-image.jpg",
  search_count: 10,
};

const mockProducts: AffiliateProduct[] = [
  {
    id: 1,
    title: "Test Actress FANZA 商品ダミー1",
    image: "/product1.jpg",
    link: "#",
  },
  {
    id: 2,
    title: "Test Actress FANZA 商品ダミー2",
    image: "/product2.jpg",
    link: "#",
  },
];

describe("ActressDetailCard", () => {
  it("should render actress information correctly", () => {
    render(<ActressDetailCard actress={mockActress} products={mockProducts} />);

    // 女優名が表示されている
    expect(screen.getByText("Test Actress")).toBeInTheDocument();

    // 検索回数が表示されている
    expect(screen.getByText("10回")).toBeInTheDocument();

    // 画像が表示されている
    const image = screen.getByAltText("Test Actress");
    expect(image).toBeInTheDocument();
    expect(image).toHaveAttribute("src", "/test-image.jpg");
  });

  it("should render affiliate products correctly", () => {
    render(<ActressDetailCard actress={mockActress} products={mockProducts} />);

    // 関連商品セクションが表示されている
    expect(screen.getByText("関連商品")).toBeInTheDocument();

    // 商品が表示されている
    expect(screen.getByText("Test Actress FANZA 商品ダミー1")).toBeInTheDocument();
    expect(screen.getByText("Test Actress FANZA 商品ダミー2")).toBeInTheDocument();

    // 詳細ボタンが表示されている
    const detailButtons = screen.getAllByText("詳細");
    expect(detailButtons).toHaveLength(2);
  });

  it("should show NO IMAGE when image_path is empty", () => {
    const actressWithoutImage = { ...mockActress, image_path: "" };
    render(<ActressDetailCard actress={actressWithoutImage} products={mockProducts} />);

    expect(screen.getByText("NO IMAGE")).toBeInTheDocument();
  });

  it("should show NO IMAGE when image_path is null", () => {
    const actressWithoutImage = { ...mockActress, image_path: null };
    render(<ActressDetailCard actress={actressWithoutImage} products={mockProducts} />);

    expect(screen.getByText("NO IMAGE")).toBeInTheDocument();
  });

  it("should render with zero search count", () => {
    const actressWithZeroCount = { ...mockActress, search_count: 0 };
    render(<ActressDetailCard actress={actressWithZeroCount} products={mockProducts} />);

    expect(screen.getByText("0回")).toBeInTheDocument();
  });

  it("should render profile description with search count", () => {
    render(<ActressDetailCard actress={mockActress} products={mockProducts} />);

    const description = screen.getByText(/検索回数も10回を記録しています/);
    expect(description).toBeInTheDocument();
  });

  it("should render empty products list", () => {
    render(<ActressDetailCard actress={mockActress} products={[]} />);

    // 関連商品セクションは表示される
    expect(screen.getByText("関連商品")).toBeInTheDocument();

    // 商品は表示されない
    expect(screen.queryByText("Test Actress FANZA 商品ダミー1")).not.toBeInTheDocument();
  });
});
