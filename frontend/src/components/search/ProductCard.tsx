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
    <a
      href={product.productURL}
      target="_blank"
      rel="noopener noreferrer"
      className="block w-[280px] h-full"
    >
      <Card
        className={cn(
          "bg-zinc-800/90 border-zinc-700 backdrop-blur-sm transition-all duration-300 hover:scale-105 hover:border-zinc-600 flex-shrink-0 cursor-pointer h-full",
          className,
        )}
      >
        <CardContent className="p-4 flex flex-col h-full">
          {/* 商品画像 */}
          <div className="relative mb-3 w-[247px] h-[165px] flex-shrink-0">
            <img
              src={product.imageURL.large}
              alt={product.title}
              className="w-full h-full object-cover rounded-md"
              loading="lazy"
            />
            <div className="absolute inset-0 bg-gradient-to-t from-black/20 to-transparent rounded-md" />
          </div>

          {/* 商品情報 */}
          <div className="space-y-2 flex-1 flex flex-col">
            <h4 className="text-sm font-semibold text-white leading-tight h-[3.375rem] overflow-hidden line-clamp-3">
              {product.title}
            </h4>

            {/* 価格表示 */}
            <div className="flex items-center justify-between">
              <span className="text-sm font-bold text-yellow-400 flex items-center">
                {formatPrice(product.prices)}
              </span>
            </div>

            {/* 購入ボタン - 下部に固定 */}
            <div className="mt-auto pt-2">
              <Button
                size="sm"
                className="w-full bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white border-none"
              >
                <ExternalLink className="w-3 h-3 mr-1" />
                詳細を見る
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </a>
  );
}
