# Known Bugs

All the terminal display issues from the 0.0.4 era (shell required for
display-only, feed not refreshing, width/wrap problems) were fixed by the
move to `textual_tty.Monitor` — a display-only board view with a public
`feed()` that sizes itself to the cast.

## Future Investigation

- Vertical scrollbar behaviour when the cast fits the viewport (verify live
  after the Monitor port; delete this line if it's gone)
- Performance with large cast files
