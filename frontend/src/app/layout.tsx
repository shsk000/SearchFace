import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import StructuredData from "@/components/StructuredData";
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
    default: "そっくりAV - AI顔画像検索システム", // フォールバック用
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
        <GoogleAnalytics />
        <StructuredData />
        <AgeVerificationProvider isAgeVerified={ageVerified}>{children}</AgeVerificationProvider>
        <Toaster />
        <BackgroundImages />
      </body>
    </html>
  );
}
