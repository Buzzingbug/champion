import { gamingTheme } from './presets/gaming';
import { fashionTheme } from './presets/fashion';
import { ThemeDefinition } from './base.theme';

export const THEME_REGISTRY: Record<string, ThemeDefinition> = {
  'gaming': gamingTheme,
  'fashion': fashionTheme,
};
