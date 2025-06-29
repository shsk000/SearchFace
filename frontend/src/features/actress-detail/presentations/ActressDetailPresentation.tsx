/**
 * 女優詳細のPresentationalコンポーネント
 * UIの表示のみを担当
 */

"use client";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
// ProductsContainerはページレベルで呼び出されるため削除
import { ExternalLink, Heart, Search } from "lucide-react";
import type { ActressDetail } from "../api";

interface ActressDetailPresentationProps {
  actress: ActressDetail;
}

/**
 * 女優詳細のPresentationalコンポーネント
 * UIの表示のみを担当し、商品表示はProductsContainerに委譲
 */
export function ActressDetailPresentation({ actress }: ActressDetailPresentationProps) {
  return (
    <div>
      {/* 女優情報カード */}
      <Card className="bg-zinc-800/90 border-zinc-700">
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
                  <p className="text-zinc-300 text-sm mb-4">
                    人気急上昇中の注目女優です。多くのファンに愛されており、 検索回数も
                    {actress.search_count}回を記録しています。
                  </p>

                  {/* FANZA商品一覧へのボタン */}
                  {actress.dmm_list_url_digital && (
                    <Button
                      asChild
                      className="bg-pink-600 hover:bg-pink-700 text-white font-semibold py-2 px-4 rounded-lg transition-colors duration-200 inline-flex items-center gap-2"
                    >
                      <a
                        href={actress.dmm_list_url_digital}
                        target="_blank"
                        rel="noopener noreferrer"
                      >
                        <ExternalLink className="w-4 h-4" />
                        FANZA商品一覧へ
                      </a>
                    </Button>
                  )}
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 関連商品セクション - ページレベルで表示されるため削除 */}
    </div>
  );
}
