import { http, HttpResponse } from "msw";
import { describe, expect, it } from "vitest";
import { server } from "../../test/mocks/server";
import { getActressDetail, getDummyAffiliateProducts } from "./api";

describe("actress-detail API", () => {
  describe("getActressDetail", () => {
    it("should fetch actress detail successfully", async () => {
      const result = await getActressDetail(1);

      expect(result).toEqual({
        person_id: 1,
        name: "Test Actress 1",
        image_path: "/test-actress-1.jpg",
        search_count: 10,
      });
    });

    it("should throw error when actress not found", async () => {
      // Override the handler for this test
      server.use(
        http.get("http://backend:10000/api/persons/:personId", () => {
          return HttpResponse.json({ message: "Not found" }, { status: 404 });
        }),
      );

      await expect(getActressDetail(999)).rejects.toThrow("女優ID 999 が見つかりません");
    });

    it("should throw error on API error", async () => {
      // Override the handler for this test
      server.use(
        http.get("http://backend:10000/api/persons/:personId", () => {
          return HttpResponse.json({ message: "Internal error" }, { status: 500 });
        }),
      );

      await expect(getActressDetail(1)).rejects.toThrow("API エラー: 500");
    });

    it("should throw error on network failure", async () => {
      // Override the handler for this test
      server.use(
        http.get("http://backend:10000/api/persons/:personId", () => {
          return HttpResponse.error();
        }),
      );

      await expect(getActressDetail(1)).rejects.toThrow();
    });
  });

  describe("getDummyAffiliateProducts", () => {
    it("should generate dummy affiliate products", () => {
      const actressName = "Test Actress";
      const products = getDummyAffiliateProducts(actressName);

      expect(products).toHaveLength(3);
      expect(products[0]).toEqual({
        id: 1,
        title: "Test Actress FANZA 商品ダミー1",
        image: "/images/dummy_product1.jpg",
        link: "#",
      });
      expect(products[1]).toEqual({
        id: 2,
        title: "Test Actress FANZA 商品ダミー2",
        image: "/images/dummy_product2.jpg",
        link: "#",
      });
      expect(products[2]).toEqual({
        id: 3,
        title: "Test Actress FANZA 商品ダミー3",
        image: "/images/dummy_product3.jpg",
        link: "#",
      });
    });

    it("should include actress name in product titles", () => {
      const actressName = "田中美咲";
      const products = getDummyAffiliateProducts(actressName);

      for (const product of products) {
        expect(product.title).toContain(actressName);
      }
    });
  });
});
