import { Content } from "@/components/content/Content";
import ActressDetailContainer from "@/features/actress-detail/containers/ActressDetailContainer";
import ProductsContainer from "@/features/products/containers/ProductsContainer";
import { logger } from "@/lib/logger";
import { notFound } from "next/navigation";
import { Suspense } from "react";

interface ActressDetailPageProps {
  params: Promise<{
    person_id: string;
  }>;
}

async function ActressDetailContent({ personId }: { personId: number }) {
  logger.info("女優詳細ページ開始", { personId });

  return (
    <>
      {/* 女優詳細情報 */}
      <ActressDetailContainer personId={personId} />

      {/* 関連商品セクション */}
      <div className="mt-8">
        <ProductsContainer personId={personId} limit={20} />
      </div>
    </>
  );
}

function ActressDetailLoading() {
  return (
    <>
      <div className="bg-zinc-800/90 border border-zinc-700 rounded-lg p-8 mb-8">
        <div className="grid md:grid-cols-2 gap-8 items-center">
          {/* 画像スケルトン */}
          <div className="w-full max-w-md mx-auto h-96 bg-zinc-700 rounded-xl animate-pulse" />

          {/* テキストスケルトン */}
          <div className="space-y-6">
            <div>
              <div className="h-10 bg-zinc-700 rounded-md animate-pulse mb-2" />
              <div className="h-6 bg-zinc-700 rounded-md animate-pulse w-24" />
            </div>
            <div className="space-y-4">
              <div className="h-6 bg-zinc-700 rounded-md animate-pulse" />
              <div className="h-20 bg-zinc-700 rounded-md animate-pulse" />
            </div>
          </div>
        </div>
      </div>

      {/* 商品スケルトン */}
      <div className="grid md:grid-cols-3 gap-6">
        {[1, 2, 3].map((i) => (
          <div key={i} className="bg-zinc-800/90 border border-zinc-700 rounded-lg p-4">
            <div className="aspect-square bg-zinc-700 rounded-lg mb-4 animate-pulse" />
            <div className="h-4 bg-zinc-700 rounded-md animate-pulse mb-2" />
            <div className="h-4 bg-zinc-700 rounded-md animate-pulse w-16" />
          </div>
        ))}
      </div>
    </>
  );
}

export default async function ActressDetailPage({ params }: ActressDetailPageProps) {
  const { person_id } = await params;
  const personId = Number.parseInt(person_id);

  // person_idが数値でない場合は404
  if (Number.isNaN(personId) || personId <= 0) {
    notFound();
  }

  return (
    <Content className="">
      <Suspense fallback={<ActressDetailLoading />}>
        <ActressDetailContent personId={personId} />
      </Suspense>
    </Content>
  );
}

export async function generateMetadata({ params }: ActressDetailPageProps) {
  const { person_id } = await params;
  return {
    title: "女優詳細",
    description: `女優ID: ${person_id}の詳細情報ページ`,
  };
}
