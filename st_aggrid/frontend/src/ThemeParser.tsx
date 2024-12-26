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
    Part,
} from 'ag-grid-community';
import _ from 'lodash';

import { Theme as StreamlitTheme } from "streamlit-component-lib"

type stAggridThemeOptions = {
    themeName: string,
    base: string,
    params: [key: string]
    parts: string[],


}

class ThemeParser {
    private baseMapper : { [key: string] : Theme} = {
        quartz: themeQuartz, 
        alpine: themeAlpine,
        balham: themeBalham
    }

    private partsMapper : { [key: string ] : Part }= {
        colorSchemeLight: colorSchemeLight, 
        colorSchemeLightWarm: colorSchemeLightWarm,
        colorSchemeLightCold: colorSchemeLightCold,
        colorSchemeDark: colorSchemeDark,
        colorSchemeDarkWarm: colorSchemeDarkWarm,
        colorSchemeDarkBlue: colorSchemeDarkBlue,
        iconSetQuartz: iconSetQuartz(undefined),
        iconSetQuartzLight: iconSetQuartzLight,
        iconSetQuartzBold: iconSetQuartzBold,
        iconSetAlpine: iconSetAlpine,
        iconSetMaterial: iconSetMaterial,
        iconSetQuartzRegular: iconSetQuartzRegular
    }

    streamlitRecipe(streamlitTheme: StreamlitTheme): Theme{
        let theme : Theme = this.baseMapper['alpine']
        const font = streamlitTheme?.font.split(",").at(1)?.trim() || "Source Sans Pro"
        const fontFamily = [font, {googleFont: font}]

        theme = theme.withParams({
            accentColor: streamlitTheme?.primaryColor,
            fontFamily: fontFamily,
            foregroundColor: streamlitTheme.textColor,
            backgroundColor: streamlitTheme.backgroundColor
        }).withPart(iconSetQuartzRegular)
        .withPart(this.partsMapper.iconSetQuartzRegular)
        if (streamlitTheme?.base === 'dark'){
            theme = theme.withPart(colorSchemeDark)
        }

        return theme
    }

    alpineRecipe() {
        return themeAlpine
    }

    balhamRecipe() {
        return this.baseMapper.themeBalham
    }

    materialRecipe() {
        return themeAlpine.withPart(iconSetMaterial)
    }

    customRecipe(gridOptionsTheme: stAggridThemeOptions, streamlitTheme?: StreamlitTheme) : Theme {
        const {base, params, parts} = gridOptionsTheme

        let theme: Theme = this.baseMapper[base]

        if (! _.isEmpty(params)){
            theme = theme.withParams(params)
        }

        if (! _.isEmpty(parts)){
            theme = parts.reduce((acc, partName) => {const part =  this.partsMapper[partName];  return acc.withPart(part)}, theme)
    
        }
      
        return theme
    }


    parse(gridOptionsTheme: stAggridThemeOptions, streamlitTheme?: StreamlitTheme) : Theme {
        const { themeName } = gridOptionsTheme;

        const recipeMapper: { [key: string]: () => Theme } = {
            streamlit: () => this.streamlitRecipe(streamlitTheme!),
            alpine: () => this.alpineRecipe(),
            balham: () => this.balhamRecipe(),
            material: () => this.materialRecipe(),
            custom: () => this.customRecipe(gridOptionsTheme, streamlitTheme)
        };

        const recipe = recipeMapper[themeName] || (() => themeBalham);
        return recipe();
    }
}


export {ThemeParser}