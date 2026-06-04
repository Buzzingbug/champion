export interface ThemeDefinition {
  id: string;
  name: string;
  vocabulary: {
    win: string;
    lose: string;
    tie: string;
  };
  colors: {
    primary: string;
    secondary: string;
  };
}
