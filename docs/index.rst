.. raw:: latex

   % Cover: no page number
   \includepdf[pages=1-,fitpaper=true,pagecommand={\thispagestyle{empty}}]{cover.pdf}
   % Start numbering from Safety page
   \clearpage
   \pagenumbering{arabic}
   \setcounter{page}{1}

.. include:: safety.rst

.. raw:: latex

   % Overview page (keep numbering)
   \includepdf[pages=1-,fitpaper=true,pagecommand={\thispagestyle{fancy}}]{product_overview.pdf}