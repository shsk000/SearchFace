import { Badge } from "@/components/ui/badge";
import { Crown, Trophy } from "lucide-react";
import Link from "next/link";
import type { RankingItemCardProps } from "./types";

// ランキングアイテムコンポーネント
export function RankingItemCard({ item }: RankingItemCardProps) {
  const isFirst = item.rank === 1;
  const isTop3 = item.rank <= 3;

  return (
    <Link href={`/actress/${item.person_id}`} className="block">
      <div className="relative p-4 rounded-lg bg-zinc-800/50 border border-zinc-700 hover:border-zinc-600 transition-all duration-300 hover:scale-105 cursor-pointer">
        {/* ランクバッジ - 右上に配置 */}
        <div className="absolute -top-2 -right-2 z-10">
          {isFirst ? (
            <div className="relative">
              <Crown className="w-6 h-6 text-yellow-500" />
              <span className="absolute -bottom-1 -right-1 bg-yellow-500 text-black text-xs font-bold rounded-full w-4 h-4 flex items-center justify-center">
                1
              </span>
            </div>
          ) : (
            <Badge
              variant={isTop3 ? "default" : "secondary"}
              className={`text-sm font-bold w-6 h-6 flex items-center justify-center ${
                isTop3
                  ? "bg-gradient-to-r from-orange-500 to-red-500 text-white"
                  : "bg-zinc-700 text-white"
              }`}
            >
              {item.rank}
            </Badge>
          )}
        </div>

        {/* 人物画像 - 中央に配置 */}
        <div className="flex justify-center mb-3">
          {item.image_path ? (
            <img
              src={item.image_path}
              alt={item.name}
              className="w-20 h-20 rounded-lg object-cover border border-zinc-600"
            />
          ) : (
            <div className="w-20 h-20 rounded-lg bg-zinc-700 flex items-center justify-center">
              <span className="text-zinc-400 text-xs">NO IMAGE</span>
            </div>
          )}
        </div>

        {/* 人物情報 - 中央揃え */}
        <div className="text-center">
          <h3 className={`font-bold text-sm mb-1 ${isFirst ? "text-yellow-400" : "text-white"}`}>
            {item.name}
          </h3>
          <div className="flex items-center justify-center gap-1">
            <Trophy className="w-3 h-3 text-orange-500" />
            <span className="text-xs text-gray-400">検索回数:{item.win_count}回</span>
          </div>
        </div>

        {/* 1位の特別装飾 */}
        {isFirst && (
          <div className="absolute inset-0 bg-gradient-to-t from-yellow-500/10 to-transparent rounded-lg pointer-events-none" />
        )}
      </div>
    </Link>
  );
}
