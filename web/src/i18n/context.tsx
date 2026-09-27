import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react"

import { en, type Messages } from "./en"
import { es } from "./es"

export type Locale = "en" | "es"
export type Theme = "light" | "dark"

type HelpKey = keyof Messages["help"]

type I18nContextValue = {
  locale: Locale
  setLocale: (value: Locale) => void
  theme: Theme
  setTheme: (value: Theme) => void
  messages: Messages
  help: (key: HelpKey) => { title: string; body: string }
}

const LOCALE_KEY = "jr_locale"
const THEME_KEY = "jr_theme"

const I18nContext = createContext<I18nContextValue | null>(null)

function readLocale(): Locale {
  const stored = localStorage.getItem(LOCALE_KEY)
  return stored === "es" ? "es" : "en"
}

function readTheme(): Theme {
  const stored = localStorage.getItem(THEME_KEY)
  return stored === "dark" ? "dark" : "light"
}

function applyTheme(theme: Theme) {
  document.documentElement.classList.toggle("dark", theme === "dark")
}

export function I18nProvider({ children }: { children: ReactNode }) {
  const [locale, setLocaleState] = useState<Locale>(() => readLocale())
  const [theme, setThemeState] = useState<Theme>(() => readTheme())

  const setLocale = useCallback((value: Locale) => {
    localStorage.setItem(LOCALE_KEY, value)
    setLocaleState(value)
  }, [])

  const setTheme = useCallback((value: Theme) => {
    localStorage.setItem(THEME_KEY, value)
    setThemeState(value)
    applyTheme(value)
  }, [])

  useEffect(() => {
    applyTheme(theme)
  }, [theme])

  const messages: Messages = locale === "es" ? (es as Messages) : en

  const help = useCallback(
    (key: HelpKey) => messages.help[key],
    [messages],
  )

  const value = useMemo(
    () => ({ locale, setLocale, theme, setTheme, messages, help }),
    [locale, setLocale, theme, setTheme, messages, help],
  )

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>
}

export function useI18n(): I18nContextValue {
  const value = useContext(I18nContext)
  if (!value) {
    throw new Error("I18nProvider is missing")
  }
  return value
}
