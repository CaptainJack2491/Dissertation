// =============================================================================
// Main Document — Testing In-Context Sleeper Agents
// =============================================================================

#set document(
  title: "Strategic Deception under varying oversight levels in Autonomous Agents",
  author: "Jayrup Nakawala",
)

#set page(
  paper: "a4",
  margin: (top: 2.5cm, bottom: 2.5cm, left: 2.5cm, right: 2.5cm),
  numbering: "1",
  number-align: center,
)

#set text(
  font: "New Computer Modern",
  size: 11pt,
  lang: "en",
)

#set par(
  justify: true,
  leading: 0.65em,
  first-line-indent: 1.2em,
)

#set heading(numbering: "1.1")

#show heading.where(level: 1): it => {
  set text(size: 16pt, weight: "bold")
  set block(above: 2em, below: 1em)
  it
}

#show heading.where(level: 2): it => {
  set text(size: 13pt, weight: "bold")
  set block(above: 1.5em, below: 0.8em)
  it
}

#show heading.where(level: 3): it => {
  set text(size: 11pt, weight: "bold")
  set block(above: 1.2em, below: 0.6em)
  it
}

// Table styling
#set table(
  stroke: 0.5pt + luma(180),
  inset: 6pt,
)

#show table.cell.where(y: 0): set text(weight: "bold", size: 10pt)

// Figure styling
#show figure.caption: it => {
  set text(size: 10pt)
  it
}

// ---- Title Page ----
#page(numbering: none)[
  #align(center + horizon)[
    #block(width: 100%)[
      // #image("uel.svg", width: 40%)
      #v(2em)
      #line(length: 100%, stroke: 2pt)
      #v(1.5em)
      #text(size: 22pt, weight: "bold")[
Strategic Deception under varying \ oversight levels in Autonomous Agents
      ]
      #v(1.5em)
      #line(length: 100%, stroke: 2pt)
      #v(3em)
      #text(size: 13pt)[Jayrup Nakawala]
      #v(0.3em)
      #text(size: 12pt, fill: luma(80))[University of East London]
      #v(3em)
      #text(size: 12pt, fill: luma(100))[Supervisor: Dr. Aloysius Adotey Edoh]
      #v(4em)
      #text(size: 11pt, fill: luma(120))[March 2026]
    ]
  ]
]

// ---- Abstract ----
#include "abstract.typ"

// ---- Main Sections ----
#include "introduction.typ"
#include "methodology.typ"
#include "results.typ"
#include "conclusion.typ"

// ---- References ----
#pagebreak()
#bibliography(
  "references.bib",
  style: "harvard-cite-them-right",
  title: "References",
)
