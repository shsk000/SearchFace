import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { AgeVerificationModal } from "./age-verification-modal";

// Logger is not mocked - let it output naturally

describe("AgeVerificationModal", () => {
  const mockOnVerified = vi.fn();
  const mockOnDeclined = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("モーダルが閉じている時は何も表示されない", () => {
    render(
      <AgeVerificationModal
        isOpen={false}
        onVerified={mockOnVerified}
        onDeclined={mockOnDeclined}
      />,
    );

    expect(screen.queryByText("年齢確認")).not.toBeInTheDocument();
  });

  it("モーダルが開いている時に適切な内容が表示される", () => {
    render(
      <AgeVerificationModal
        isOpen={true}
        onVerified={mockOnVerified}
        onDeclined={mockOnDeclined}
      />,
    );

    expect(screen.getByText("年齢確認")).toBeInTheDocument();
    expect(screen.getByText("このサイトは成人向けコンテンツが含まれています")).toBeInTheDocument();
    expect(screen.getByText("あなたは18歳以上ですか？")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "はい" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "いいえ" })).toBeInTheDocument();
  });

  it("「はい」ボタンをクリックするとonVerifiedが呼ばれる", async () => {
    render(
      <AgeVerificationModal
        isOpen={true}
        onVerified={mockOnVerified}
        onDeclined={mockOnDeclined}
      />,
    );

    const yesButton = screen.getByRole("button", { name: "はい" });
    fireEvent.click(yesButton);

    await waitFor(() => {
      expect(mockOnVerified).toHaveBeenCalledTimes(1);
    });
  });

  it("「いいえ」ボタンをクリックするとonDeclinedが呼ばれる", async () => {
    render(
      <AgeVerificationModal
        isOpen={true}
        onVerified={mockOnVerified}
        onDeclined={mockOnDeclined}
      />,
    );

    const noButton = screen.getByRole("button", { name: "いいえ" });
    fireEvent.click(noButton);

    await waitFor(() => {
      expect(mockOnDeclined).toHaveBeenCalledTimes(1);
    });
  });

  it("「はい」ボタンクリック後にモーダルが閉じる", async () => {
    render(
      <AgeVerificationModal
        isOpen={true}
        onVerified={mockOnVerified}
        onDeclined={mockOnDeclined}
      />,
    );

    const yesButton = screen.getByRole("button", { name: "はい" });
    fireEvent.click(yesButton);

    await waitFor(() => {
      expect(screen.queryByText("年齢確認")).not.toBeInTheDocument();
    });
  });

  it("「いいえ」ボタンクリック後にモーダルが閉じる", async () => {
    render(
      <AgeVerificationModal
        isOpen={true}
        onVerified={mockOnVerified}
        onDeclined={mockOnDeclined}
      />,
    );

    const noButton = screen.getByRole("button", { name: "いいえ" });
    fireEvent.click(noButton);

    await waitFor(() => {
      expect(screen.queryByText("年齢確認")).not.toBeInTheDocument();
    });
  });
});
