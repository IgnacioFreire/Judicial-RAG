import { KeyRound, LogOut, Moon, Sun, UserRound } from "lucide-react"
import { useEffect, useState } from "react"

import { HelpButton } from "@/components/HelpButton"
import { KeysDialog } from "@/components/KeysDialog"
import { Button } from "@/components/ui/button"
import { useI18n } from "@/i18n/context"
import { loadProfile, signOut } from "@/lib/api"
import type { ProfileView } from "@/lib/types"
import { useWorkspace } from "@/workspace"

function flag(configured: boolean, messages: { configured: string; missing: string }) {
  return configured ? messages.configured : messages.missing
}

export function ProfileMenu() {
  const { messages, locale, setLocale, theme, setTheme } = useI18n()
  const t = messages.profile
  const { session, reload } = useWorkspace()
  const [open, setOpen] = useState(false)
  const [keysOpen, setKeysOpen] = useState(false)
  const [profile, setProfile] = useState<ProfileView | null>(null)
  const [profileError, setProfileError] = useState<string | null>(null)
  const [signingOut, setSigningOut] = useState(false)

  useEffect(() => {
    if (!open) {
      return
    }
    loadProfile()
      .then((value) => {
        setProfile(value)
        setProfileError(null)
      })
      .catch((error: Error) => setProfileError(error.message))
  }, [open, session.is_processing])

  async function handleSignOut() {
    setSigningOut(true)
    try {
      await signOut()
      setOpen(false)
      await reload()
    } catch (error) {
      setProfileError(error instanceof Error ? error.message : "Sign out failed")
    } finally {
      setSigningOut(false)
    }
  }

  return (
    <>
      <div className="relative">
        <Button
          type="button"
          variant="outline"
          className="rounded-full"
          onClick={() => setOpen((value) => !value)}
        >
          <UserRound className="size-4" />
          {t.title}
        </Button>
        {open ? (
          <div
            className="absolute right-0 z-20 mt-2 w-[min(100vw-2rem,22rem)] rounded-2xl border border-border bg-card p-4 text-sm shadow-lg"
            role="dialog"
            aria-label={t.title}
          >
            <div className="mb-3 flex items-center justify-between gap-2">
              <p className="font-semibold">{t.title}</p>
              <HelpButton helpKey="profile" />
            </div>
            {profileError ? <p className="mb-2 text-destructive">{profileError}</p> : null}
            {profile ? (
              <dl className="space-y-2 text-card-foreground">
                <div>
                  <dt className="text-xs text-muted-foreground">{t.account}</dt>
                  <dd>{profile.email || messages.common.notSet}</dd>
                </div>
                <div>
                  <dt className="text-xs text-muted-foreground">{t.llm}</dt>
                  <dd>
                    {profile.llm_provider} · {profile.llm_model}
                  </dd>
                </div>
                <div>
                  <dt className="text-xs text-muted-foreground">{t.activeLlmKey}</dt>
                  <dd>{flag(profile.llm_key_configured, messages.common)}</dd>
                </div>
                <div>
                  <dt className="text-xs text-muted-foreground">{t.embeddings}</dt>
                  <dd>
                    {profile.embedding_provider} · {profile.embedding_model}
                  </dd>
                </div>
                <div>
                  <dt className="text-xs text-muted-foreground">{t.hfKey}</dt>
                  <dd>{flag(profile.huggingface_key_configured, messages.common)}</dd>
                </div>
                <div>
                  <dt className="text-xs text-muted-foreground">{t.tokens}</dt>
                  <dd>
                    in {profile.input_tokens} · out {profile.output_tokens}
                  </dd>
                  <dd className="text-xs text-muted-foreground">{t.tokensHint}</dd>
                </div>
              </dl>
            ) : (
              <p className="text-muted-foreground">{messages.common.loading}</p>
            )}
            <div className="mt-4 space-y-3 border-t border-border pt-4">
              <div>
                <p className="mb-1 text-xs font-medium text-muted-foreground">{t.theme}</p>
                <div className="flex gap-2">
                  <Button
                    type="button"
                    size="sm"
                    variant={theme === "light" ? "default" : "outline"}
                    onClick={() => setTheme("light")}
                  >
                    <Sun className="size-3.5" />
                    {messages.theme.light}
                  </Button>
                  <Button
                    type="button"
                    size="sm"
                    variant={theme === "dark" ? "default" : "outline"}
                    onClick={() => setTheme("dark")}
                  >
                    <Moon className="size-3.5" />
                    {messages.theme.dark}
                  </Button>
                </div>
              </div>
              <div>
                <p className="mb-1 text-xs font-medium text-muted-foreground">{t.language}</p>
                <div className="flex gap-2">
                  <Button
                    type="button"
                    size="sm"
                    variant={locale === "en" ? "default" : "outline"}
                    onClick={() => setLocale("en")}
                  >
                    {messages.locale.en}
                  </Button>
                  <Button
                    type="button"
                    size="sm"
                    variant={locale === "es" ? "default" : "outline"}
                    onClick={() => setLocale("es")}
                  >
                    {messages.locale.es}
                  </Button>
                </div>
              </div>
              <div className="flex flex-wrap gap-2">
                <Button type="button" size="sm" variant="outline" onClick={() => setKeysOpen(true)}>
                  <KeyRound className="size-3.5" />
                  {t.keys}
                </Button>
                <Button
                  type="button"
                  size="sm"
                  variant="outline"
                  disabled={signingOut || session.is_processing}
                  onClick={() => void handleSignOut()}
                >
                  <LogOut className="size-3.5" />
                  {t.signOut}
                </Button>
              </div>
            </div>
          </div>
        ) : null}
      </div>
      <KeysDialog
        open={keysOpen}
        onClose={() => setKeysOpen(false)}
        onSaved={() => {
          loadProfile()
            .then(setProfile)
            .catch(() => undefined)
        }}
      />
    </>
  )
}
