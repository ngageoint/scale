echo Generating PDF...
asciidoctor-pdf -a stylesdir=./styles -a stylesheet=walkthrough.css -D /documents/output index.adoc

echo Rename output PDF...
mv /documents/output/index.pdf /documents/output/scale-walkthrough.pdf