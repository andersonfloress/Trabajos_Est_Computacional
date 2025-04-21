library(shiny)
library(readxl)
library(ggplot2)
library(dplyr)
library(tidyr)
library(shinythemes)
library(car)
library(DescTools)
library(tseries)
library(nortest)

ui <- fluidPage(
  theme = shinytheme("slate"),
  titlePanel("App para Realizar Pruebas Estadísticas"),
  
  sidebarLayout(
    sidebarPanel(
      selectInput("data_type", "Selecciona el tipo de prueba:",
                  choices = c("Cuantitativa" = "cuantitativa", 
                              "Cualitativa" = "cualitativa", 
                              "Normalidad" = "normalidad")),
      
      uiOutput("test_select_ui"),
      
      fileInput("file", "Cargar archivo Excel", accept = c(".xlsx", ".xls")),
      
      uiOutput("specific_test_options"),
      
      actionButton("run_test", "Realizar Prueba"),
      
      textOutput("validation_message")
    ),
    
    mainPanel(
      tabsetPanel(
        tabPanel("Resultados",
                 h3("Resultados"),
                 verbatimTextOutput("test_result")
        ),
        tabPanel("Descripción de Pruebas Estadísticas",
                 h3("Prueba T-test"),
                 p("Se utiliza para comparar las medias de dos grupos..."),
                 h3("Prueba ANOVA"),
                 p("Es una extensión del t-test que permite comparar las medias de tres o más grupos...")
        )
      )
    )
  )
)

