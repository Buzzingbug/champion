import { ThemeDefinition } from './base.theme';
import { gamingTheme } from './presets/gaming';
import { fashionTheme } from './presets/fashion';
import { SportsTheme } from './presets/sports';
import { MusicTheme } from './presets/music';
import { AdultTheme } from './presets/adult';
import { AnimeTheme } from './presets/anime';

export const THEME_REGISTRY: Record<string, ThemeDefinition> = {
  gaming: gamingTheme,
  fashion: fashionTheme,
  sports: SportsTheme,
  music: MusicTheme,
  adult: AdultTheme,
  anime: AnimeTheme,
};
