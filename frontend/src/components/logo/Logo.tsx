import Image from "next/image";

/**
 * サイトロゴコンポーネント
 * - SVGロゴ画像を表示
 * - ホバー時にわずかに拡大するアニメーション
 */
export function Logo({ size = 56, className = "" }: { size?: number; className?: string }) {
  return (
    <Image
      src="/logo.svg"
      alt="SearchFace ロゴ"
      width={size}
      height={size}
      className={`transition-transform duration-200 hover:scale-110 ${className}`}
      priority
      draggable={false}
    />
  );
}
