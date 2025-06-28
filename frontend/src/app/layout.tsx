import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import StructuredData from "@/components/StructuredData";
import { Header } from "@/components/header/Header";
import { Toaster } from "@/components/ui/sonner";
import { AgeVerificationProvider } from "@/features/age-verification/age-verification-provider";
import GoogleAnalytics from "@/features/analytics/google-analytics";
import { BackgroundImages } from "@/features/background/BackgroundImages";
import { isAgeVerified } from "@/lib/age-verification";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: {
    template: "%s | そっくりAV",
    default: "そっくりAV - AI顔画像検索システム",
  },
  description:
    "画像をアップするだけで、そっくりなAV女優が見つかる。最新のAI技術を使用した高精度な顔画像検索システム。",
  openGraph: {
    title: "そっくりAV - AI顔画像検索システム",
    description:
      "画像をアップするだけで、そっくりなAV女優が見つかる。最新のAI技術を使用した高精度な顔画像検索システム。",
    url: "https://www.sokkuri-av.lol",
    siteName: "そっくりAV",
    images: [
      {
        url: "https://www.sokkuri-av.lol/og-image.jpg",
        width: 1200,
        height: 630,
        alt: "そっくりAV - AI顔画像検索システム",
      },
    ],
    type: "website",
    locale: "ja_JP",
  },
  twitter: {
    card: "summary_large_image",
    title: "そっくりAV - AI顔画像検索システム",
    description:
      "画像をアップするだけで、そっくりなAV女優が見つかる。最新のAI技術を使用した高精度な顔画像検索システム。",
    images: ["https://www.sokkuri-av.lol/og-image.jpg"],
  },
  alternates: {
    canonical: "https://www.sokkuri-av.lol",
  },
  authors: [{ name: "そっくりAV" }],
  creator: "そっくりAV",
  publisher: "そっくりAV",
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      "max-video-preview": -1,
      "max-image-preview": "large",
      "max-snippet": -1,
    },
  },
  viewport: {
    width: "device-width",
    initialScale: 1,
    maximumScale: 1,
  },
  // verification: {
  //   google: "your-google-verification-code",
  // bing: "your-bing-verification-code",
  // },
  category: "technology",
};

export default async function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const ageVerified = await isAgeVerified();

  return (
    <html lang="ja">
      <body className={`${geistSans.variable} ${geistMono.variable} antialiased`}>
        <Header />
        <GoogleAnalytics />
        <StructuredData
          title="そっくりAV - AI顔画像検索システム"
          description="画像をアップするだけで、そっくりなAV女優が見つかる。最新のAI技術を使用した高精度な顔画像検索システム。"
          url="https://www.sokkuri-av.lol"
          image="https://www.sokkuri-av.lol/og-image.jpg"
        />
        <AgeVerificationProvider isAgeVerified={ageVerified}>
          <main className="relative min-h-screen text-white flex items-center justify-center p-4 overflow-hidden pt-14 bg-gradient-to-br from-[#111] via-[#1a1a1a] to-[#ee2737]/40">
            {children}
          </main>
        </AgeVerificationProvider>
        <Toaster />
        <BackgroundImages />
      </body>
    </html>
  );
}
