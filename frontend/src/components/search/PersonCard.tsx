"use client";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { Crown } from "lucide-react";
import Link from "next/link";

interface Person {
  id: number;
  name: string;
  similarity: number;
  image_path: string;
  rank: number;
}

interface PersonCardProps {
  person: Person;
  isWinner: boolean;
  className?: string;
  isCompact?: boolean;
}

export function PersonCard({ person, isWinner, className, isCompact = false }: PersonCardProps) {
  return (
    <div className={cn("relative", className)}>
      <Link href={`/actress/${person.id}`}>
        <Card
          className={cn(
            "backdrop-blur-sm transition-all duration-300 hover:scale-105 cursor-pointer",
            isCompact
              ? isWinner
                ? "h-32 w-full bg-gradient-to-r from-yellow-400/30 to-amber-600/30 border-yellow-500/70"
                : "h-32 w-full bg-zinc-800/90 border-zinc-700 hover:border-zinc-600"
              : isWinner
                ? "h-80 bg-gradient-to-br from-yellow-400/20 to-amber-600/20 border-yellow-500/70 shadow-lg shadow-yellow-500/30"
                : "h-64 bg-zinc-800/90 border-zinc-700 hover:border-zinc-600",
          )}
        >
          <CardContent
            className={cn(
              "p-3 h-full",
              isCompact ? "flex flex-row items-center gap-4" : "flex flex-col",
            )}
          >
            {isCompact ? (
              // コンパクトモード: 横並びレイアウト
              <>
                {/* 画像 */}
                <div className="relative flex-shrink-0">
                  <img
                    src={person.image_path}
                    alt={person.name}
                    className="w-[125px] h-[125px] object-cover rounded-lg"
                  />
                  {isWinner && (
                    <div className="absolute inset-0 bg-gradient-to-t from-yellow-500/20 to-transparent rounded-lg" />
                  )}
                  <Badge
                    variant={isWinner ? "default" : "secondary"}
                    className={cn(
                      "absolute top-2 left-2 text-xs font-bold",
                      isWinner
                        ? "bg-yellow-500 text-black hover:bg-yellow-600"
                        : "bg-zinc-700 text-white hover:bg-zinc-600",
                    )}
                  >
                    No.{person.rank}
                  </Badge>
                </div>

                {/* テキスト情報 */}
                <div className="flex-1 flex flex-col justify-center">
                  <h3
                    className={cn(
                      "font-bold mb-2 leading-tight",
                      isWinner ? "text-lg text-yellow-300" : "text-base text-white",
                    )}
                    style={{
                      display: "-webkit-box",
                      WebkitLineClamp: 2,
                      WebkitBoxOrient: "vertical",
                      overflow: "hidden",
                      wordBreak: "keep-all",
                    }}
                    title={person.name}
                  >
                    {person.name}
                  </h3>

                  <div className="flex items-center gap-2 mb-2">
                    <span className={cn("text-sm", isWinner ? "text-yellow-200" : "text-gray-400")}>
                      類似度:
                    </span>
                    <span
                      className={cn(
                        "font-bold text-lg",
                        isWinner ? "text-yellow-300" : "text-white",
                      )}
                    >
                      {person.similarity}%
                    </span>
                    {isWinner && <Crown className="w-5 h-5 text-yellow-500 animate-pulse" />}
                  </div>
                </div>
              </>
            ) : (
              // 通常モード: 縦並びレイアウト
              <>
                {/* ランクバッジ */}
                <div className="flex justify-between items-start mb-2">
                  <Badge
                    variant={isWinner ? "default" : "secondary"}
                    className={cn(
                      "text-xs font-bold",
                      isWinner
                        ? "bg-yellow-500 text-black hover:bg-yellow-600"
                        : "bg-zinc-700 text-white hover:bg-zinc-600",
                    )}
                  >
                    No.{person.rank}
                  </Badge>

                  {isWinner && <Crown className="w-4 h-4 text-yellow-500 animate-pulse" />}
                </div>

                {/* 画像 */}
                <div className="relative mb-2">
                  <img
                    src={person.image_path}
                    alt={person.name}
                    className={cn("w-full aspect-square object-cover rounded-lg")}
                  />
                  {isWinner && (
                    <div className="absolute inset-0 bg-gradient-to-t from-yellow-500/20 to-transparent rounded-lg" />
                  )}
                </div>

                {/* 人物情報 */}
                <div className="text-center mt-auto px-1">
                  <h3
                    className={cn(
                      "font-bold mb-1 leading-tight",
                      isWinner ? "text-sm text-yellow-300 h-10" : "text-xs text-white h-8",
                    )}
                    style={{
                      display: "-webkit-box",
                      WebkitLineClamp: isWinner ? 2 : 2,
                      WebkitBoxOrient: "vertical",
                      overflow: "hidden",
                      wordBreak: "keep-all",
                    }}
                    title={person.name}
                  >
                    {person.name}
                  </h3>

                  <div className="flex items-center justify-center gap-1">
                    <span className={cn("text-xs", isWinner ? "text-yellow-200" : "text-gray-400")}>
                      類似度:
                    </span>
                    <span
                      className={cn(
                        "font-bold text-xs",
                        isWinner ? "text-yellow-300" : "text-white",
                      )}
                    >
                      {person.similarity}%
                    </span>
                  </div>
                </div>
              </>
            )}

            {/* 1位の特別装飾 */}
            {isWinner && (
              <div className="absolute -top-2 left-1/2 transform -translate-x-1/2">
                <div className="bg-gradient-to-r from-yellow-400 to-yellow-600 text-black px-6 py-1 rounded-full text-sm font-bold shadow-lg whitespace-nowrap">
                  🏆 BEST MATCH
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </Link>
    </div>
  );
}
