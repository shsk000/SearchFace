import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Trophy } from "lucide-react";
import { RankingItemCard } from "./RankingItemCard";
import { getRankingData } from "./api";

// メインのランキングコンポーネント
export default async function SearchRanking() {
  const rankingData = await getRankingData();

  if (!rankingData || rankingData.ranking.length === 0) {
    return (
      <Card className="bg-zinc-900/90 border-zinc-700 backdrop-blur-sm">
        <CardHeader className="pb-4">
          <CardTitle className="text-white flex items-center justify-center gap-2 text-lg">
            <Trophy className="w-5 h-5 text-orange-500" />
            検索ランキング
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-gray-400 text-center py-4">ランキングデータがありません</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="bg-zinc-900/90 border-zinc-700 backdrop-blur-sm">
      <CardHeader className="pb-4">
        <CardTitle className="text-white flex items-center justify-center gap-2 text-lg">
          <Trophy className="w-5 h-5 text-orange-500" />
          検索ランキング TOP{rankingData.ranking.length}
        </CardTitle>
        <p className="text-sm text-gray-400 text-center">最も検索された人物のランキングです</p>
      </CardHeader>
      <CardContent>
        {/* ランキングをグリッド表示に変更 */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {rankingData.ranking.map((item) => (
            <RankingItemCard key={item.person_id} item={item} />
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
