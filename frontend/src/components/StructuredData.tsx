import Script from "next/script";

export default function StructuredData() {
  const structuredData = {
    "@context": "https://schema.org",
    "@type": "WebApplication",
    name: "そっくりAV",
    description:
      "画像をアップするだけで、そっくりなAV女優が見つかる。最新のAI技術を使用した高精度な顔画像検索システム。",
    url: "https://www.sokkuri-av.lol",
    applicationCategory: "MultimediaApplication",
    operatingSystem: "Web Browser",
    browserRequirements: "Requires JavaScript",
    softwareVersion: "1.0.0",
    author: {
      "@type": "Organization",
      name: "そっくりAV",
    },
    provider: {
      "@type": "Organization",
      name: "そっくりAV",
    },
    featureList: ["AI顔認識技術", "高精度類似検索", "リアルタイム検索", "ランキング機能"],
    // screenshot: "https://www.sokkuri-av.lol/screenshot.jpg",
  };

  return (
    <Script id="structured-data" type="application/ld+json">
      {JSON.stringify(structuredData)}
    </Script>
  );
}
