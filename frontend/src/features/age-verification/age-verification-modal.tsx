"use client";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { createLogger } from "@/lib/logger";
import { useEffect, useState } from "react";

const logger = createLogger("AgeVerification");

interface AgeVerificationModalProps {
  isOpen: boolean;
  onVerified: () => void;
  onDeclined: () => void;
}

export function AgeVerificationModal({
  isOpen,
  onVerified,
  onDeclined,
}: AgeVerificationModalProps) {
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    if (isOpen) {
      logger.info("Age verification modal opened");
      setIsVisible(true);
    }
  }, [isOpen]);

  const handleYes = () => {
    logger.info("User confirmed they are 18 years or older");
    setIsVisible(false);
    onVerified();
  };

  const handleNo = () => {
    logger.info("User declined age verification");
    setIsVisible(false);
    onDeclined();
  };

  if (!isVisible) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm">
      <div className="mx-4 max-w-md">
        <Card className="border-border/50">
          <CardHeader className="text-center">
            <CardTitle className="text-xl font-bold">年齢確認</CardTitle>
            <CardDescription className="text-base">
              このサイトは成人向けコンテンツが含まれています
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="text-center">
              <p className="text-lg font-medium text-foreground">あなたは18歳以上ですか？</p>
            </div>
            <div className="flex gap-4">
              <Button onClick={handleYes} className="flex-1" size="lg">
                はい
              </Button>
              <Button onClick={handleNo} variant="outline" className="flex-1" size="lg">
                いいえ
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
