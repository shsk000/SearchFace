import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { Button } from "./button";

describe("Button", () => {
  it("デフォルトのボタンがレンダリングされる", () => {
    render(<Button>Click me</Button>);

    const button = screen.getByRole("button", { name: "Click me" });
    expect(button).toBeInTheDocument();
    expect(button).toHaveAttribute("data-slot", "button");
  });

  it("variant propsが正しく適用される", () => {
    render(<Button variant="destructive">Delete</Button>);

    const button = screen.getByRole("button", { name: "Delete" });
    expect(button).toHaveClass("bg-destructive");
  });

  it("size propsが正しく適用される", () => {
    render(<Button size="lg">Large Button</Button>);

    const button = screen.getByRole("button", { name: "Large Button" });
    expect(button).toHaveClass("h-10");
  });

  it("カスタムclassNameが適用される", () => {
    render(<Button className="custom-class">Custom</Button>);

    const button = screen.getByRole("button", { name: "Custom" });
    expect(button).toHaveClass("custom-class");
  });

  it("disabled状態が正しく適用される", () => {
    render(<Button disabled>Disabled Button</Button>);

    const button = screen.getByRole("button", { name: "Disabled Button" });
    expect(button).toBeDisabled();
    expect(button).toHaveClass("disabled:opacity-50");
  });

  it("asChild propでSlotコンポーネントとして動作する", () => {
    render(
      <Button asChild>
        <a href="/test">Link Button</a>
      </Button>,
    );

    const link = screen.getByRole("link", { name: "Link Button" });
    expect(link).toBeInTheDocument();
    expect(link).toHaveAttribute("href", "/test");
    expect(link).toHaveAttribute("data-slot", "button");
  });

  it("onClick eventが正しく動作する", async () => {
    const handleClick = vi.fn();
    render(<Button onClick={handleClick}>Click me</Button>);

    const button = screen.getByRole("button", { name: "Click me" });
    await userEvent.click(button);

    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it("複数のvariantがテストできる", () => {
    const variants = ["default", "destructive", "outline", "secondary", "ghost", "link"] as const;

    for (const variant of variants) {
      const { unmount } = render(<Button variant={variant}>{variant} button</Button>);

      const button = screen.getByRole(variant === "link" ? "button" : "button");
      expect(button).toBeInTheDocument();

      unmount();
    }
  });

  it("複数のsizeがテストできる", () => {
    const sizes = ["default", "sm", "lg", "icon"] as const;

    for (const size of sizes) {
      const { unmount } = render(<Button size={size}>{size} button</Button>);

      const button = screen.getByRole("button");
      expect(button).toBeInTheDocument();

      unmount();
    }
  });
});
