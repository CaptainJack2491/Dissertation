// Content for Abstract, Acknowledgements, Table of Contents

#set heading(numbering: none) // Temporarily disable numbering for Abstract/Ack
= Abstract <abstract>
#show heading.where(level: 1): it => {
  set block(above: 2em, below: 1em) // Adjust spacing for these headings
  align(center, text(16pt, weight: "bold", it.body))
}

// Abstract text goes here...
#lorem(50)

#pagebreak()

= Acknowledgements <acknowledgements>

// Acknowledgements text goes here...
Special thanks to...

#pagebreak()

= Table of Contents <toc>
#set heading(numbering: "1.1.1") // Re-enable numbering before ToC
#outline(
  title: none, // Don't repeat "Table of Contents" inside the outline
  depth: 2 // Show chapter and section headings, adjust as needed
)

#pagebreak() // Ensure Chapter 1 starts on a new page
