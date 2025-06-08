"use client";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { logger } from "@/lib/logger";
import { cn } from "@/lib/utils";
import { ExternalLink } from "lucide-react";

interface Product {
  id: number;
  title: string;
  price: string;
  image: string;
}

interface ProductCardProps {
  product: Product;
  className?: string;
}

export function ProductCard({ product, className }: ProductCardProps) {
  return (
    <Card
      className={cn(
        "bg-zinc-800/90 border-zinc-700 backdrop-blur-sm transition-all duration-300 hover:scale-105 hover:border-zinc-600 w-48 flex-shrink-0",
        className,
      )}
    >
      <CardContent className="p-4">
        {/* 商品画像 */}
        <div className="relative mb-3">
          <img
            src={product.image}
            alt={product.title}
            className="w-full h-32 object-cover rounded-md"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-black/20 to-transparent rounded-md" />
        </div>

        {/* 商品情報 */}
        <div className="space-y-2">
          <h4 className="text-sm font-semibold text-white leading-tight h-10 overflow-hidden">
            {product.title}
          </h4>

          <div className="flex items-center justify-between">
            <span className="text-lg font-bold text-yellow-400">{product.price}</span>
          </div>

          {/* 購入ボタン */}
          <Button
            size="sm"
            className="w-full bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white border-none"
            onClick={() => {
              // アフィリエイトリンクへの遷移処理
              logger.info("商品がクリックされました", {
                productId: product.id,
                productTitle: product.title,
                price: product.price,
              });
            }}
          >
            <ExternalLink className="w-3 h-3 mr-1" />
            詳細を見る
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
