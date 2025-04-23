# Generador base
lcg_core <- function(n, seed, a, c, m) {
  x <- numeric(n)
  x[1] <- seed %% m
  for (i in 2:n) {
    x[i] <- (a * x[i - 1] + c) %% m
  }
  return(x)
}

# N. reales aleatorios
lcg_real <- function(n, min_val = 0, max_val = 1,
                     seed = as.integer(Sys.time()),
                     a = 1664525, c = 1013904223, m = 2^32) {
  raw <- lcg_core(n, seed, a, c, m)
  return(min_val + (raw / m) * (max_val - min_val))
}

# N. enteros aleatorios
lcg_int <- function(n, min_val = 0, max_val = 20,
                    seed = as.integer(Sys.time()),
                    a = 1664525, c = 1013904223, m = 2^32) {
  raw <- lcg_core(n, seed, a, c, m)
  scaled <- min_val + (raw / m) * (max_val - min_val + 1)
  result <- floor(scaled)
  return(pmin(result, max_val))
}

#=====COMPARACIONES=====
# Generar valores con LCG
seed <- 42
n <- 1000
valores_lcg <- lcg_real(n, 0, 1, seed = seed)

set.seed(seed)
valores_r <- runif(n)

# Comparacion visual
par(mfrow = c(1, 2))
hist(valores_r, breaks = 30, col = "lightblue", main = "Generador Nativo de R (runif)", xlab = "Valor")
hist(valores_lcg, breaks = 30, col = "lightgreen", main = "Generador LCG", xlab = "Valor")

# Comparaciones estadisticas
cat("\n--- Comparación con Generador Nativo de R ---\n")
cat("Media (R nativo):", mean(valores_r), "\n")
cat("Media (LCG):", mean(valores_lcg), "\n")
cat("Varianza (R nativo):", var(valores_r), "\n")
cat("Varianza (LCG):", var(valores_lcg), "\n")
cat("Desviación estándar (R nativo):", sd(valores_r), "\n")
cat("Desviación estándar (LCG):", sd(valores_lcg), "\n")
cat("Mínimo (R nativo):", min(valores_r), "\n")
cat("Mínimo (LCG):", min(valores_lcg), "\n")
cat("Máximo (R nativo):", max(valores_r), "\n")
cat("Máximo (LCG):", max(valores_lcg), "\n")
cat("Rango (R nativo):", range(valores_r), "\n")
cat("Rango (LCG):", range(valores_lcg), "\n")

cat("\n--- Comparación: lcg_int vs sample() ---\n")
set.seed(42)
valores_r_int <- sample(1:6, 1000, replace = TRUE)
valores_lcg_int <- lcg_int(1000, 1, 6, seed = 42)

cat("Media (R nativo):", mean(valores_r_int), "\n")
cat("Media (LCG):", mean(valores_lcg_int), "\n")
cat("Varianza (R nativo):", var(valores_r_int), "\n")
cat("Varianza (LCG):", var(valores_lcg_int), "\n")
cat("Desviación estándar (R nativo):", sd(valores_r_int), "\n")
cat("Desviación estándar (LCG):", sd(valores_lcg_int), "\n")
cat("Mínimo (R nativo):", min(valores_r_int), "\n")
cat("Mínimo (LCG):", min(valores_lcg_int), "\n")
cat("Máximo (R nativo):", max(valores_r_int), "\n")
cat("Máximo (LCG):", max(valores_lcg_int), "\n")
cat("Rango (R nativo):", range(valores_r_int), "\n")
cat("Rango (LCG):", range(valores_lcg_int), "\n")
