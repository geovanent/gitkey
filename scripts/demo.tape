# Generate: vhs demo.tape  (https://github.com/charmbracelet/vhs)
Output assets/demo/demo-vhs.gif

Set FontSize 16
Set Width 1100
Set Height 420
Set Theme "Catppuccin Mocha"
Set Padding 24

Type "gitkey -p personal"
Enter
Sleep 2s

Type "cd ~/work/client-repo"
Enter
Sleep 800ms

Type "gitkey --bind -p clientA"
Enter
Sleep 2s

Type "git push"
Enter
Sleep 2s
