import React, {useRef, useState} from 'react';

type DrawableDiagramProps = {
  src: string;
  title: string;
  height?: number;
};

export default function DrawableDiagram({src, title, height = 720}: DrawableDiagramProps) {
  const frameRef = useRef<HTMLDivElement | null>(null);
  const [scale, setScale] = useState(0.45);
  const [isDragging, setIsDragging] = useState(false);
  const dragStart = useRef({x: 0, y: 0, left: 0, top: 0});

  const zoom = (delta: number) => {
    setScale((value) => Math.min(1.6, Math.max(0.2, Number((value + delta).toFixed(2)))));
  };

  const reset = () => {
    setScale(0.45);
    if (frameRef.current) {
      frameRef.current.scrollTo({left: 0, top: 0, behavior: 'smooth'});
    }
  };

  return (
    <section className="archdocDrawableDiagram" aria-label={title}>
      <header className="archdocDrawableDiagramHeader">
        <div>
          <strong>{title}</strong>
          <span>{Math.round(scale * 100)}%</span>
        </div>
        <div className="archdocDrawableDiagramControls">
          <button type="button" onClick={() => zoom(-0.1)} aria-label="Zoom out">-</button>
          <button type="button" onClick={reset}>Reset</button>
          <button type="button" onClick={() => zoom(0.1)} aria-label="Zoom in">+</button>
          <a href={src} target="_blank" rel="noreferrer">Open SVG</a>
        </div>
      </header>

      <div
        ref={frameRef}
        className={`archdocDrawableDiagramFrame ${isDragging ? 'archdocDrawableDiagramFrame--dragging' : ''}`}
        style={{height}}
        onMouseDown={(event) => {
          if (!frameRef.current) return;
          setIsDragging(true);
          dragStart.current = {
            x: event.clientX,
            y: event.clientY,
            left: frameRef.current.scrollLeft,
            top: frameRef.current.scrollTop,
          };
        }}
        onMouseLeave={() => setIsDragging(false)}
        onMouseUp={() => setIsDragging(false)}
        onMouseMove={(event) => {
          if (!isDragging || !frameRef.current) return;
          frameRef.current.scrollLeft = dragStart.current.left - (event.clientX - dragStart.current.x);
          frameRef.current.scrollTop = dragStart.current.top - (event.clientY - dragStart.current.y);
        }}
      >
        <img
          src={src}
          alt={title}
          draggable={false}
          style={{width: `${scale * 5802}px`}}
        />
      </div>
    </section>
  );
}
