import Script from "next/script";

interface StructuredDataProps {
  title?: string;
  description?: string;
  url?: string;
  image?: string;
}

export default function StructuredData({ title, description, url, image }: StructuredDataProps) {
  const siteUrl = "https://www.sokkuri-av.lol";
  const siteName = "そっくりAV";
  const logoUrl = `${siteUrl}/logo.svg`;
  const pageUrl = url || siteUrl;
  const pageTitle = title || siteName;
  const pageDescription =
    description ||
    "画像をアップするだけで、そっくりなAV女優が見つかる。最新のAI技術を使用した高精度な顔画像検索システム。";
  const pageImage = image || `${siteUrl}/og-image.jpg`;

  const structuredData = [
    {
      "@context": "https://schema.org",
      "@type": "WebSite",
      name: siteName,
      url: siteUrl,
      description: pageDescription,
      publisher: {
        "@type": "Organization",
        name: siteName,
        logo: {
          "@type": "ImageObject",
          url: logoUrl,
        },
      },
      image: pageImage,
      potentialAction: {
        "@type": "SearchAction",
        target: `${siteUrl}/?q={search_term_string}`,
        "query-input": "required name=search_term_string",
      },
    },
    {
      "@context": "https://schema.org",
      "@type": "WebPage",
      name: pageTitle,
      url: pageUrl,
      description: pageDescription,
      isPartOf: { "@id": siteUrl },
      primaryImageOfPage: pageImage,
      inLanguage: "ja",
    },
    {
      "@context": "https://schema.org",
      "@type": "WebApplication",
      name: siteName,
      description: pageDescription,
      url: siteUrl,
      applicationCategory: "MultimediaApplication",
      operatingSystem: "Web Browser",
      browserRequirements: "Requires JavaScript",
      softwareVersion: "1.0.0",
      author: {
        "@type": "Organization",
        name: siteName,
      },
      provider: {
        "@type": "Organization",
        name: siteName,
      },
      featureList: ["AI顔認識技術", "高精度類似検索", "リアルタイム検索", "ランキング機能"],
    },
  ];

  return (
    <Script id="structured-data" type="application/ld+json">
      {JSON.stringify(structuredData)}
    </Script>
  );
}
