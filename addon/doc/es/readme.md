# WordNav #

* Autor: Tony Malykh
* Descargar [versión estable][1]
* Compatibilidad con NVDA: 2019.3 y posterior

El complemento WordNav para NVDA mejora la navegación por palabras integrada
y añade órdenes extra de navegación con diferentes definiciones de lo que es
una palabra. También proporciona órdenes de selección de palabras.

La mayoría de editores de texto soportan las órdenes control+flechas
izquierda y derecha para navegar por palabras. Sin embargo, la definición de
palabra cambia de un programa a otro. Esto es especialmente cierto en los
editores de texto modernos basados en web, tales como Monaco. NVDA debería
saber la definición de palabra en un programa dado para verbalizar las
palabras correctamente. Si NVDA no conoce la definición exacta, las palabras
se saltan o se pronuncian varias veces. Por si fuera poco, algunos editores
basados en web sitúan el cursor al final de la palabra en lugar del
principio, dificultando la edición a personas con discapacidad visual. Para
combatir este problema, he creado órdenes de navegación por palabra
mejoradas, que toman la definición de palabra de Notepad++ y no se apoyan en
la definición de palabra de otros programas, y que en su lugar descomponen
las líneas en palabras dentro del propio NVDA. El gesto control+flecha
izquierda o flecha derecha ni siquiera se envía al programa, garantizando
por tanto la consistencia del habla.

## Navegación por palabras y definiciones de palabra

Actualmente, WordNav soporta cinco definiciones de palabra, asignadas a
diferentes gestos:

* `Control izquierdo+flechas`: definición de Notepad++, que trata los
  caracteres alfanuméricos como palabras, y también trata como palabras las
  marcas de puntuación adyacentes. Esta debería ser la definición de palabra
  más conveniente para la mayoría de usuarios.
* `Control derecho+flechas`: definición de palabra Fine, que divide los
  `identificadoresCamelCase` y los
  `identificadores_separados_por_subrayados` en partes independientes,
  permitiendo que el cursor se desplace por identificadores largos.
* `Control izquierdo+Windows+flechas`: definición de palabra en lote, que
  trata casi todos los símbolos de puntuación adyacentes al texto como parte
  de una única palabra, por lo que trataría rutas como
  `C:\directorio\subdirectorio\archivo.txt` como una única palabra.
* `Control derecho+Windows+flechas`: definición multipalabra, que agrupa
  varias palabras juntas. El número de palabras es configurable.
* Sin asignar: definición de palabra con expresión regular personalizada:
  permite al usuario definir una expresión regular personalizada para los
  límites de una palabra.

Se pueden personalizar todos estos gestos en el panel de opciones de
WordNav.

## Selección de palabras

Se soporta la selección de palabras a partir de WordNav 2.0. Simplemente
añade el modificador `shift` a cualquier gesto de navegación por palabras
para seleccionarlas. También hay un gesto extra para seleccionar palabras:

* `Control+shift+1 numérico` y `control+shift+windows+1 numérico`
  seleccionan palabras a la derecha, de forma similar a sus homólogos con
  `flecha derecha`, pero también incluyen espacios finales en la selección.

Ten en cuenta, sin embargo, que las APIs de accesibilidad usadas en la
actualidad tienen varios fallos relativos a la selección de
palabras. Familiarízate con la siguiente lista de problemas y soluciones
alternativas:

* Las aplicaciones UIA (por ejemplo el bloc de notas, Visual Studio o
  Microsoft Word) no soportan situar el cursor al principio de la
  selección. En estas aplicaciones, el cursor se almacena del lado de
  WordNav. Como efecto colateral adverso, las órdenes de navegación por
  palabras podrían no llevarse bien con las órdenes de selección de párrafos
  y líneas (`shift+flechas arriba o abajo`, `control+shift+flechas arriba o
  abajo`) y los resultados podrían ser impredecibles. Por conveniencia, las
  órdenes de selección por caracteres (`shift+flechas izquierda y derecha`)
  se han actualizado en WordNav para las aplicaciones UIA y deberían
  funcionar bien.
* Los cuadros de edición básicos de Windows de una sola línea tampoco
  permiten situar el cursor delante de la selección, por lo que el punto
  anterior también se les aplica. Esto afecta a todos los cuadros de edición
  de una sola línea que hay dentro de NVDA.
* IAccessible2 no proporciona una forma de selección que abarque varios
  párrafos. No hay solución conocida para este problema. Esto afecta a
  cuadros de edición enriquecida en Chrome y Firefox, como el área de texto
  de redacción en GMail y la ventana de redacción de correo en Thunderbird.
* En Notepad++,los mensajes de actualización de selección llegan
  inexplicablemente lentos. Como solución alternativa, WordNav anuncia la
  selección del lado de NVDA con las órdenes de selección de palabras y
  silencia notificaciones posteriores durante los siguientes 0,5
  segundos. Como resultado, si se pulsa una orden de selección de palabra
  seguida de otra orden de selección (por ejemplo, por caracteres) en
  sucesión rápida, se podría perder la notificación de selección de la
  última orden si se pulsó menos de medio segundo después de la orden de
  selección de palabra.
* En cuadros de edición multilínea que soporten interfaces TOM, NVDA
  identifica incorrectamente la posición del cursor cuando la selección está
  presente. Esto se ha corregido en nvaccess/nvda#16455, cuya inclusión está
  prevista en la versión 2024.2 de NVDA. Antes de dicha versión, las órdenes
  de selección de palabras no funcionarán correctamente en cuadros de
  edición TOM, tales como el visualizador de registro de NVDA.

## Notas

* Si quieres utilizar la función de escritorios virtuales de Windows 10,
  recuerda desactivar los atajos de teclado control+windows+flechas desde el
  panel de opciones de WordNav, o bien en el diálogo Gestos de entrada de
  NVDA.
* La compatibilidad con VSCode requiere que el complemento IndentNav 2.0 o
  una versión posterior esté instalado. Además, la extensión para VSCode
  [Accesibilidad para NVDA
  IndentNav](https://marketplace.visualstudio.com/items?itemName=TonyMalykh.nvda-indent-nav-accessibility)
  debe estar instalada en VSCode.

##  Descargas

Por favor, instala la versión más reciente desde la tienda de complementos
de NVDA.

[[!tag dev stable]]

[1]: https://www.nvaccess.org/addonStore/legacy?file=wordnav
