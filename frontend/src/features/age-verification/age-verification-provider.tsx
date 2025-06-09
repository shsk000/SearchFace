"use client";

import {
  confirmAgeVerification,
  declineAgeVerification,
} from "@/actions/age-verification/age-verification";
import { AgeVerificationModal } from "@/features/age-verification/age-verification-modal";
import { createLogger } from "@/lib/logger";
import { useState, useTransition } from "react";

const logger = createLogger("AgeVerificationProvider");

interface AgeVerificationProviderProps {
  children: React.ReactNode;
  isAgeVerified: boolean;
}

export function AgeVerificationProvider({ children, isAgeVerified }: AgeVerificationProviderProps) {
  const [showModal, setShowModal] = useState(!isAgeVerified);
  const [isPending, startTransition] = useTransition();

  const handleVerified = () => {
    startTransition(async () => {
      try {
        await confirmAgeVerification();
        setShowModal(false);
        logger.info("Age verification completed successfully");
      } catch (error) {
        logger.error("Failed to complete age verification", error);
        // モーダルを閉じずにエラー処理
      }
    });
  };

  const handleDeclined = () => {
    startTransition(async () => {
      try {
        await declineAgeVerification();
      } catch (error) {
        logger.error("Failed to handle age verification decline", error);
        // declineAgeVerificationは必ずリダイレクトするためここには到達しない
      }
    });
  };

  return (
    <>
      {children}
      <AgeVerificationModal
        isOpen={showModal && !isPending}
        onVerified={handleVerified}
        onDeclined={handleDeclined}
      />
    </>
  );
}
