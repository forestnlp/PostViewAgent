import { GitHubLogoIcon } from "@radix-ui/react-icons";
import Link from "next/link";

import { Button } from "@/components/ui/button";
import type { Locale } from "@/core/i18n/locale";
import { getI18n } from "@/core/i18n/server";
import { cn } from "@/lib/utils";

export type HeaderProps = {
  className?: string;
  homeURL?: string;
  locale?: Locale;
  hideOnHome?: boolean;  // 是否在首页隐藏 Header
};

export async function Header({ className, homeURL, locale, hideOnHome }: HeaderProps) {
  // 如果是首页且设置了 hideOnHome，完全隐藏 Header
  if (hideOnHome) {
    return null;
  }
  
  return (
    <header
      className={cn(
        "container-md fixed top-0 right-0 left-0 z-20 mx-auto flex h-16 items-center justify-between px-4 backdrop-blur-xs",
        className,
      )}
    >
      {/* Header 内容区域（可选） */}
    </header>
  );
}
