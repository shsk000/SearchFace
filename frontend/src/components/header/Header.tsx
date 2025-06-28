import { Logo } from "@/components/logo/Logo";
import { Search, Users } from "lucide-react";
import Link from "next/link";

/**
 * サイト共通ヘッダー
 * - ロゴ（トップページへのリンク）
 * - ナビゲーション（女優一覧・顔検索）
 */
export function Header() {
  return (
    <header className="w-full flex items-center justify-between px-4 py-2 bg-zinc-950/80 border-b border-zinc-800 shadow-sm fixed top-0 left-0 z-30 backdrop-blur-md">
      <Link href="/" className="flex items-center gap-1 group">
        <Logo size={36} />
        <span className="text-lg font-bold tracking-tight text-white group-hover:text-[#ee2737] transition-colors">
          SOKKURI AV
        </span>
      </Link>
      <nav className="flex gap-2">
        <Link
          href="/actresses"
          className="flex items-center gap-1 px-3 py-1.5 rounded-md text-sm font-medium text-zinc-200 hover:bg-zinc-800/80 transition-colors"
        >
          <Users className="w-4 h-4" />
          女優一覧
        </Link>
        <Link
          href="/"
          className="flex items-center gap-1 px-3 py-1.5 rounded-md text-sm font-medium text-white bg-[#ee2737] hover:bg-[#d81e2b] transition-colors"
        >
          <Search className="w-4 h-4" />
          顔検索
        </Link>
      </nav>
    </header>
  );
}
