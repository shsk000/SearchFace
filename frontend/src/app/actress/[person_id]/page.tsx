import { getActressDetail, getDummyAffiliateProducts } from "@/features/actress-detail";
import { ActressDetailCard } from "@/features/actress-detail";
import { logger } from "@/lib/logger";
import { notFound } from "next/navigation";
import { Suspense } from "react";

interface ActressDetailPageProps {
  params: Promise<{
    person_id: string;
  }>;
}

async function ActressDetailContent({ personId }: { personId: number }) {
  try {
    logger.info("女優詳細ページデータを取得中", { personId });

    // 女優詳細情報を取得
    const actress = await getActressDetail(personId);

    // ダミーのアフィリエイト商品を生成
    const products = getDummyAffiliateProducts(actress.name);

    logger.info("女優詳細ページデータを取得しました", {
      actressName: actress.name,
      productCount: products.length,
    });

    return <ActressDetailCard actress={actress} products={products} />;
  } catch (error) {
    logger.error("女優詳細ページでエラーが発生しました", { error, personId });
    notFound();
  }
}

function ActressDetailLoading() {
  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
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
    </div>
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
    <div className="min-h-screen bg-gradient-to-br from-zinc-900 via-black to-zinc-900">
      <Suspense fallback={<ActressDetailLoading />}>
        <ActressDetailContent personId={personId} />
      </Suspense>
    </div>
  );
}

export async function generateMetadata({ params }: ActressDetailPageProps) {
  const { person_id } = await params;
  return {
    title: "女優詳細 | SearchFace",
    description: `女優ID: ${person_id}の詳細情報ページ`,
  };
}
