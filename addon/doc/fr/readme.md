# WordNav #

* Auteur : Tony Malykh
* Télécharger [version stable][1]
* Compatibilité NVDA : 2019.3 et ultérieurs

L'extension WordNav pour NVDA améliore la navigation intégrée par mot, et
ajoute des commandes de navigation de mot supplémentaires avec une
définition différente pour le mot. Elle fournit également des commandes de
sélection de mots.

La plupart des éditeurs de texte prennent en charge les commandes
Contrôle+FlècheGauche/FlècheDroite pour la navigation dans les
mots. Cependant la définition du mot change d'un programme à l'autre. Cela
est particulièrement vrai des éditeurs de texte modernes basés sur le Web,
tels que Monaco. NVDA doit connaître la définition du mot dans un programme
donné afin de prononcer les mots correctement. Si NVDA ne connaît pas la
définition exacte, alors les mots seront ignorés ou prononcés plusieurs
fois. De plus, certains éditeurs de texte basés sur le Web positionnent le
curseur à la fin du mot, au lieu du début, ce qui rend l'édition beaucoup
plus difficile pour les utilisateurs malvoyants. Afin de lutter contre ce
problème, j'ai créé des commandes de navigation de mots améliorées, qui
prennent la définition de mot de Notepad ++ et ne reposent pas sur la
définition des mots du programme, mais analysent plutôt les lignes en mots
du côté de NVDA. Le geste Contrôle+FlècheGauche/FlècheDroite n'est même pas
envoyé au programme, assurant ainsi la cohérence du discours.

## Navigation dans les mots et définitions de mots

Actuellement, WordNav prend en charge cinq définitions du mot, attribuées à
différents gestes :

* « Contrôle gauche + flèches » : définition de Notepad++, qui traite les
  caractères alphanumériques comme des mots, et les signes de ponctuation
  adjacents sont également traités comme des mots. Cela devrait être la
  définition de mot la plus pratique pour la majorité des utilisateurs.
* `ContrôleDroit+Flèches` : la définition fine des mots divise
  `identifiantsCamelCase` et `identifiants_séparés_par_souligné` en parties
  séparées, permettant ainsi au curseur d'entrer dans de longs identifiants.
* `ContrôleGauche+Windows+Flèches` : la définition de mots volumineux traite
  presque tous les symboles de ponctuation adjacents au texte comme faisant
  partie d'un seul mot. Par conséquent, les chemins tels que
  « C:\répertoire\sous-répertoire\fichier.txt » seraient traités comme un
  seul mot.
* `ContrôleDroit+Windows+Flèches` : définition de plusieurs mots, qui
  regroupe plusieurs mots. Le nombre de mots est configurable.
* Non attribué : définition de mot d'expression régulière personnalisée :
  permet à l'utilisateur de définir une expression régulière personnalisée
  pour les limites des mots.

Les gestes peuvent être personnalisés dans le panneau des paramètres de
WordNav.

## Sélection de mots

La sélection de mots est prise en charge à partir de WordNav v2.0. Ajoutez
simplement le modificateur `maj` à n'importe quel geste de navigation de
mots pour sélectionner des mots. Il existe également un geste supplémentaire
pour la sélection des mots :

* `contrôle+maj+pavnum1` et `contrôle+windows+maj+pavnum1` sélectionnent le
  mot à droite de la même manière que leurs homologues `flèche droite`, mais
  ils incluent également des espaces de fin dans la sélection.

Veuillez noter cependant que les API d'accessibilité actuellement utilisées
présentent de nombreux problèmes liés à la sélection des mots. Veuillez vous
familiariser avec la liste suivante de problèmes et de solutions :

* Les applications UIA (par exemple Notepad, Visual Studio, Microsoft Word)
  ne prennent pas en charge la définition du curseur au début de la
  sélection. Dans ces applications, l'emplacement du curseur est stocké du
  côté de WordNav. Comme effet secondaire indésirable, les commandes de
  navigation dans les mots peuvent ne pas fonctionner correctement avec les
  commandes de sélection de lignes et de paragraphes (`maj+flèche haut/bas`,
  `contrôle+maj+flèche haut/bas`) et les résultats peuvent être
  imprévisibles. Pour plus de commodité, les commandes de sélection de
  caractères (`maj+flèche gauche/droite`) ont été mises à jour dans WordNav
  pour les applications UIA et devraient bien fonctionner.
* Les contrôles d'édition Windows de base sur une seule ligne ne permettent
  pas non plus de placer le curseur devant la sélection, donc le point
  précédent s'applique également à eux. Cela affecte toutes les zones
  d'édition sur une seule ligne dans NVDA.
* IAccessible2 ne permet pas de définir une sélection s'étendant sur
  plusieurs paragraphes. Il n’existe aucune solution de contournement connue
  pour ce problème. Cela affecte les zones d'édition multilignes riches dans
  Chrome et Firefox, telles que la zone de texte de rédaction d'e-mail dans
  GMail et la fenêtre de rédaction d'e-mail dans Thunderbird.
* Dans Notepad ++, les messages de mise à jour de la sélection sont
  déraisonnablement lents. Pour contourner le problème, WordNav annonce la
  sélection côté NVDA pour les commandes de sélection de mots et fait taire
  les notifications tardives pendant les 0,5 secondes suivantes. Par
  conséquent, si vous appuyez rapidement sur la commande de sélection de mot
  suivie d'une autre commande de sélection (par exemple un caractère), vous
  risquez de manquer la notification de sélection pour cette dernière si
  elle intervient dans les 0,5 secondes suivant la dernière commande de
  sélection de mot.
* Dans les zones d'édition multilignes prenant en charge l'interface TOM,
  NVDA identifie incorrectement l'emplacement du curseur lorsque la
  sélection est présente. Ce problème a été corrigé dans
  nvaccess/nvda#16455, qui devrait être inclus dans la version NVDA
  v2024.2. Avant cette version, les commandes de sélection de mots ne
  fonctionneraient pas correctement dans les zones d'édition TOM, telles que
  la Visionneuse du journal de NVDA.

## Notes

* Si vous souhaitez utiliser la fonctionnalité de bureaux virtuels de
  Windows 10, n'oubliez pas de désactiver les raccourcis clavier
  Ctrl+Windows+Flèches soit dans le panneau Paramètres WordNav, soit dans le
  dialogue Gestes dde commande de NVDA.
* La compatibilité avec VSCode nécessite l'installation de l'extension NVDA
  IndentNav v2.0 ou version ultérieure. De plus, l'extension VSCode
  [Accessibilité pour NVDA
  IndentNav](https://marketplace.visualstudio.com/items?itemName=TonyMalykh.nvda-indent-nav-accessibility)
  doit être installée dans VSCode.

##  Téléchargements

Veuillez installer la dernière version depuis l'add-on store.

[[!tag dev stable]]

[1]: https://www.nvaccess.org/addonStore/legacy?file=wordnav
