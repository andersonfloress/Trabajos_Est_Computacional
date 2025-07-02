from flask import Flask, render_template, request, redirect, url_for, session, flash
import random
from collections import Counter

app = Flask(__name__)
app.secret_key = 'clave-secreta-para-sesiones'

DULCES = ['limon', 'pera', 'huevo']

# Función para validar combinaciones permitidas
def valida_combinacion(dulces_totales, cantidad):
    c = dulces_totales
    if cantidad == 3:
        # 1 de cada tipo
        return all(c[d] >= 1 for d in DULCES)
    elif cantidad == 4:
        # 2 pares iguales (ej: 2 limon + 2 pera)
        pares = [c[d] // 2 for d in DULCES]
        return sum(pares) >= 2
    elif cantidad == 6:
        # 2 de cada tipo
        return all(c[d] >= 2 for d in DULCES)
    elif cantidad == 9:
        # 3 de cada tipo
        return all(c[d] >= 3 for d in DULCES)
    else:
        # Para otros casos, solo checamos que haya suficientes dulces en total
        return sum(c.values()) >= cantidad

# Página inicial y manejo de todo el juego
@app.route('/', methods=['GET', 'POST'])
def index():
    mensaje = None
    
    if request.method == 'POST':
        accion = request.form.get('accion')
        if accion == 'reiniciar_juego':
            session.clear()
            return redirect(url_for('index'))

        # Primera configuración del juego
        if not accion:
            try:
                num = int(request.form['participantes'])
                dulces_para_cambiar = int(request.form['dulces_para_cambiar'])
                dulces_extra = int(request.form['dulces_extra'])
                dulces_recibidos = int(request.form['dulces_recibidos'])

                participantes = []
                dulces_totales = Counter()

                # Dar 2 dulces aleatorios a cada participante
                for _ in range(num):
                    dulces = random.choices(DULCES, k=2)
                    participantes.append(dulces)
                    dulces_totales.update(dulces)

                # Guardamos datos en sesión
                session['num'] = num
                session['dulces_para_cambiar'] = dulces_para_cambiar
                session['dulces_extra'] = dulces_extra
                session['dulces_recibidos'] = dulces_recibidos
                session['participantes'] = participantes
                session['dulces_totales'] = dict(dulces_totales)
                session['chupetines'] = 0
                session['cambios_dulces_a_chupetin'] = 0
                session['cambios_chupetin_a_dulces'] = 0

            except Exception as e:
                flash(f"Error: {e}")
                return redirect(url_for('index'))
        
        # Cambios de dulces
        else:
            num = session.get('num', 0)
            dulces_para_cambiar = session.get('dulces_para_cambiar', 0)
            dulces_extra = session.get('dulces_extra', 0)
            dulces_recibidos = session.get('dulces_recibidos', 0)
            participantes = session.get('participantes', [])
            dulces_totales = Counter(session.get('dulces_totales', {}))
            chupetines = session.get('chupetines', 0)
            cambios_dulces_a_chupetin = session.get('cambios_dulces_a_chupetin', 0)
            cambios_chupetin_a_dulces = session.get('cambios_chupetin_a_dulces', 0)

            if accion == 'cambiar_dulces_a_chupetin':
                # Usuario debe elegir dulces exactos dulces_para_cambiar
                dulces_elegidos = []
                for d in DULCES:
                    cantidad = int(request.form.get(f'dulce_{d}', 0))
                    dulces_elegidos.extend([d]*cantidad)

                extra_elegidos = []
                for d in DULCES:
                    cantidad = int(request.form.get(f'extra_{d}', 0))
                    extra_elegidos.extend([d]*cantidad)

                if len(dulces_elegidos) != dulces_para_cambiar:
                    mensaje = f"Debes elegir exactamente {dulces_para_cambiar} dulces para cambiar por un chupetín."
                elif len(extra_elegidos) != dulces_extra:
                    mensaje = f"Debes elegir exactamente {dulces_extra} dulces extra."
                else:
                    contador_elegidos = Counter(dulces_elegidos)
                    if not valida_combinacion(contador_elegidos, dulces_para_cambiar):
                        if dulces_para_cambiar == 3:
                            mensaje = "Para 3 dulces debe ser: 1 de cada tipo (1 limón + 1 pera + 1 huevo)."
                        elif dulces_para_cambiar == 4:
                            mensaje = "Para 4 dulces debe ser: 2 pares iguales (ej: 2 limón + 2 pera)."
                        elif dulces_para_cambiar == 6:
                            mensaje = "Para 6 dulces debe ser: 2 de cada tipo (2 limón + 2 pera + 2 huevo)."
                        elif dulces_para_cambiar == 9:
                            mensaje = "Para 9 dulces debe ser: 3 de cada tipo (3 limón + 3 pera + 3 huevo)."
                        else:
                            mensaje = "Combinación inválida. Revisa las reglas."
                    else:
                        disponibles = True
                        for d in DULCES:
                            if dulces_elegidos.count(d) > dulces_totales.get(d, 0):
                                disponibles = False
                                break

                        if not disponibles:
                            mensaje = "No tienes suficientes dulces para esa combinación."
                        else:
                            for d in dulces_elegidos:
                                dulces_totales[d] -= 1
                            for d in extra_elegidos:
                                dulces_totales[d] += 1
                            chupetines += 1
                            cambios_dulces_a_chupetin += 1


            elif accion == 'cambiar_chupetin_a_dulces':
                if chupetines == 0:
                    mensaje = "No tienes chupetines para cambiar."
                else:
                    # Usuario debe elegir dulces para recibir exactamente dulces_recibidos
                    dulces_elegidos = []
                    for d in DULCES:
                        cantidad = int(request.form.get(f'dulce_{d}', 0))
                        dulces_elegidos.extend([d]*cantidad)

                    if len(dulces_elegidos) != dulces_recibidos:
                        mensaje = f"Debes elegir exactamente {dulces_recibidos} dulces al cambiar un chupetín."
                    else:
                        chupetines -= 1
                        cambios_chupetin_a_dulces += 1
                        # Agregar los dulces elegidos
                        for d in dulces_elegidos:
                            dulces_totales[d] += 1

            # Guardamos todo actualizado en sesión
            session['dulces_totales'] = dict(dulces_totales)
            session['chupetines'] = chupetines
            session['cambios_dulces_a_chupetin'] = cambios_dulces_a_chupetin
            session['cambios_chupetin_a_dulces'] = cambios_chupetin_a_dulces

    # Obtener datos para mostrar solo si hay juego iniciado
    num = session.get('num')
    
    if num:
        participantes = session.get('participantes', [])
        dulces_totales = Counter(session.get('dulces_totales', {}))
        chupetines = session.get('chupetines', 0)
        cambios_dulces_a_chupetin = session.get('cambios_dulces_a_chupetin', 0)
        cambios_chupetin_a_dulces = session.get('cambios_chupetin_a_dulces', 0)
        dulces_para_cambiar = session.get('dulces_para_cambiar', 6)
        dulces_extra = session.get('dulces_extra', 2)
        dulces_recibidos = session.get('dulces_recibidos', 6)

        # Validar combinaciones
        cantidad_dulces = sum(dulces_totales.values())
        if not valida_combinacion(dulces_totales, cantidad_dulces):
            mensaje = "La combinación actual de dulces no cumple las reglas permitidas."

        salvados = chupetines >= num

        return render_template('index.html',
                               num=num,
                               participantes=participantes,
                               dulces_totales=dulces_totales,
                               chupetines=chupetines,
                               cambios_dulces_a_chupetin=cambios_dulces_a_chupetin,
                               cambios_chupetin_a_dulces=cambios_chupetin_a_dulces,
                               dulces_para_cambiar=dulces_para_cambiar,
                               dulces_extra=dulces_extra,
                               dulces_recibidos=dulces_recibidos,
                               mensaje=mensaje,
                               salvados=salvados,
                               DULCES=DULCES)
    else:
        # No hay juego iniciado, solo mostrar formulario inicial
        return render_template('index.html', num=None)

if __name__ == '__main__':
    app.run(debug=True)