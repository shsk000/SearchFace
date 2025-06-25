import Link from "next/link";
import type { ActressCardProps } from "../types";

/**
 * 女優カードコンポーネント
 * RankingItemCardのスタイルを踏襲し、ランキング要素を除いたシンプルなデザイン
 */
export function ActressCard({ actress }: ActressCardProps) {
  return (
    <Link href={`/actress/${actress.person_id}`} className="block">
      <div className="relative p-4 rounded-lg bg-zinc-800/50 border border-zinc-700 hover:border-zinc-600 transition-all duration-300 hover:scale-105 cursor-pointer">
        {/* 女優画像 - 中央に配置 */}
        <div className="flex justify-center mb-3">
          {actress.image_path ? (
            <img
              src={actress.image_path}
              alt={actress.name}
              className="w-20 h-20 rounded-lg object-cover border border-zinc-600"
            />
          ) : (
            <div className="w-20 h-20 rounded-lg bg-zinc-700 flex items-center justify-center">
              <span className="text-zinc-400 text-xs">NO IMAGE</span>
            </div>
          )}
        </div>

        {/* 女優情報 - 中央揃え */}
        <div className="text-center">
          <h3 className="font-bold text-sm mb-1 text-white">
            {actress.name}
          </h3>
          {actress.dmm_actress_id && (
            <div className="text-xs text-gray-400">
              ID: {actress.dmm_actress_id}
            </div>
          )}
        </div>
      </div>
    </Link>
  );
}