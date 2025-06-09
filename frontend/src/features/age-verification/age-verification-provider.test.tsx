import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { type MockedFunction, beforeEach, describe, expect, it, vi } from "vitest";
import { AgeVerificationProvider } from "./age-verification-provider";

// Logger is not mocked - let it output naturally

vi.mock("@/actions/age-verification/age-verification", () => ({
  confirmAgeVerification: vi.fn(),
  declineAgeVerification: vi.fn(),
}));

vi.mock("@/features/age-verification/age-verification-modal", () => ({
  AgeVerificationModal: ({
    isOpen,
    onVerified,
    onDeclined,
  }: {
    isOpen: boolean;
    onVerified: () => void;
    onDeclined: () => void;
  }) => {
    if (!isOpen) return null;
    return (
      <div data-testid="age-verification-modal">
        <button type="button" onClick={onVerified} data-testid="verify-button">
          はい
        </button>
        <button type="button" onClick={onDeclined} data-testid="decline-button">
          いいえ
        </button>
      </div>
    );
  },
}));

import {
  confirmAgeVerification,
  declineAgeVerification,
} from "@/actions/age-verification/age-verification";

describe("AgeVerificationProvider", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("年齢認証済みの場合はモーダルを表示しない", () => {
    render(
      <AgeVerificationProvider isAgeVerified={true}>
        <div data-testid="children">子コンポーネント</div>
      </AgeVerificationProvider>,
    );

    expect(screen.getByTestId("children")).toBeInTheDocument();
    expect(screen.queryByTestId("age-verification-modal")).not.toBeInTheDocument();
  });

  it("年齢認証未済の場合はモーダルを表示する", () => {
    render(
      <AgeVerificationProvider isAgeVerified={false}>
        <div data-testid="children">子コンポーネント</div>
      </AgeVerificationProvider>,
    );

    expect(screen.getByTestId("children")).toBeInTheDocument();
    expect(screen.getByTestId("age-verification-modal")).toBeInTheDocument();
  });

  it("年齢認証確認ボタンをクリックするとconfirmAgeVerificationが呼ばれる", async () => {
    (confirmAgeVerification as MockedFunction<typeof confirmAgeVerification>).mockResolvedValue(
      undefined,
    );

    render(
      <AgeVerificationProvider isAgeVerified={false}>
        <div data-testid="children">子コンポーネント</div>
      </AgeVerificationProvider>,
    );

    const verifyButton = screen.getByTestId("verify-button");
    fireEvent.click(verifyButton);

    await waitFor(() => {
      expect(confirmAgeVerification).toHaveBeenCalledTimes(1);
    });
  });

  it("年齢認証拒否ボタンをクリックするとdeclineAgeVerificationが呼ばれる", async () => {
    (declineAgeVerification as MockedFunction<typeof declineAgeVerification>).mockResolvedValue(
      undefined,
    );

    render(
      <AgeVerificationProvider isAgeVerified={false}>
        <div data-testid="children">子コンポーネント</div>
      </AgeVerificationProvider>,
    );

    const declineButton = screen.getByTestId("decline-button");
    fireEvent.click(declineButton);

    await waitFor(() => {
      expect(declineAgeVerification).toHaveBeenCalledTimes(1);
    });
  });

  it("年齢認証確認が成功するとモーダルが閉じる", async () => {
    (confirmAgeVerification as MockedFunction<typeof confirmAgeVerification>).mockResolvedValue(
      undefined,
    );

    render(
      <AgeVerificationProvider isAgeVerified={false}>
        <div data-testid="children">子コンポーネント</div>
      </AgeVerificationProvider>,
    );

    expect(screen.getByTestId("age-verification-modal")).toBeInTheDocument();

    const verifyButton = screen.getByTestId("verify-button");
    fireEvent.click(verifyButton);

    await waitFor(() => {
      expect(screen.queryByTestId("age-verification-modal")).not.toBeInTheDocument();
    });
  });

  it("年齢認証確認でエラーが発生してもモーダルは開いたまま", async () => {
    const error = new Error("認証エラー");
    (confirmAgeVerification as MockedFunction<typeof confirmAgeVerification>).mockRejectedValue(
      error,
    );

    render(
      <AgeVerificationProvider isAgeVerified={false}>
        <div data-testid="children">子コンポーネント</div>
      </AgeVerificationProvider>,
    );

    const verifyButton = screen.getByTestId("verify-button");
    fireEvent.click(verifyButton);

    // エラー発生後もモーダルは表示されている
    await waitFor(() => {
      expect(confirmAgeVerification).toHaveBeenCalledTimes(1);
    });

    expect(screen.getByTestId("age-verification-modal")).toBeInTheDocument();
  });
});
