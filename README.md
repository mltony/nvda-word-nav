# nvda-word-nav
WordNav NVDA add-on improves built-in navigation  by word, as well as adds extra word navigation commands with different definition for the word.

Most text editors support Control+LeftArrow/RightArrow commands for word navigation. However the definition of the word changes from one program to another. This is especially true of modern web-based text editors, such as Monaco. NVDA should know the definition of word in given program in order to speak words correctly. If NVDA doesn't know the exact definition, then either words are going to be skipped, or pronounced multiple times. Moreover, some web-based text editors position the cursor in the end of the word, instead of the beginning, making editing much harder for visually impaired users. In order to combat this problem I have created enhanced word navigation commands, that take the word definition from Notepad++ and they do not rely on program's definition of words, but rather parse lines into words on NVDA's side. The Control+LeftArrow/RightArrow gesture is not even sent to the program, thus ensuring the consistency of the speech.

Please note that a prototype of WordNav was formerly a part of [Tony's enhancements](https://github.com/mltony/nvda-tonys-enhancements/) add-on. Please either uninstall it or upgrade to [Tony's enhancements latest stable version](https://github.com/mltony/nvda-tonys-enhancements/releases/latest/download/tonysEnhancements.nvda-addon) to avoid conflicts.

Currently WordNav supports four definitions of the word, assigned to different gestures:

- `Left Control+Arrows`: Notepad++ definition, that treats alphanumeric characters as words, and adjacent punctuation marks are also treated as words. This should be the most convenient word definition for the majority of users.
- `RightControl+Arrows`: Fine word definition splits `camelCaseIdentifiers` and `underscore_separated_identifiers` into separate parts, thus allowing the cursor to go into long identifiers.
- `LeftControl+Windows+Arros`: Bulky word definition treats almost all punctuation symbols adjacent to text as part of a single word, therefore it would treat paths like `C:\directory\subdirectory\file.txt` as a single word.
- `RightControl+Windows+Arros`: Multiword definition, that groups several words together. The amount of words is configurable.

Gestures can be customized in WordNav settings panel.

## Notes

- At this time WordNav doesn't modify `Control+Shift+LeftArrow/RightArrow` gestures to select words, since implementation of such commands are significantly more complicated.
- If you would like to use virtual desktops feature of Windows 10, please remember to disable Control+Windows+Arrows keyboard shortcuts either in WordNav Settings panel, or in NVDA Input gestures dialog.
- WordNav doesn't work reliably in VSCode, since due to its internal optimizations, VSCode presents only a few lines of file contents at a time, that change dynamically, and this occasionally interferes with WordNav algorithm.


##  Downloads

[WordNav latest stable version](https://github.com/mltony/nvda-word-nav/releases/latest/download/wordNav.nvda-addon)