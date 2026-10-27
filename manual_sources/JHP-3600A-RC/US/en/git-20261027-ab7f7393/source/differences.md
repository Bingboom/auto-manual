# JHP-3600A-RC US — deliberate differences from print

1. Cover, paper TOC, back cover and page numbers are not on the Web page (`web_exclusions`).
2. The printed FCC panel has no title; the shared theme keeps an `FCC` H1 for navigation and assistive
   technology only, as on the other shared FCC editions.
3. Bold spans inside callout bodies (USB-C caution, 2.3 note) render as plain text: the shared callout
   carrier compares its body line by line. The words are unchanged.
4. LCD rows ④ and ⑲ cover two icons each in print (merged cell); the shared LCD table repeats the number.
5. Warranty years render as the shared numeric badges; section title pills are the headings before each card.
6. In-panel body copy (UPS description, AC charging instruction, car-cable pill, standby callout) is blanked
   in the panel art and rendered as native text after the figure; the USB prerequisite pill corner is
   blanked in the art and the pill is a native paragraph.
7. The key-combination and LCD tables scroll inside their shared component when the column is narrower
   than the component's minimum width.
8. Sphinx typesetting turns straight apostrophes/quotes into typographic ones (shared scaffold behaviour).
