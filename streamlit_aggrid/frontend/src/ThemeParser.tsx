import {
    colorSchemeDark,
    colorSchemeDarkBlue,
    colorSchemeDarkWarm,
    colorSchemeLight,
    colorSchemeLightCold,
    colorSchemeLightWarm,
    iconSetAlpine,
    iconSetMaterial,
    iconSetQuartz,
    iconSetQuartzBold,
    iconSetQuartzLight,
    iconSetQuartzRegular,
    themeAlpine,
    themeBalham,
    themeQuartz,
    type Part,
    type Theme,
} from "ag-grid-community"

// Components V2 exposes the resolved Streamlit font as a CSS custom property
// on the component wrapper. Keeping the reference as CSS (instead of reading
// computed styles in JavaScript) makes font changes update through the browser's
// cascade without rebuilding the AG Grid theme or touching individual cells.
const streamlitFontFamily = "var(--st-font, inherit)"

type ThemeName = "streamlit" | "alpine" | "balham" | "material" | "custom"
type CustomThemeBase = "quartz" | "alpine" | "balham"
type CustomThemePart =
    | "colorSchemeLight"
    | "colorSchemeLightWarm"
    | "colorSchemeLightCold"
    | "colorSchemeDark"
    | "colorSchemeDarkWarm"
    | "colorSchemeDarkBlue"
    | "iconSetQuartz"
    | "iconSetQuartzLight"
    | "iconSetQuartzBold"
    | "iconSetAlpine"
    | "iconSetMaterial"
    | "iconSetQuartzRegular"

export type StAggridThemeOptions = {
    themeName?: ThemeName
    base?: CustomThemeBase
    params?: Record<string, unknown>
    parts?: CustomThemePart[]
}

class ThemeParser {
    private readonly baseMapper: Record<CustomThemeBase, Theme> = {
        quartz: themeQuartz,
        alpine: themeAlpine,
        balham: themeBalham,
    }

    private readonly partsMapper: Record<CustomThemePart, Part> = {
        colorSchemeLight,
        colorSchemeLightWarm,
        colorSchemeLightCold,
        colorSchemeDark,
        colorSchemeDarkWarm,
        colorSchemeDarkBlue,
        iconSetQuartz: iconSetQuartz(),
        iconSetQuartzLight,
        iconSetQuartzBold,
        iconSetAlpine,
        iconSetMaterial,
        iconSetQuartzRegular,
    }

    streamlitRecipe(): Theme {
        // Streamlit exposes resolved theme values on the V2 component host.
        // Keeping these as CSS references lets light/dark and config changes
        // cascade without rebuilding the grid theme.
        return themeAlpine.withPart(iconSetQuartzRegular).withParams({
            accentColor: "var(--st-primary-color)",
            fontFamily: streamlitFontFamily,
            foregroundColor: "var(--st-text-color)",
            backgroundColor: "var(--st-background-color)",
            chromeBackgroundColor: "var(--st-secondary-background-color)",
            headerBackgroundColor: "var(--st-dataframe-header-background-color)",
            borderColor: "var(--st-dataframe-border-color)",
            browserColorScheme: "inherit",
        })
    }

    alpineRecipe(): Theme {
        return themeAlpine.withParams({
            accentColor: "var(--st-primary-color)",
            fontFamily: streamlitFontFamily,
            foregroundColor: "var(--st-text-color)",
            backgroundColor: "var(--st-background-color)",
        })
    }

    balhamRecipe(): Theme {
        return themeBalham.withParams({
            fontFamily: streamlitFontFamily,
        })
    }

    materialRecipe(): Theme {
        return themeAlpine.withPart(iconSetMaterial).withParams({
            fontFamily: streamlitFontFamily,
        })
    }

    customRecipe(gridOptionsTheme: StAggridThemeOptions): Theme {
        const { base = "quartz", params = {}, parts = [] } = gridOptionsTheme
        let theme = this.baseMapper[base] || themeQuartz

        // A part supplies defaults for a feature. Apply parts first, then the
        // inherited font, and finally user params so explicit values always win.
        for (const partName of parts) {
            const part = this.partsMapper[partName]
            if (part) {
                theme = theme.withPart(part)
            } else {
                console.error(`Unsupported AG Grid theme part: ${partName}`)
            }
        }

        theme = theme.withParams({ fontFamily: streamlitFontFamily })
        if (Object.keys(params).length > 0) {
            theme = theme.withParams(params)
        }

        return theme
    }

    parse(gridOptionsTheme?: StAggridThemeOptions): Theme {
        switch (gridOptionsTheme?.themeName) {
            case "streamlit":
                return this.streamlitRecipe()
            case "alpine":
                return this.alpineRecipe()
            case "balham":
                return this.balhamRecipe()
            case "material":
                return this.materialRecipe()
            case "custom":
                return this.customRecipe(gridOptionsTheme)
            default:
                return this.balhamRecipe()
        }
    }
}

export { ThemeParser }
