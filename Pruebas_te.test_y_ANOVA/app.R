library(shiny)
library(readxl)
library(ggplot2)
library(dplyr)
library(multcomp)
library(car)
library(tidyr)
library(shinythemes)

ui <- fluidPage(
  theme = shinytheme("slate"),
  titlePanel("App Para Realizar Pruebas Estadísticas: T-test y ANOVA - Tukey"),
  
  sidebarLayout(
    sidebarPanel(
      radioButtons("test_type", "Selecciona la prueba a realizar:",
                   choices = c("Prueba T (2 grupos)" = "ttest", "ANOVA (> 2 grupos) + Tukey" = "anova")),
      
      fileInput("file", "Cargar archivo Excel", accept = c(".xlsx", ".xls")),
      
      uiOutput("var_select_ui"),
      
      uiOutput("group_filter_ui"),
      
      selectInput("plot_type", "Selecciona el tipo de gráfico:", 
                  choices = c("Boxplot" = "boxplot", 
                              "Barras con Error Estándar" = "bar_error", 
                              "Gráfico de Puntos" = "dotplot", 
                              "Violin Plot" = "violin_plot", 
                              "Histogramas por Grupo" = "histogram")),
      
      actionButton("run_test", "Realizar Prueba")
    ),
    
    mainPanel(
      tabsetPanel(
        tabPanel("Resultados",
                 h3("Resultados"),
                 verbatimTextOutput("test_result"),
                 plotOutput("plot_result")
        ),
        tabPanel("Descripción de Pruebas Estadísticas",
                 h3("Prueba T-test"),
                 p("Se utiliza para comparar las medias de dos grupos independientes o relacionados y determinar si existen diferencias significativas entre ellas. Puede ser para muestras independientes (cuando los grupos no están relacionados) o muestras relacionadas (cuando hay algún vínculo entre los grupos)."),
                 h3("Prueba ANOVA (Análisis de Varianza)"),
                 p("Es una extensión del t-test que permite comparar las medias de tres o más grupos. Evalúa si las diferencias entre las medias de los grupos son estadísticamente significativas, considerando la variabilidad dentro y entre los grupos."),
                 h3("Prueba de Tukey"),
                 p("Es un procedimiento post-hoc usado después de realizar un ANOVA. Su propósito es identificar qué pares de grupos específicos tienen diferencias significativas entre sus medias. Es útil cuando ANOVA muestra diferencias significativas, pero no indica cuáles grupos son diferentes.")
        ),
        tabPanel("Instrucciones para Usar la Aplicación",
                 h3("Instrucciones"),
                 tags$ol(
                   tags$li("Carga tu archivo de datos en formato EXCEL (xlsx)."),
                   tags$li("Selecciona las variables o columnas que deseas analizar."),
                   tags$li("Visualiza los resultados generados de las pruebas y los graficos.")
                 )
        ),
        tabPanel("Notas Importantes",
                 h3("Notas"),
                 tags$ul(
                   tags$li("La prueba T solo admite 2 grupos."),
                   tags$li("La Prueba de ANOVA-Tukey admite 3 o más grupos.")
                 )
        ),
        tabPanel("Gráficos Disponibles",
                 h3("Gráficos para la Prueba T:"),
                 tags$ul(
                   tags$li("Boxplot"),
                   tags$li("Barras con Error Estándar")
                 ),
                 h3("Gráficos para la Prueba de ANOVA-Tukey:"),
                 tags$ul(
                   tags$li("Boxplot"),
                   tags$li("Barras con Error Estándar"),
                   tags$li("Gráfico de Puntos"),
                   tags$li("Violin Plot"),
                   tags$li("Histogramas por Grupo")
                 )
        )
      )
    )
  )
)

