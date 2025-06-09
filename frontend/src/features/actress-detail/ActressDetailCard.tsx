"use client";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Heart, Search, ShoppingBag } from "lucide-react";
import type { ActressDetail, AffiliateProduct } from "./api";

interface ActressDetailCardProps {
  actress: ActressDetail;
  products: AffiliateProduct[];
}

export function ActressDetailCard({ actress, products }: ActressDetailCardProps) {
  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      {/* 女優情報カード */}
      <Card className="bg-zinc-800/90 border-zinc-700 mb-8">
        <CardContent className="p-8">
          <div className="grid md:grid-cols-2 gap-8 items-center">
            {/* 画像 */}
            <div className="relative">
              {actress.image_path ? (
                <img
                  src={actress.image_path}
                  alt={actress.name}
                  className="w-full max-w-md mx-auto rounded-xl object-cover border border-zinc-600"
                />
              ) : (
                <div className="w-full max-w-md mx-auto h-96 rounded-xl bg-zinc-700 flex items-center justify-center border border-zinc-600">
                  <span className="text-zinc-400 text-lg">NO IMAGE</span>
                </div>
              )}
              {/* グラデーション装飾 */}
              <div className="absolute inset-0 bg-gradient-to-t from-black/20 to-transparent rounded-xl" />
            </div>

            {/* 詳細情報 */}
            <div className="space-y-6">
              <div>
                <h1 className="text-4xl font-bold text-white mb-2">{actress.name}</h1>
                <Badge className="bg-pink-500 text-white hover:bg-pink-600">
                  <Heart className="w-4 h-4 mr-2" />
                  人気女優
                </Badge>
              </div>

              <div className="space-y-4">
                <div className="flex items-center gap-3">
                  <Search className="w-5 h-5 text-blue-400" />
                  <span className="text-zinc-300">検索回数:</span>
                  <span className="text-xl font-bold text-white">{actress.search_count}回</span>
                </div>

                <div className="bg-zinc-700/50 rounded-lg p-4">
                  <h3 className="text-lg font-semibold text-white mb-2">プロフィール</h3>
                  <p className="text-zinc-300 text-sm">
                    人気急上昇中の注目女優です。多くのファンに愛されており、 検索回数も
                    {actress.search_count}回を記録しています。
                  </p>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* アフィリエイト商品セクション */}
      <div>
        <div className="flex items-center gap-3 mb-6">
          <ShoppingBag className="w-6 h-6 text-orange-400" />
          <h2 className="text-2xl font-bold text-white">関連商品</h2>
        </div>

        <div className="grid md:grid-cols-3 gap-6">
          {products.map((product) => (
            <Card
              key={product.id}
              className="bg-zinc-800/90 border-zinc-700 hover:border-zinc-600 transition-all duration-300 hover:scale-105"
            >
              <CardContent className="p-4">
                <div className="aspect-square bg-zinc-700 rounded-lg mb-4 flex items-center justify-center">
                  <ShoppingBag className="w-12 h-12 text-zinc-400" />
                </div>

                <h3 className="font-semibold text-white mb-2 text-sm line-clamp-2">
                  {product.title}
                </h3>

                <div className="flex justify-end">
                  <a
                    href={product.link}
                    className="bg-orange-500 hover:bg-orange-600 text-white px-3 py-1 rounded-md text-sm font-medium transition-colors"
                    onClick={(e) => e.preventDefault()} // ダミーリンクなのでクリックを無効化
                  >
                    詳細
                  </a>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
}
