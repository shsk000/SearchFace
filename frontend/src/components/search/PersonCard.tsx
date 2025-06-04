"use client";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { Crown } from "lucide-react";

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
}

export function PersonCard({ person, isWinner, className }: PersonCardProps) {
  return (
    <div className={cn("relative", className)}>
      <Card
        className={cn(
          "bg-zinc-800/90 border-zinc-700 backdrop-blur-sm transition-all duration-300 hover:scale-105",
          isWinner
            ? "border-yellow-500/50 shadow-lg shadow-yellow-500/20"
            : "hover:border-zinc-600",
        )}
      >
        <CardContent className="p-6">
          {/* ランクバッジ */}
          <div className="flex justify-between items-start mb-4">
            <Badge
              variant={isWinner ? "default" : "secondary"}
              className={cn(
                "text-sm font-bold",
                isWinner
                  ? "bg-yellow-500 text-black hover:bg-yellow-600"
                  : "bg-zinc-700 text-white hover:bg-zinc-600",
              )}
            >
              No.{person.rank}
            </Badge>

            {isWinner && <Crown className="w-6 h-6 text-yellow-500 animate-pulse" />}
          </div>

          {/* 画像 */}
          <div className="relative mb-4">
            <img
              src={person.image_path}
              alt={person.name}
              className="w-full h-64 object-cover rounded-lg"
            />
            {isWinner && (
              <div className="absolute inset-0 bg-gradient-to-t from-yellow-500/20 to-transparent rounded-lg" />
            )}
          </div>

          {/* 人物情報 */}
          <div className="text-center">
            <h3
              className={cn(
                "font-bold mb-2",
                isWinner ? "text-xl text-yellow-400" : "text-lg text-white",
              )}
            >
              {person.name}
            </h3>

            <div className="flex items-center justify-center gap-2">
              <span className="text-sm text-gray-400">類似度:</span>
              <span
                className={cn("font-bold text-lg", isWinner ? "text-yellow-400" : "text-white")}
              >
                {person.similarity}%
              </span>
            </div>
          </div>

          {/* 1位の特別装飾 */}
          {isWinner && (
            <div className="absolute -top-2 left-1/2 transform -translate-x-1/2">
              <div className="bg-gradient-to-r from-yellow-400 to-yellow-600 text-black px-4 py-1 rounded-full text-sm font-bold shadow-lg">
                🏆 BEST MATCH
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