server <- function(input, output, session) {
  
  datos <- reactive({
    req(input$file)
    ext <- tools::file_ext(input$file$name)
    if (ext %in% c("xlsx", "xls")) {
      df <- read_excel(input$file$datapath)
      
      if (all(sapply(df, is.numeric)) && ncol(df) >= 2) {
        df_largo <- pivot_longer(df,
                                 cols = everything(),
                                 names_to = "grupo",
                                 values_to = "valor")
        return(df_largo)
      }
      
      return(df)
    } else {
      stop("Por favor, sube un archivo de Excel (.xlsx)")
    }
  })
  
  output$var_select_ui <- renderUI({
    req(datos())
    df <- datos()
    tagList(
      selectInput("grupo_var", "Selecciona la variable de Grupos:", choices = names(df)),
      selectInput("valor_var", "Selecciona la variable de Valores:", choices = names(df))
    )
  })
  
  output$group_filter_ui <- renderUI({
    req(datos(), input$grupo_var)
    df <- datos()
    grupos_disponibles <- unique(df[[input$grupo_var]])
    
    if (input$test_type == "anova" && length(grupos_disponibles) >= 3) {
      checkboxGroupInput("grupos_seleccionados", "Selecciona los grupos a comparar:", 
                         choices = grupos_disponibles,
                         selected = grupos_disponibles)
    }
  })
  
  datos_filtrados <- reactive({
    req(input$grupo_var, input$valor_var)
    df <- datos()
    
    if (input$test_type == "anova" && !is.null(input$grupos_seleccionados)) {
      df <- df[df[[input$grupo_var]] %in% input$grupos_seleccionados, ]
    }
    df
  })
  
  resultado <- eventReactive(input$run_test, {
    req(input$grupo_var, input$valor_var)
    df <- datos_filtrados()
    grupo <- as.factor(df[[input$grupo_var]])
    valores <- as.numeric(df[[input$valor_var]])
    
    if (input$test_type == "ttest") {
      if (length(unique(grupo)) != 2) {
        return("Aviso: La prueba t requiere exactamente 2 grupos.")
      }
      t.test(valores ~ grupo, data = df, var.equal = TRUE)
      
    } else {
      if (length(unique(grupo)) < 3) {
        return("Aviso: La prueba ANOVA requiere 3 o más grupos.")
      }
      modelo <- aov(valores ~ grupo, data = df)
      resumen <- summary(modelo)
      tukey <- TukeyHSD(modelo)
      list(anova = resumen, tukey = tukey)
    }
  })
  
  output$test_result <- renderPrint({
    res <- resultado()
    if (is.character(res)) {
      cat(res)
    } else if (input$test_type == "ttest") {
      print(res)
    } else {
      print(res$anova)
      cat("\n--- Prueba de Tukey ---\n")
      print(res$tukey)
    }
  })
  
  output$plot_result <- renderPlot({
    req(input$grupo_var, input$valor_var)
    df <- datos_filtrados()
    
    if (input$test_type == "ttest" && length(unique(df[[input$grupo_var]])) != 2) return()
    if (input$test_type == "anova" && length(unique(df[[input$grupo_var]])) < 3) return()
    
    if (input$test_type == "ttest") {
      if (input$plot_type == "boxplot") {
        ggplot(df, aes_string(x = input$grupo_var, y = input$valor_var, fill = input$grupo_var)) +
          geom_boxplot() +
          theme_minimal() +
          labs(title = "Gráfico de Caja", x = "Grupo", y = "Valor")
      } else if (input$plot_type == "bar_error") {
        ggplot(df, aes_string(x = input$grupo_var, y = input$valor_var)) +
          stat_summary(fun = mean, geom = "bar", fill = "lightblue", color = "black") +
          stat_summary(fun.data = mean_se, geom = "errorbar", width = 0.2) +
          labs(title = "Barras con Error Estándar", x = "Grupo", y = "Valor") +
          theme_minimal()
      }
    } else {
      if (input$plot_type == "boxplot") {
        ggplot(df, aes_string(x = input$grupo_var, y = input$valor_var, fill = input$grupo_var)) +
          geom_boxplot() +
          theme_minimal() +
          labs(title = "Gráfico de Caja", x = "Grupo", y = "Valor")
      } else if (input$plot_type == "bar_error") {
        ggplot(df, aes_string(x = input$grupo_var, y = input$valor_var)) +
          stat_summary(fun = mean, geom = "bar", fill = "lightblue", color = "black") +
          stat_summary(fun.data = mean_se, geom = "errorbar", width = 0.2) +
          labs(title = "Barras con Error Estándar", x = "Grupo", y = "Valor") +
          theme_minimal()
      } else if (input$plot_type == "dotplot") {
        ggplot(df, aes_string(x = input$valor_var, y = input$grupo_var)) +
          geom_jitter(width = 0.2, height = 0.1) +
          labs(title = "Gráfico de Puntos Dispersos", x = "Valor", y = "Grupo") +
          theme_minimal()
      } else if (input$plot_type == "violin_plot") {
        ggplot(df, aes_string(x = input$grupo_var, y = input$valor_var, fill = input$grupo_var)) +
          geom_violin() +
          theme_minimal() +
          labs(title = "Violin Plot", x = "Grupo", y = "Valor")
      } else if (input$plot_type == "histogram") {
        ggplot(df, aes_string(x = input$valor_var, fill = input$grupo_var)) +
          geom_histogram(position = "dodge", bins = 30) +
          facet_wrap(as.formula(paste("~", input$grupo_var))) +
          labs(title = "Histogramas por Grupo", x = "Valor", y = "Frecuencia") +
          theme_minimal()
      }
    }
  })
}
shinyApp(ui = ui, server = server)
