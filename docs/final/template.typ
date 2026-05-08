// template.typ
#let is-appendix = state("is-appendix", false)

#let project(
  title: "",
  author: "",
  student_id: "",
  degree: "",
  supervisor: "",
  date: datetime.today(),
  abstract: [],
  acknowledgments: [],
  body
) = {
  // 1. Page & Font Setup
  set document(author: author, title: title)
  set page(
    paper: "a4",
    margin: (left: 2.5cm, right: 2.5cm, top: 2.5cm, bottom: 2.5cm),
    numbering: none,
  )
  set text(lang: "en", size: 12pt)
  
  // 2. The Title Page [cite: 1]
  align(center)[
    // INSERT LOGO HERE
    #image("uel.svg", width: 5cm) 
    #v(2em) // Adds a small gap between logo and text
    
    #text(size: 14pt)[SCHOOL OF ARCHITECTURE, COMPUTING AND ENGINEERING] \
    #v(0.5em)
    #text(size: 12pt)[Department of Engineering and Computing]
    
    #v(4fr)
    
    #text(weight: "bold", size: 22pt)[#title]
    
    #v(2fr)
    
    #text(weight: "bold", size: 14pt)[#author] \
    #text(size: 12pt)[#student_id]
    
    #v(2fr)
    
    A report submitted in part fulfilment of the degree of \
    BSc (Hons) in #text(style: "italic")[#degree]
    
    #v(1em)
    
    Supervisor: #supervisor \
    CN6000

    #v(2fr)
    
    
    #v(1em)
    #date
    #v(2em)
  ]
  pagebreak()

  set page(numbering: "i")
  counter(page).update(1) 

  // 3. Front Matter (Abstract & Acknowledgments)
  // We use aligned numbering: none so they don't get "1. Abstract"
  set heading(numbering: none)
  
  heading(level: 1, outlined: true)[Abstract]
  abstract
  pagebreak()

  heading(level: 1, outlined: true)[Acknowledgments]
  acknowledgments
  pagebreak()

  // 4. Table of Contents [cite: 6]
  outline(depth: 3, indent: 2em)
  pagebreak()

  // 4.1 List of Figures and Tables
  heading(level: 1, outlined: true)[List of Figures]
  outline(target: figure.where(kind: image), title: none)
  pagebreak()

  heading(level: 1, outlined: true)[List of Tables]
  outline(target: figure.where(kind: table), title: none)
  pagebreak()

  // 4.2 Start numbering pages
  set page(numbering: "1")
  counter(page).update(1) 
  // ------------------------

  // 5. Main Content Styling & Headers
  set page(
    numbering: "1",
    // HEADER LOGIC STARTS HERE
    header: context {
      // 1. Get the current page number
      let current_page = here().page()
      
      // 2. Find the last heading BEFORE this point
      let before = query(selector(heading.where(level: 1)).before(here()))
      
      // 3. Find the first heading AFTER this point (potential new chapter on this page)
      let after = query(selector(heading.where(level: 1)).after(here()))
      
      let target_heading = none

      // LOGIC: If a heading exists AFTER the header but ON THE SAME PAGE, use it.
      if after.len() > 0 and after.first().location().page() == current_page {
        target_heading = after.first()
      } 
      // OTHERWISE: Use the heading from before (continuation of previous chapter)
      else if before.len() > 0 {
        target_heading = before.last()
      }

      // 4. Render the header if we found a valid heading
      if target_heading != none {
        grid(
            columns: (1fr, 1fr),
            align(left)[
              #text(style: "italic", size: 10pt)[
                // Check state to distinguish appendices from chapters
                #if target_heading.numbering != none [
                  #if is-appendix.get() [
                    Appendix #numbering("A", counter(heading).at(target_heading.location()).first()): 
                  ] else [
                    Chapter #counter(heading).at(target_heading.location()).first(): 
                  ]
                ]
                #target_heading.body
              ]
            ],
            align(right)[
              #text(size: 10pt)[#author]
            ]
        )
        v(-0.8em)
        line(length: 100%, stroke: 0.5pt + gray)
      }
    }
    // ... end set page ...
  )
  
  counter(page).update(1)
  set heading(numbering: "1.1")
  // Table captions at top (academic convention)
  show figure.where(kind: table): set figure.caption(position: top)
  // Bold label (e.g. "Figure 1:"), italic description
  show figure.caption: it => [
    #text(weight: "bold")[#it.supplement #context it.counter.display(it.numbering):]
    #text(style: "italic", it.body)
  ]
  // Number all display equations
  set math.equation(numbering: "(1)")
  
  // Custom rule to force "Chapter X: Title" formatting
  show heading.where(level: 1): it => {
    pagebreak(weak: true)
    v(1em)
    text(size: 16pt, weight: "bold")[
      Chapter #counter(heading).display(): #it.body
    ]
    v(1em)
  }

  // Paragraph styling
  set par(justify: true, leading: 0.8em)
  
  body
}

// Helper for multi-page PDF inclusion
#let include-pdf(path, pages: 1) = {
  for i in range(1, pages + 1) {
    image(path, page: i, width: 100%)
    if i < pages { pagebreak() }
  }
}

// Qualitative Analysis Components
#let thought(body) = {
  v(0.6em)
  block(
    fill: rgb("#f8fafc"),
    inset: (x: 1.5em, y: 1.2em),
    radius: 6pt,
    width: 100%,
    stroke: (left: 4pt + rgb("#94a3b8")),
    [
      #text(size: 8pt, weight: "bold", fill: rgb("#64748b"), tracking: 0.08em)[INTERNAL REASONING]
      #v(0.4em)
      #set text(size: 11pt, style: "italic", fill: rgb("#334155"))
      #body
    ]
  )
  v(0.6em)
}

#let chat(body, name: "Model Output") = {
  v(0.6em)
  block(
    fill: rgb("#f1f5f9"),
    inset: (x: 1.5em, y: 1.2em),
    radius: 6pt,
    width: 100%,
    stroke: (left: 4pt + rgb("#3b82f6")),
    [
      #text(size: 8pt, weight: "bold", fill: rgb("#1e40af"), tracking: 0.08em)[#upper(name)]
      #v(0.4em)
      #set text(size: 11pt, fill: rgb("#1e293b"))
      #body
    ]
  )
  v(0.6em)
}

// Helper for Appendices to switch lettering
#let appendix(body) = {
  is-appendix.update(true)
  pagebreak()
  counter(heading).update(0)
  set heading(numbering: "A.1")
  show heading.where(level: 1): it => {
    pagebreak(weak: true)
    text(size: 14pt, weight: "bold")[
      Appendix #counter(heading).display("A") - #it.body
    ]
    v(1em)
  }
  body
}
