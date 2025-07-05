import React from 'react';
import { useDraggable } from '@dnd-kit/core';
import { CSS } from '@dnd-kit/utilities';

interface DraggableToolProps {
  id: string;
  data: { [key: string]: any };
  children: React.ReactNode;
}

export function DraggableTool({ id, data, children }: DraggableToolProps) {
  const { attributes, listeners, setNodeRef, transform } = useDraggable({
    id: id,
    data: data,
  });

  const style = {
    transform: CSS.Translate.toString(transform),
  };

  return (
    <div ref={setNodeRef} style={style} {...listeners} {...attributes} className="cursor-grab">
      {children}
    </div>
  );
} 