server <- function(input, output, session) {
  
  datos_originales <- reactive({
    req(input$file)
    ext <- tools::file_ext(input$file$name)
    if (ext %in% c("xlsx", "xls")) {
      df <- read_excel(input$file$datapath)
      return(df)
    } else {
      stop("Por favor, sube un archivo de Excel (.xlsx)")
    }
  })
  
  datos <- reactive({
    req(input$file)
    req(input$data_type)
    
    if (input$data_type == "normalidad") {
      return(datos_originales())
    }
    
    df <- datos_originales()
    if (all(sapply(df, is.numeric)) && ncol(df) >= 2) {
      df_largo <- pivot_longer(df,
                               cols = everything(),
                               names_to = "grupo",
                               values_to = "valor")
      return(df_largo)
    }
    return(df)
  })
  
  output$test_select_ui <- renderUI({
    req(input$data_type)
    
    if (input$data_type == "cuantitativa") {
      return(selectInput("test_type", "Selecciona la prueba cuantitativa:",
                         choices = c("Prueba T (2 grupos)" = "ttest",
                                     "ANOVA + Tukey (> 2 grupos)" = "anova_tukey",
                                     "Wilcoxon (Mann-Whitney)" = "wilcoxon",
                                     "Correlación Pearson" = "pearson",
                                     "Correlación Spearman" = "spearman")))
    }
    
    if (input$data_type == "cualitativa") {
      return(selectInput("test_type", "Selecciona la prueba cualitativa:",
                         choices = c("Chi-cuadrado" = "chi_squared",
                                     "McNemar" = "mcnemar",
                                     "Q de Cochran" = "cochran_q")))
    }
    
    if (input$data_type == "normalidad") {
      return(selectInput("test_type", "Selecciona la prueba de normalidad:",
                         choices = c("Shapiro-Wilk" = "shapiro_wilk",
                                     "Kolmogorov-Smirnov" = "ks_test",
                                     "Lilliefors" = "lilliefors",
                                     "Jarque-Bera" = "jarque_bera")))
    }
  })
  
  output$specific_test_options <- renderUI({
    req(input$test_type)
    
    df <- if(input$data_type == "normalidad") datos_originales() else datos()
    if(is.null(df)) return(NULL)
    
    if (input$test_type == "cochran_q") {
      all_cols <- names(df)
      if (length(all_cols) <= 1) {
        return("Se necesitan al menos 2 columnas para la prueba Q de Cochran")
      }
      selected_cols <- if (length(all_cols) > 1) all_cols[-1] else NULL
      
      return(selectInput("selected_columns", "Selecciona las columnas para la prueba Q de Cochran:", 
                         choices = all_cols,
                         selected = selected_cols,
                         multiple = TRUE))
    }
    
    if (input$test_type == "shapiro_wilk" || input$test_type == "lilliefors" || input$test_type == "jarque_bera") {
      column_names <- names(datos_originales())
      
      return(selectInput("columna_normalidad", "Selecciona la columna para analizar:", 
                         choices = column_names))
    }
    
    if (input$test_type == "ks_test") {
      column_names <- names(datos_originales())
      
      return(tagList(
        selectInput("columna_ks_1", "Selecciona la primera columna:", 
                    choices = column_names),
        selectInput("columna_ks_2", "Selecciona la segunda columna (opcional, compara con distribución normal si se omite):", 
                    choices = c("Usar distribución normal" = "normal", column_names))
      ))
    }
    
    return(NULL)
  })
  
  resultado <- eventReactive(input$run_test, {
    if (input$data_type == "normalidad") {
      df <- datos_originales()
    } else {
      df <- datos()
    }
    
    if (input$test_type == "ttest") {
      if (ncol(df) < 2) {
        return("El archivo debe tener al menos 2 columnas para la prueba T.")
      }
      grupo <- as.factor(df[[1]])
      valores <- as.numeric(df[[2]])
      
      if (length(unique(grupo)) != 2) {
        return("Aviso: La prueba T requiere exactamente 2 grupos.")
      }
      test_result <- t.test(valores ~ grupo, var.equal = TRUE)
      return(test_result)
    }
    
    if (input$test_type == "anova_tukey") {
      if (ncol(df) < 2) {
        return("El archivo debe tener al menos 2 columnas para ANOVA.")
      }
      grupo <- as.factor(df[[1]])
      valores <- as.numeric(df[[2]])
      
      if (length(unique(grupo)) < 3) {
        return("Aviso: La prueba ANOVA + Tukey requiere al menos 3 grupos.")
      }
      anova_result <- aov(valores ~ grupo, data = df)
      tukey_result <- TukeyHSD(anova_result)
      return(list(ANOVA = summary(anova_result), Tukey = tukey_result))
    }
    
    if (input$test_type == "wilcoxon") {
      if (ncol(df) < 2) {
        return("El archivo debe tener al menos 2 columnas para la prueba Wilcoxon.")
      }
      grupo <- as.factor(df[[1]])
      valores <- as.numeric(df[[2]])
      
      test_result <- wilcox.test(valores ~ grupo)
      return(test_result)
    }
    
    if (input$test_type == "pearson") {
      if (ncol(df) < 2) {
        return("El archivo debe tener al menos 2 columnas para la correlación de Pearson.")
      }
      x <- as.numeric(df[[1]])
      y <- as.numeric(df[[2]])
      
      test_result <- cor.test(x, y, method = "pearson")
      return(test_result)
    }
    
    if (input$test_type == "spearman") {
      if (ncol(df) < 2) {
        return("El archivo debe tener al menos 2 columnas para la correlación de Spearman.")
      }
      x <- as.numeric(df[[1]])
      y <- as.numeric(df[[2]])
      
      test_result <- cor.test(x, y, method = "spearman")
      return(test_result)
    }
    
    if (input$test_type == "chi_squared") {
      if (ncol(df) < 2) {
        return("El archivo debe tener al menos 2 columnas para la prueba Chi-cuadrado.")
      }
      var1 <- df[[1]]
      var2 <- df[[2]]
      
      test_result <- chisq.test(table(var1, var2))
      return(test_result)
    }
    
    if (input$test_type == "mcnemar") {
      if (ncol(df) < 2) {
        return("El archivo debe tener al menos 2 columnas para la prueba McNemar.")
      }
      Antes <- df[[1]]
      Despues <- df[[2]]
      
      test_result <- mcnemar.test(table(Antes, Despues))
      return(test_result)
    }
    
    if (input$test_type == "cochran_q") {
      req(input$selected_columns)
      selected_cols <- input$selected_columns
      
      if (length(selected_cols) < 1) {
        return("Debes seleccionar al menos una columna para la prueba Q de Cochran.")
      }
      
      df_bin <- df[, selected_cols, drop = FALSE]
      
      if (any(df_bin != 0 & df_bin != 1)) {
        return("Los datos deben ser binarios (0 o 1) para la prueba de Cochran.")
      }
      
      return(DescTools::CochranQTest(as.matrix(df_bin)))
    }
    
    if (input$test_type == "shapiro_wilk") {
      req(input$columna_normalidad)
      columna_valores <- na.omit(df[[input$columna_normalidad]])
      
      if (!is.numeric(columna_valores)) {
        return("La columna seleccionada debe contener valores numéricos.")
      }
      
      test_result <- shapiro.test(columna_valores)
      return(test_result)
    }
    
    if (input$test_type == "lilliefors") {
      req(input$columna_normalidad)
      columna_valores <- na.omit(df[[input$columna_normalidad]])
      
      if (!is.numeric(columna_valores)) {
        return("La columna seleccionada debe contener valores numéricos.")
      }
      
      test_result <- lillie.test(columna_valores)
      return(test_result)
    }
    
    if (input$test_type == "jarque_bera") {
      req(input$columna_normalidad)
      columna_valores <- na.omit(df[[input$columna_normalidad]])
      
      if (!is.numeric(columna_valores)) {
        return("La columna seleccionada debe contener valores numéricos.")
      }
      
      test_result <- jarque.bera.test(columna_valores)
      return(test_result)
    }
    
    if (input$test_type == "ks_test") {
      req(input$columna_ks_1)
      columna_valores_1 <- na.omit(df[[input$columna_ks_1]])
      
      if (!is.numeric(columna_valores_1)) {
        return("La primera columna seleccionada debe contener valores numéricos.")
      }
      
      if (input$columna_ks_2 == "normal") {
        test_result <- ks.test(columna_valores_1, "pnorm", mean(columna_valores_1), sd(columna_valores_1))
      } else {
        columna_valores_2 <- na.omit(df[[input$columna_ks_2]])
        
        if (!is.numeric(columna_valores_2)) {
          return("La segunda columna seleccionada debe contener valores numéricos.")
        }
        
        test_result <- ks.test(columna_valores_1, columna_valores_2)
      }
      
      return(test_result)
    }
  })
  
  output$test_result <- renderPrint({
    resultado()
  })
  
  output$validation_message <- renderText({
    req(input$run_test)
    return("Prueba completada correctamente.")
  })
}

shinyApp(ui = ui, server = server)

