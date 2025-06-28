import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { beforeAll, beforeEach, describe, expect, it, vi } from "vitest";
import { toast } from "sonner";
import { server } from "../../test/mocks/server";
import { ImageUploadZone } from "./ImageUploadZone";

// Next.js のモック設定
vi.mock("next/navigation", () => ({
  useRouter: () => ({
    push: vi.fn(),
    replace: vi.fn(),
  }),
}));

// Sonner toast のモック設定
vi.mock("sonner", () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}));

describe("ImageUploadZone - Clipboard Paste Functionality", () => {
  const user = userEvent.setup();
  
  // Clipboard API のモック
  const mockClipboard = {
    read: vi.fn(),
  };

  // テスト前にnavigator.clipboardとURLをモック
  beforeAll(() => {
    Object.defineProperty(navigator, 'clipboard', {
      value: mockClipboard,
      configurable: true,
    });
    
    // URL.createObjectURLをモック
    global.URL.createObjectURL = vi.fn(() => 'blob:mock-url');
    global.URL.revokeObjectURL = vi.fn();
  });

  beforeEach(() => {
    vi.clearAllMocks();
    server.resetHandlers();
    
    // デフォルトの成功レスポンス
    server.use(
      http.post("http://backend:10000/api/search", () => {
        return HttpResponse.json({
          results: [
            {
              name: "Test Person 1",
              similarity: 0.95,
              distance: 0.05,
              image_path: "/test-image-1.jpg",
            },
          ],
          processing_time: 0.123,
          search_session_id: "test-session-123",
        });
      }),
    );
  });

  it("クリップボードペースト機能がサポートされている場合、ペーストボタンが表示される", async () => {
    render(<ImageUploadZone />);

    await waitFor(() => {
      // クリップボードペーストボタンが表示されることを確認
      expect(screen.getByText("📋 クリップボードから貼り付け")).toBeInTheDocument();
    });

    // ペースト機能の説明テキストも表示されることを確認
    expect(screen.getByText("Ctrl+V")).toBeInTheDocument();
  });

  it("クリップボードから画像を正常にペーストできる", async () => {
    // クリップボードに画像があることをモック
    const mockImageBlob = new Blob(["fake image data"], { type: "image/png" });
    const mockClipboardItem = {
      types: ["image/png"],
      getType: vi.fn().mockResolvedValue(mockImageBlob),
    };
    
    mockClipboard.read.mockResolvedValue([mockClipboardItem]);

    render(<ImageUploadZone />);

    await waitFor(() => {
      expect(screen.getByText("📋 クリップボードから貼り付け")).toBeInTheDocument();
    });

    // ペーストボタンをクリック
    const pasteButton = screen.getByText("📋 クリップボードから貼り付け");
    await user.click(pasteButton);

    await waitFor(() => {
      // トーストの成功メッセージが呼ばれることを確認
      expect(toast.success).toHaveBeenCalledWith("クリップボードから画像を読み込みました！");
    });

    // クリップボードAPIが呼ばれたことを確認
    expect(mockClipboard.read).toHaveBeenCalledTimes(1);
    expect(mockClipboardItem.getType).toHaveBeenCalledWith("image/png");
  });

  it("クリップボードに画像がない場合、エラーメッセージが表示される", async () => {
    // クリップボードにテキストのみがあることをモック
    const mockClipboardItem = {
      types: ["text/plain"],
      getType: vi.fn(),
    };
    
    mockClipboard.read.mockResolvedValue([mockClipboardItem]);

    render(<ImageUploadZone />);

    await waitFor(() => {
      expect(screen.getByText("📋 クリップボードから貼り付け")).toBeInTheDocument();
    });

    // ペーストボタンをクリック
    const pasteButton = screen.getByText("📋 クリップボードから貼り付け");
    await user.click(pasteButton);

    await waitFor(() => {
      // トーストのエラーメッセージが呼ばれることを確認
      expect(toast.error).toHaveBeenCalledWith("クリップボードに画像が見つかりません", {
        closeButton: true,
      });
    });

    // クリップボードAPIが呼ばれたことを確認
    expect(mockClipboard.read).toHaveBeenCalledTimes(1);
  });

  it("クリップボードアクセスが拒否された場合、適切なエラーメッセージが表示される", async () => {
    // アクセス拒否エラーをモック
    const notAllowedError = new Error("Permission denied");
    notAllowedError.name = "NotAllowedError";
    mockClipboard.read.mockRejectedValue(notAllowedError);

    render(<ImageUploadZone />);

    await waitFor(() => {
      expect(screen.getByText("📋 クリップボードから貼り付け")).toBeInTheDocument();
    });

    // ペーストボタンをクリック
    const pasteButton = screen.getByText("📋 クリップボードから貼り付け");
    await user.click(pasteButton);

    await waitFor(() => {
      // 権限拒否のトーストエラーメッセージが呼ばれることを確認
      expect(toast.error).toHaveBeenCalledWith("クリップボードへのアクセスが拒否されました", {
        closeButton: true,
      });
    });
  });

  it("Ctrl+Vキーボードショートカットでペースト機能が動作する", async () => {
    // クリップボードに画像があることをモック
    const mockImageBlob = new Blob(["fake image data"], { type: "image/jpeg" });
    const mockClipboardItem = {
      types: ["image/jpeg"],
      getType: vi.fn().mockResolvedValue(mockImageBlob),
    };
    
    mockClipboard.read.mockResolvedValue([mockClipboardItem]);

    render(<ImageUploadZone />);

    await waitFor(() => {
      expect(screen.getByText("📋 クリップボードから貼り付け")).toBeInTheDocument();
    });

    // Ctrl+V キーを押下
    fireEvent.keyDown(document, { key: 'v', ctrlKey: true });

    await waitFor(() => {
      // トーストの成功メッセージが呼ばれることを確認
      expect(toast.success).toHaveBeenCalledWith("クリップボードから画像を読み込みました！");
    });

    expect(mockClipboard.read).toHaveBeenCalledTimes(1);
  });

  it("Cmd+Vキーボードショートカット（Mac）でペースト機能が動作する", async () => {
    // クリップボードに画像があることをモック
    const mockImageBlob = new Blob(["fake image data"], { type: "image/webp" });
    const mockClipboardItem = {
      types: ["image/webp"],
      getType: vi.fn().mockResolvedValue(mockImageBlob),
    };
    
    mockClipboard.read.mockResolvedValue([mockClipboardItem]);

    render(<ImageUploadZone />);

    await waitFor(() => {
      expect(screen.getByText("📋 クリップボードから貼り付け")).toBeInTheDocument();
    });

    // Cmd+V キーを押下（Mac）
    fireEvent.keyDown(document, { key: 'v', metaKey: true });

    await waitFor(() => {
      // トーストの成功メッセージが呼ばれることを確認
      expect(toast.success).toHaveBeenCalledWith("クリップボードから画像を読み込みました！");
    });

    expect(mockClipboard.read).toHaveBeenCalledTimes(1);
  });

  it("input要素にフォーカスがある場合、キーボードショートカットが無効になる", async () => {
    render(
      <div>
        <input type="text" data-testid="text-input" />
        <ImageUploadZone />
      </div>
    );

    await waitFor(() => {
      expect(screen.getByText("📋 クリップボードから貼り付け")).toBeInTheDocument();
    });

    // テキスト入力にフォーカス
    const textInput = screen.getByTestId("text-input");
    await user.click(textInput);

    // Ctrl+V キーを押下
    fireEvent.keyDown(document, { key: 'v', ctrlKey: true });

    // クリップボードAPIが呼ばれないことを確認
    expect(mockClipboard.read).not.toHaveBeenCalled();
  });

  it("画像が既に選択されている場合、ペーストボタンが非表示になる", async () => {
    render(<ImageUploadZone />);

    await waitFor(() => {
      expect(screen.getByText("📋 クリップボードから貼り付け")).toBeInTheDocument();
    });

    // ファイル入力要素を取得
    const fileInput = document.getElementById("fileInput") as HTMLInputElement;
    const file = new File(["test"], "test.jpg", { type: "image/jpeg" });
    
    // ファイルを直接設定
    Object.defineProperty(fileInput, 'files', {
      value: [file],
      configurable: true
    });
    
    // changeイベントを発火
    fireEvent.change(fileInput);

    await waitFor(() => {
      // ペーストボタンが非表示になることを確認
      expect(screen.queryByText("📋 クリップボードから貼り付け")).not.toBeInTheDocument();
    });
  });

  it("ファイルサイズが大きすぎる場合、クリップボードペーストでもエラーが表示される", async () => {
    // 大きなサイズの画像データをモック（500KB以上）
    const largeImageData = "a".repeat(600 * 1024); // 600KB の文字列
    const mockImageBlob = new Blob([largeImageData], { type: "image/png" });
    const mockClipboardItem = {
      types: ["image/png"],
      getType: vi.fn().mockResolvedValue(mockImageBlob),
    };
    
    mockClipboard.read.mockResolvedValue([mockClipboardItem]);

    render(<ImageUploadZone />);

    await waitFor(() => {
      expect(screen.getByText("📋 クリップボードから貼り付け")).toBeInTheDocument();
    });

    // ペーストボタンをクリック
    const pasteButton = screen.getByText("📋 クリップボードから貼り付け");
    await user.click(pasteButton);

    await waitFor(() => {
      // ファイルサイズエラーのトーストメッセージが呼ばれることを確認
      expect(toast.error).toHaveBeenCalledWith(
        expect.stringContaining("ファイルサイズが大きすぎます"),
        { closeButton: true }
      );
    }, { timeout: 3000 });
  });
});