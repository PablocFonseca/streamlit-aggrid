import { themeQuartz,
    themeAlpine, 
    themeBalham, 
    Theme, 
    colorSchemeLight, 
    colorSchemeLightWarm, 
    colorSchemeLightCold,
    colorSchemeDark,
    colorSchemeDarkWarm,  
    colorSchemeDarkBlue,
    iconSetQuartz,
    iconSetQuartzLight,
    iconSetQuartzBold,
    iconSetAlpine,
    iconSetMaterial,
    iconSetQuartzRegular,
} from 'ag-grid-community';

import { Theme as StreamlitTheme } from "streamlit-component-lib"

type stAggridThemeOptions = {
    themeName: string,
    withParts: string[],

}

class ThemeParser {
    private baseMapper = {
        themeQuartz: themeQuartz, 
        themeAlpine: themeAlpine,
        themeBalham: themeBalham
    }

    private partsMapper = {
        colorSchemeLight: colorSchemeLight, 
        colorSchemeLightWarm: colorSchemeLightWarm,
        colorSchemeLightCold: colorSchemeLightCold,
        colorSchemeDark: colorSchemeDark,
        colorSchemeDarkWarm: colorSchemeDarkWarm,
        colorSchemeDarkBlue: colorSchemeDarkBlue,
        iconSetQuartz: iconSetQuartz,
        iconSetQuartzLight: iconSetQuartzLight,
        iconSetQuartzBold: iconSetQuartzBold,
        iconSetAlpine: iconSetAlpine,
        iconSetMaterial: iconSetMaterial,
        iconSetQuartzRegula: iconSetQuartzRegular
    }

    streamlitRecipe(streamlitTheme: StreamlitTheme): Theme{
        let theme : Theme = this.baseMapper.themeBalham
        let font = streamlitTheme?.font.split(",").at(1)?.trim() || "Source Sans Pro"
        let fontFamily = [font, {googleFont: font}]

        theme = theme.withParams({
            accentColor: streamlitTheme?.primaryColor,
            fontFamily: fontFamily,
            foregroundColor: streamlitTheme.textColor,
            backgroundColor: streamlitTheme.backgroundColor
        }
        ).withPart(iconSetQuartzRegular)

        if (streamlitTheme?.base === 'dark'){
            theme = theme.withPart(colorSchemeDark)
        }

        return theme
    }


    parse(gridOptionsTheme: stAggridThemeOptions, streamlitTheme?: StreamlitTheme) : Theme {
        let {themeName = 'streamlit'} = gridOptionsTheme;

        if ((themeName === 'streamlit') && (streamlitTheme !== undefined)) {
            return this.streamlitRecipe(streamlitTheme)
        }

        return themeBalham
    }
}


export {ThemeParser}