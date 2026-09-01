import { create } from 'zustand';

export type ThemeMode = 'l1' | 'l2' | 'l3' | 'd';
export type LightThemeVariant = 'l1' | 'l2' | 'l3';

interface ThemeState {
  themeMode: ThemeMode;
  lastLightVariant: LightThemeVariant;
  setThemeMode: (mode: ThemeMode) => void;
  toggleDarkLight: () => void;
  setLightVariant: (variant: LightThemeVariant) => void;
}

const applyThemeToDocument = (mode: ThemeMode) => {
  if (typeof document === 'undefined') return;
  const body = document.body;
  body.classList.remove('palette-arctic', 'palette-iris', 'theme-light');
  document.documentElement.removeAttribute('data-theme');

  if (mode === 'l1') {
    body.classList.add('theme-light');
  } else if (mode === 'l2') {
    body.classList.add('palette-arctic', 'theme-light');
  } else if (mode === 'l3') {
    body.classList.add('palette-iris', 'theme-light');
  }
};

const savedMode = (typeof localStorage !== 'undefined' && (localStorage.getItem('synthexis_theme_mode') as ThemeMode)) || 'l1';
const savedLight = (typeof localStorage !== 'undefined' && (localStorage.getItem('synthexis_last_light_variant') as LightThemeVariant)) || 'l1';

const initialMode: ThemeMode = savedMode;
const initialLight: LightThemeVariant = savedMode !== 'd' ? (savedMode as LightThemeVariant) : savedLight;

if (typeof document !== 'undefined') {
  applyThemeToDocument(initialMode);
}

export const useThemeStore = create<ThemeState>((set, get) => ({
  themeMode: initialMode,
  lastLightVariant: initialLight,

  setThemeMode: (mode: ThemeMode) => {
    applyThemeToDocument(mode);
    if (typeof localStorage !== 'undefined') {
      localStorage.setItem('synthexis_theme_mode', mode);
      if (mode !== 'd') {
        localStorage.setItem('synthexis_last_light_variant', mode);
      }
    }
    set({
      themeMode: mode,
      ...(mode !== 'd' ? { lastLightVariant: mode as LightThemeVariant } : {})
    });
  },

  toggleDarkLight: () => {
    const current = get().themeMode;
    if (current === 'd') {
      const target = get().lastLightVariant || 'l1';
      get().setThemeMode(target);
    } else {
      get().setThemeMode('d');
    }
  },

  setLightVariant: (variant: LightThemeVariant) => {
    get().setThemeMode(variant);
  }
}));
