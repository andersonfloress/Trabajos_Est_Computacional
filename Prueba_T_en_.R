#CARGANDO DATOS
datos <- read.table("puntajes.txt", header = TRUE, sep = ",")

head(datos, 26)
# Coeficiente de variacion
cv_electronica <- (sd(datos$electronica) / mean(datos$electronica)) * 100
cv_mecanica <- (sd(datos$mecanica_electrica) / mean(datos$mecanica_electrica)) * 100

cv_electronica
cv_mecanica
# Varianzas
var_electronica <- var(datos$electronica)
var_mecanica <- var(datos$mecanica_electrica)

var_electronica
var_mecanica

t.test(datos$electronica, datos$mecanica_electrica, var.equal = FALSE)

Puntajes <- c(datos$electronica, datos$mecanica_electrica)
Carrera <- c(rep("Electrónica", length(datos$electronica)),
             rep("Mecánica Eléctrica", length(datos$mecanica_electrica)))

boxplot(Puntajes ~ Carrera,
        main = "Comparación de Puntajes por Carrera",
        xlab = "Carrera", ylab = "Puntaje",
        col = c("skyblue", "lightgreen"))
