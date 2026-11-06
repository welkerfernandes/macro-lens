export type Field = {name:string;label:string;type?:string;options?:{value:string;label:string}[]};
export const config: {title:string;symbol:string;subtitle:string;headline:string;description:string;provider:string;source:string;notice:string;defaults:Record<string,string>;fields:Field[]} = {
  "title": "Macro Lens",
  "symbol": "⌁",
  "subtitle": "Economic indicators, with context",
  "headline": "Contexto para grandes decisões.",
  "description": "Compare séries econômicas com tendências descritivas e origem verificável.",
  "provider": "World Bank",
  "source": "https://data.worldbank.org/",
  "notice": "Tendências descritivas não são previsões. Valores de demonstração são sintéticos para todos os indicadores.",
  "defaults": {
    "countries": "BRA,PRT",
    "indicator": "NY.GDP.PCAP.CD",
    "start_year": "2015",
    "end_year": "2024"
  },
  "fields": [
    {
      "name": "countries",
      "label": "Comparação",
      "options": [
        {
          "value": "BRA,PRT",
          "label": "Brasil × Portugal"
        },
        {
          "value": "BRA,USA",
          "label": "Brasil × Estados Unidos"
        },
        {
          "value": "BRA,DEU,CHL",
          "label": "Brasil × Alemanha × Chile"
        }
      ]
    },
    {
      "name": "indicator",
      "label": "Indicador",
      "options": [
        {
          "value": "NY.GDP.PCAP.CD",
          "label": "PIB per capita · US$ correntes"
        },
        {
          "value": "FP.CPI.TOTL.ZG",
          "label": "Inflação · % anual"
        },
        {
          "value": "SL.UEM.TOTL.ZS",
          "label": "Desemprego · % força de trabalho"
        }
      ]
    },
    {
      "name": "start_year",
      "label": "Ano inicial",
      "type": "number"
    },
    {
      "name": "end_year",
      "label": "Ano final",
      "type": "number"
    }
  ]
};
