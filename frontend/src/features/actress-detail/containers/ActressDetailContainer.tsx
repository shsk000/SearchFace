/**
 * 女優詳細のContainerコンポーネント
 * React Server Component - データ取得とビジネスロジックを担当
 */

import { createLogger } from "@/lib/logger";
import { notFound } from "next/navigation";
import { getActressDetail } from "../api";
import { ActressDetailPresentation } from "../presentations/ActressDetailPresentation";

const logger = createLogger("ActressDetailContainer");

interface ActressDetailContainerProps {
  personId: number;
}

/**
 * 女優詳細のContainerコンポーネント
 * データ取得を行い、Presentationalコンポーネントに渡す
 */
export default async function ActressDetailContainer({ personId }: ActressDetailContainerProps) {
  logger.info("女優詳細コンテナ開始", { personId });

  try {
    // 女優詳細情報を取得
    const actress = await getActressDetail(personId);

    logger.info("女優詳細データ取得完了", {
      personId,
      actressName: actress.name,
    });

    // Presentationalコンポーネントにデータを渡す
    return <ActressDetailPresentation actress={actress} />;
  } catch (error) {
    logger.error("女優詳細コンテナでエラーが発生", { personId, error });
    notFound();
  }
}
