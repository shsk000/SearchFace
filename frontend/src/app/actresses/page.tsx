import { Suspense } from "react";
import Link from "next/link";
import { Users, Home } from "lucide-react";
import ActressListContainer from "@/features/actress-list/containers/ActressListContainer";
import { Content } from "@/components/content/Content";

interface PageProps {
  searchParams?: Promise<{
    page?: string;
    search?: string;
    sort_by?: string;
  }>;
}

/**
 * 女優一覧ページ
 */
export default async function ActressListPage({ searchParams }: PageProps) {
  const resolvedSearchParams = await searchParams;
  return (
    <Content>
      <div className="container mx-auto px-4 py-8">
        {/* ナビゲーションメニュー */}
        <nav className="w-full mb-8">
          <div className="flex justify-center gap-4">
            <Link
              href="/"
              className="flex items-center gap-2 px-4 py-2 bg-zinc-800/50 border border-zinc-700 rounded-lg hover:border-zinc-600 transition-all duration-300 hover:scale-105"
            >
              <Home className="w-4 h-4" />
              <span className="text-sm">ホーム</span>
            </Link>
            <Link
              href="/actresses"
              className="flex items-center gap-2 px-4 py-2 bg-blue-600/50 border border-blue-500 rounded-lg"
            >
              <Users className="w-4 h-4" />
              <span className="text-sm">女優一覧</span>
            </Link>
          </div>
        </nav>

        <Suspense
          fallback={
            <div className="text-center py-12">
              <div className="text-gray-400">読み込み中...</div>
            </div>
          }
        >
          <ActressListContainer searchParams={resolvedSearchParams} />
        </Suspense>
      </div>
    </Content>
  );
}

export const metadata = {
  title: "女優一覧",
  description: "登録されている女優の一覧ページです。名前で検索や並び替えが可能です。",
};
