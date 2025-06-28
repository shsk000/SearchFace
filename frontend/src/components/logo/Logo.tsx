"use client";

import Image from "next/image";
import { useEffect, useRef } from "react";

/**
 * サイトロゴコンポーネント
 * - SVGロゴ画像を表示
 * - 読み込み時にフェードイン＋スケールアニメーション
 * - ホバー時にバウンドアニメーション
 */
export function Logo({ size = 56, className = "" }: { size?: number; className?: string }) {
  const ref = useRef<HTMLImageElement>(null);

  useEffect(() => {
    if (ref.current) {
      ref.current.classList.add("animate-logo-in");
    }
  }, []);

  return (
    <Image
      ref={ref}
      src="/logo.svg"
      alt="SOKKURI AV ロゴ"
      width={size}
      height={size}
      className={`transition-transform duration-200 hover:animate-logo-bounce ${className}`}
      priority
      draggable={false}
    />
  );
}
