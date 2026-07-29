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
};

export async function Header({ className, homeURL, locale }: HeaderProps) {
  const { locale: resolvedLocale } = await getI18n(locale);
  const lang = resolvedLocale.substring(0, 2);
  return (
    <header
      className={cn(
        "container-md fixed top-0 right-0 left-0 z-20 mx-auto flex h-16 items-center justify-between gap-3 px-4 backdrop-blur-xs",
        className,
      )}
    >
      <div className="flex min-w-0 items-center gap-6">
        <a
          href={homeURL ?? "https://github.com/forestnlp/PostViewAgent"}
          target={homeURL ? "_self" : "_blank"}
          rel={homeURL ? undefined : "noopener noreferrer"}
          className="font-serif text-xl whitespace-nowrap"
        >
          邮览官
        </a>
      </div>
    </header>
  );
}
