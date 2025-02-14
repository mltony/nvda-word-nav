# WordNav #

* Autor: Tony Malykh
* Download [versão estável][1]
* Compatibilidade com NVDA: 2019.3 e posterior

O complemento WordNav NVDA aprimora a navegação integrada por palavra, além
de adicionar comandos extras de navegação por palavra com definições
diferentes para a palavra. Ele também fornece comandos de seleção de
palavras.

A maioria dos editores de texto suporta os comandos Control+Seta para a
esquerda/Seta para a direita para a navegação de palavras. Entretanto, a
definição da palavra muda de um programa para outro. Isso é especialmente
verdadeiro em editores de texto modernos baseados na Web, como o Monaco. O
NVDA deve conhecer a definição da palavra em um determinado programa para
falar as palavras corretamente. Se o NVDA não souber a definição exata, as
palavras serão ignoradas ou pronunciadas várias vezes. Além disso, alguns
editores de texto baseados na Web posicionam o cursor no final da palavra,
em vez de no início, tornando a edição muito mais difícil para os usuários
com deficiência visual. Para combater esse problema, criei comandos
aprimorados de navegação de palavras, que usam a definição de palavras do
Notepad++ e não dependem da definição de palavras do programa, mas analisam
as linhas em palavras no lado do NVDA. O gesto de Control+Seta para a
esquerda/Seta para a direita nem sequer é enviado ao programa, garantindo
assim a consistência da fala.

## Navegação e definições de palavras

Atualmente, o WordNav suporta cinco definições da palavra, atribuídas a
diferentes gestos:

* `Control esquerdo+Setas`: Definição do Notepad++ que trata os caracteres
  alfanuméricos como palavras, e os sinais de pontuação adjacentes também
  são tratados como palavras. Essa deve ser a definição de palavra mais
  conveniente para a maioria dos usuários.
* `Control direito+Setas`: A definição de palavras finas divide
  `camelCaseIdentifiers` e `sublinhado identificadores_separados` em partes
  separadas, permitindo assim que o cursor vá para identificadores longos.
* `Control esquerdo+Windows+Arros`: A definição de palavra volumosa trata
  quase todos os símbolos de pontuação adjacentes ao texto como parte de uma
  única palavra, portanto, trataria caminhos como
  `C:\directory\subdirectory\file.txt` como uma única palavra.
* `ControlDireita+Windows+setas`: Define um grupo de palavras, cuja
  quantidade é configurável.
* Não atribuído: expressão regular personalizada definição de palavra:
  permite que o usuário defina uma expressão regular personalizada para
  limites de palavras.

Os gestos podem ser personalizados no painel de configurações do WordNav.

## Seleção de palavras

A seleção de palavras é suportada a partir do WordNav v2.0. Basta adicionar
o modificador `shift` a qualquer gesto de navegação de palavras para
selecionar palavras. Há também um gesto extra para a seleção de palavras:

* Os comandos `control+shift+numpad1` e `control+windows+shift+numpad1`
  selecionam a palavra à direita de forma semelhante às suas contrapartes
  `setaDireita`, mas também incluem espaços finais na seleção.

Note, no entanto, que as APIs de acessibilidade usadas atualmente têm vários
problemas relacionados à seleção de palavras. Familiarize-se com a seguinte
lista de problemas e soluções alternativas:

* Os aplicativos UIA (por exemplo, Notepad, Visual Studio, Microsoft Word)
  não suportam a definição do cursor no início da seleção. Nesses
  aplicativos, o local do cursor é armazenado no WordNav. Como efeito
  colateral adverso, os comandos de navegação de palavras podem não
  funcionar bem com os comandos de seleção de linhas e parágrafos
  (`shift+seta para cima/seta para baixo`, `controle+shift+seta para
  cima/seta para baixo`) e os resultados podem ser imprevisíveis. Por
  conveniência, os comandos de seleção de caracteres (`shift+seta
  esquerda/seta direita`) foram atualizados no WordNav para aplicativos UIA
  e devem funcionar bem.
* Os controles básicos de edição de linha única do Windows também não
  permitem definir o cursor na frente da seleção, portanto, o ponto anterior
  também se aplica a eles. Isso afeta todas as caixas de edição de linha
  única no NVDA.
* O IAccessible2 não oferece uma maneira de definir a abrangência da seleção
  em vários parágrafos. Não há nenhuma solução alternativa conhecida para
  esse problema. Isso afeta as caixas de edição ricas em várias linhas no
  Chrome e no Firefox, como a área de texto de composição de e-mail no GMail
  e a janela de composição de e-mail no Thunderbird.
* No Notepad++, as mensagens de atualização de seleção são excessivamente
  lentas. Como solução alternativa, o WordNav anuncia a seleção no lado do
  NVDA para comandos de seleção de palavras e silencia as notificações
  tardias durante os 0,5 segundos seguintes. Como resultado, se você
  pressionar o comando de seleção de palavra seguido por outro comando de
  seleção (por exemplo, caractere) em rápida sucessão, poderá perder a
  notificação de seleção para o último comando, se ele tiver chegado a 0,5
  segundos do último comando de seleção de palavra.
* Nas caixas de edição de várias linhas que suportam a interface TOM, o NVDA
  identifica incorretamente a localização do cursor quando há seleção. Isso
  foi corrigido em nvaccess/nvda#16455, que está programado para ser
  incluído na versão v2024.2 do NVDA. Antes dessa versão, os comandos de
  seleção de palavras não funcionarão corretamente nas caixas de edição TOM,
  como o visualizador de registros do NVDA.

## Notas

* Se você quiser usar o recurso de áreas de trabalho virtuais do Windows 10,
  lembre-se de desativar os atalhos de teclado Control+Windows+Setas no
  painel Configurações do WordNav ou na caixa de diálogo Gestos de entrada
  do NVDA.
* A compatibilidade com o VSCode requer a instalação do complemento
  IndentNav v2.0 ou posterior do NVDA. Além disso, a extensão VSCode
  [Accessibility for NVDA IndentNav]
  (https://marketplace.visualstudio.com/items?itemName=TonyMalykh.nvda-indent-nav-accessibility)
  deve ser instalada no VSCode.

##  Downloads

Instale a versão mais recente da loja de complementos do NVDA.

[[!tag dev stable]]

[1]: https://www.nvaccess.org/addonStore/legacy?file=wordnav
