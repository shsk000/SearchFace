import { describe, expect, it } from "vitest";
import { cn } from "./utils";

describe("cn utility function", () => {
  it("単一のクラス名を正しく処理する", () => {
    const result = cn("text-red-500");
    expect(result).toBe("text-red-500");
  });

  it("複数のクラス名を結合する", () => {
    const result = cn("text-red-500", "bg-blue-100");
    expect(result).toBe("text-red-500 bg-blue-100");
  });

  it("条件付きクラス名を正しく処理する", () => {
    const isActive = true;
    const result = cn("base-class", isActive && "active-class");
    expect(result).toBe("base-class active-class");
  });

  it("falseの条件付きクラス名を除外する", () => {
    const isActive = false;
    const result = cn("base-class", isActive && "active-class");
    expect(result).toBe("base-class");
  });

  it("Tailwind CSSの競合するクラスを正しく処理する", () => {
    const result = cn("p-4", "p-8");
    expect(result).toBe("p-8");
  });

  it("オブジェクト形式のクラス名を処理する", () => {
    const result = cn({
      "text-red-500": true,
      "bg-blue-100": false,
      "font-bold": true,
    });
    expect(result).toBe("text-red-500 font-bold");
  });

  it("配列形式のクラス名を処理する", () => {
    const result = cn(["text-red-500", "bg-blue-100"], "font-bold");
    expect(result).toBe("text-red-500 bg-blue-100 font-bold");
  });

  it("undefined、null、空文字を正しく処理する", () => {
    const result = cn("base-class", undefined, null, "", "valid-class");
    expect(result).toBe("base-class valid-class");
  });

  it("複雑な混合パターンを処理する", () => {
    const isActive = true;
    const isDisabled = false;
    const result = cn(
      "base-class",
      {
        "active-class": isActive,
        "disabled-class": isDisabled,
      },
      ["hover:bg-gray-100", "focus:ring-2"],
      isActive && "extra-active",
      "final-class",
    );
    expect(result).toBe(
      "base-class active-class hover:bg-gray-100 focus:ring-2 extra-active final-class",
    );
  });

  it("Tailwind CSSの競合する複雑なクラスを正しくマージする", () => {
    const result = cn(
      "px-4 py-2",
      "px-6", // pxが競合
      "bg-red-500",
      "bg-blue-500", // bgが競合
    );
    expect(result).toBe("py-2 px-6 bg-blue-500");
  });
});
