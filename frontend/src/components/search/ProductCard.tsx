"use client";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import type { DmmProduct } from "@/features/products/types";
import { cn } from "@/lib/utils";
import { ExternalLink } from "lucide-react";

interface ProductCardProps {
  product: DmmProduct;
  className?: string;
}

/**
 * 価格情報を表示用にフォーマット
 */
function formatPrice(prices: DmmProduct["prices"]): string {
  if (prices.price) {
    return `¥${prices.price}`;
  }
  if (prices.deliveries && prices.deliveries.length > 0) {
    const firstDelivery = prices.deliveries[0];
    return `¥${firstDelivery.price}`;
  }
  return "価格未設定";
}

/**
 * 商品タイトルを3行まで表示できるよう調整
 * 文字数による切り捨てではなく、CSSで3行表示制御を行う
 */

export function ProductCard({ product, className }: ProductCardProps) {
  return (
    <a href={product.productURL} target="_blank" rel="noopener noreferrer">
      <Card
        className={cn(
          "bg-zinc-800/90 border-zinc-700 backdrop-blur-sm transition-all duration-300 hover:scale-105 hover:border-zinc-600 flex-shrink-0 cursor-pointer",
          className,
        )}
      >
        <CardContent className="p-4">
          {/* 商品画像 */}
          <div className="relative mb-3" style={{ minWidth: "247px" }}>
            <img
              src={product.imageURL.large}
              alt={product.title}
              className="w-full h-auto object-cover rounded-md"
              loading="lazy"
              onError={(e) => {
                // フォールバック画像を設定
                const target = e.target as HTMLImageElement;
                target.src = product.imageURL.small || product.imageURL.list;
              }}
            />
            <div className="absolute inset-0 bg-gradient-to-t from-black/20 to-transparent rounded-md" />
          </div>

          {/* 商品情報 */}
          <div className="space-y-2">
            <h4 className="text-sm font-semibold text-white leading-tight h-16 overflow-hidden line-clamp-3">
              {product.title}
            </h4>

            {/* 価格表示 */}
            <div className="flex items-center justify-between">
              <span className="text-sm font-bold text-yellow-400 flex items-center">
                {formatPrice(product.prices)}
              </span>
            </div>

            {/* 購入ボタン */}
            <Button
              size="sm"
              className="w-full bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white border-none"
            >
              <ExternalLink className="w-3 h-3 mr-1" />
              詳細を見る
            </Button>
          </div>
        </CardContent>
      </Card>
    </a>
  );
}
