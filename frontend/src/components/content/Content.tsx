import { cn } from "@/lib/utils";
import type { ElementType, PropsWithChildren } from "react";

type ContentProps<T extends ElementType = "div"> = PropsWithChildren<{
  as?: T;
  className?: string;
}> &
  Omit<
    React.ComponentPropsWithoutRef<T>,
    keyof PropsWithChildren<{
      as?: T;
      className?: string;
    }>
  >;

/**
 * 汎用的なコンテンツコンテナコンポーネント
 * 任意のHTML要素としてレンダリング可能
 *
 * @example
 * // デフォルト（div要素）
 * <Content>コンテンツ</Content>
 *
 * @example
 * // section要素として
 * <Content as="section">コンテンツ</Content>
 *
 * @example
 * // main要素として、追加のprops付き
 * <Content as="main" id="main-content" aria-label="メインコンテンツ">
 *   コンテンツ
 * </Content>
 *
 * @example
 * // article要素として、カスタムクラス付き
 * <Content as="article" className="custom-article">
 *   コンテンツ
 * </Content>
 */
export const Content = <T extends ElementType = "div">({
  as,
  children,
  className,
  ...props
}: ContentProps<T>) => {
  const Component = as || "div";

  return (
    <Component
      className={cn("min-h-screen  text-white mt-4 overflow-hidden", className)}
      {...props}
    >
      <div className="relative z-10 max-w-7xl mx-auto backdrop-blur-sm bg-black/20 rounded-lg p-6">
        {children}
      </div>
    </Component>
  );
};
