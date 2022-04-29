# NVDA 单词导航
NVDA 单词导航插件（WordNav）改进了内建的单词导航方式，同时还增加了一些额外的单词导航命令，这些命令采用了不同的单词定义。

大多数文本编辑器支持“Ctrl+左右箭头”命令来进行单词导航，但对于单词的定义在这些应用程序之间则存在差异，尤其是现在一些基于 web 的文本编辑器，如 Monaco。为了正确地朗读单词，NVDA 应当知道给定的应用程序中是如何定义单词的。如果 NVDA 不知道单词的确切定义，不仅给定的单词会被跳过，而且有可能将单词朗读数次。不仅如此，一些基于 web 的文本编辑器将光标置于单词的末尾而不是开头，这就使视障用户的编辑更加困难了。为了克服这些困难，我创建了一些用于单词导航的增强命令。这些命令引进了 Notepad++ 的单词定义，并且不依赖于编辑器程序对单词的定义，而是由 NVDA 将文本行解析为单词的。甚至“Ctrl+左右箭头”这样的手势也不会被发送到编辑器程序，这便确保了朗读的一致性。

请注意，单词导航的原型以前是[Tony 增强](https://github.com/mltony/nvda-tonys-enhancements/)插件的一部分。为避免冲突，请卸载它或升级至[Tony 增强最新稳定版](https://github.com/mltony/nvda-tonys-enhancements/releases/latest/download/tonysEnhancements.nvda-addon)。

目前，单词导航插件支持五种单词定义，并为它们分配了相应的手势：

- `左Ctrl+箭头`：Notepad++ 定义。它将字母、数字作为单词处理，同时把临近的标点符号也视为单词。对大多数用户而言，这应当是最便捷的单词定义了。
- `右Ctrl+箭头`：精细单词定义。它可以将“`camelCaseIdentifiers`”及“`underscore_separated_identifiers`”拆分成若干部分，从而允许光标进入这样的长标识符中，并在所拆分出的各部分之间移动。
- `左Ctrl+Windows+箭头`：大型单词定义。它将临近文本的几乎所有标点符号都作为一个单词的一部分，因此它会把像“`C:\directory\subdirectory\file.txt`”这样的路径作为一个大型单词处理。
-`右Ctrl+Windows+箭头`：多单词定义。它把多个单词组合起来进行导航操作（也就是一次可以阅读多个单词）。要组合起来的单词数是可以自定义的。
- 默认未分配手势：自定义正则表达式单词导航。允许用户自定义正则表达式作为单词之间的分界。

这些手势在单词导航的设置面板中是可以自定义的。

## 注释

- 目前，单词导航插件并没有对用于选择单词的手势——`Ctrl+Shift+左右箭头`进行改动，因为这些命令的实现非常复杂。
- 如果你想使用 Windows10 的虚拟桌面功能，请记得在单词导航的设置面板或 NVDA 的输入手势对话框中禁用“Ctrl+Windows+箭头”这个快捷键。

## 下载

[单词导航最新稳定版](https://github.com/mltony/nvda-word-nav/releases/latest/download/wordNav.nvda-addon)