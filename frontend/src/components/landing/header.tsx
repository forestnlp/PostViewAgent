import { GitHubLogoIcon } from "@radix-ui/react-icons";
import Link from "next/link";

import { Button } from "@/components/ui/button";
import type { Locale } from "@/core/i18n/locale";
import { getI18n } from "@/core/i18n/server";
import { cn } from "@/lib/utils";

import { MobileNav } from "./mobile-nav";

export type HeaderProps = {
  className?: string;
  homeURL?: string;
  locale?: Locale;
};

export async function Header({ className, homeURL, locale }: HeaderProps) {
  const isExternalHome = !homeURL;
  const { locale: resolvedLocale, t } = await getI18n(locale);
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
          target={isExternalHome ? "_blank" : "_self"}
          rel={isExternalHome ? "noopener noreferrer" : undefined}
          className="font-serif text-xl whitespace-nowrap"
        >
          邮览官
        </a>
      </div>
      <nav className="ml-auto hidden items-center gap-5 text-sm font-medium sm:flex md:mr-8 md:gap-8">
        <a
          href="https://github.com/forestnlp/PostViewAgent/tree/main/docs"
          target="_blank"
          rel="noopener noreferrer"
          className="text-secondary-foreground hover:text-foreground transition-colors"
        >
          {t.home.docs}
        </a>
      </nav>
      <div className="relative">
        <Button
          variant="outline"
          size="sm"
          asChild
          className="group relative z-10"
        >
          <a
            href="https://github.com/forestnlp/PostViewAgent"
            target="_blank"
            rel="noopener noreferrer"
          >
            <GitHubLogoIcon className="size-4" />
            <span className="hidden sm:inline">GitHub</span>
          </a>
        </Button>
      </div>
      <MobileNav
        links={[
          { href: "https://github.com/forestnlp/PostViewAgent/tree/main/docs", label: t.home.docs },
        ]}
      />
      <hr className="from-border/0 via-border/70 to-border/0 absolute top-16 right-0 left-0 z-10 m-0 h-px w-full border-none bg-linear-to-r" />
    </header>
  );
}
