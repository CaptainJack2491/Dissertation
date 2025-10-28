// 1. Define or import the title page function
#let title-page(title:[], subtitle:[], name:[], studentid:[], body) = {
  // Use `auto` for page dimensions unless you need fixed sizes
  // set page(width: auto, height: auto, margin: (top: 1.5in, rest: 1in)) // Adjusted margins
  set text(size: 12pt) // Set base size for body, adjust locally
  // Define title page specific layout
  align(horizon + left)[
    #line(length: 100%, stroke: 2pt)
    #v(1em)
    #text(size: 24pt, weight: "bold", title)
    #v(1em)
    #text(size: 18pt, subtitle)
    #v(3em) // More space before name
    #text(size: 14pt, name)
    #v(0.5em)
    #text(size: 14pt, studentid)
    #v(1fr) // Push content down if needed
  ]
  pagebreak() // Ensures body starts on a new page
  // Reset text size for the main body content
  set text(size: 12pt)
  // Apply heading numbering for the rest of the document here or after preface
  set heading(numbering: "1.1")
  body // This is where the included content will go
}

// 2. Apply the show rule using the function
#show: body => title-page(
  title: [Testing In-Context Sleeper Agents: Challenges in Detecting Hidden Goal Pursuit], // Your updated title
  subtitle: [Dissertation (CN6000)],
  name: "Jayrup Nakawala",
  studentid: "u2613621",
  body // Pass the actual document body through
)

// --- Document Content Starts Here ---

// 3. Include preface content (Abstract, Acknowledgements, ToC)
#include "preface.typ"

// 4. Include main chapters
#include "intro.typ" // Introduction
#include "lit.typ" // Literature Review
#include "methodology.typ" // Methodology
#include "results.typ" // Results
#include "analysis.typ" // Analysis
#include "conclusion.typ" // Conclusion

// 5. Include Bibliography (if in separate file or define here)
// #bibliography("references.bib")

// Title page
// Contents
// = C1: Introduction
// = C2: Literature Review
// = C3: Methodology
// = C4: Results
// = C5: Analysis
// = C6: Conclusion
// References
// Appendices
