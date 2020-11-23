# nvda-word-nav
WordNav NVDA add-on improves built-in navigation  by word, as well as adds extra word navigation commands with different definition fo the word.

Most text editors support Control+LeftArrow/RightArrow commands for word navigation. However the definition of the word changes from one program to another. This is especially true of modern web-based text editors, such as Monaco. NVDA should know the definition of word in given program in order to speak words correctly. If NVDA doesn't know the exact definition, then either words are going to be skipped, or pronounced multiple times. Moreover, some web-based text editors position the cursor in the end of the word, instead of the beginning, making editing much harder for visually impaired users. In order to combat this problem I have created enhanced word navigation commands, that take the word definition from Notepad++ and they do not rely on program's definition of words, but rather parse lines into words on NVDA's side. The Control+LeftArrow/RightArrow gesture is not even sent to the program, thus ensuring the consistency of the speech.
* Control+LeftArrow/RightArrow - jump to previous/next word on the line
* Control+Windows+LeftArrow/RightArrow - jump to previous/next word on the line according to alternative word definition

Currently the drawback of this approach is that sometimes it is not able to advance to next/previous line in some text editors, such as VSCode, since due to its internal optimizations, VSCode presents only a few lines of file contents at a time.

## Alternative word definitions
Default word definition of WordNav comes from Notepad++.
However, sometimes it is desirable to jump into separate words of camelCaseIdentifiers or underscore_separated_identifiers. If you wish to do so, you should use command for fine word navigation.
At other times, you might want to consider for example a long file path as a single word so that you can jump over it with a single keystroke. In this case, use bulky word definition.

There are three availabel modifiers supported in this addon: LeftControl, RightControl and Control+Windows. You can assign different word definitions to these three modifiers in the settings dialog.

##  Downloads

[WordNav latest stable version](https://github.com/mltony/nvda-word-nav/releases/latest/download/wordNav.nvda-addon)