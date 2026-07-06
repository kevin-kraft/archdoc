import React from 'react';

type PdfDocumentProps = {
  src: string;
  title: string;
  height?: number;
};

export default function PdfDocument({src, title, height = 780}: PdfDocumentProps) {
  return (
    <section className="archdocPdfDocument" aria-label={title}>
      <header className="archdocPdfDocumentHeader">
        <div>
          <strong>{title}</strong>
          <span>Embedded PDF handbook</span>
        </div>
        <div className="archdocPdfDocumentControls">
          <a href={src} target="_blank" rel="noreferrer">Open PDF</a>
          <a href={src} download>Download</a>
        </div>
      </header>
      <iframe
        title={title}
        src={`${src}#view=FitH`}
        style={{height}}
      />
    </section>
  );
}
