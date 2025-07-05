import React from 'react';
import { useDroppable } from '@dnd-kit/core';

interface DroppableAreaProps {
  id: string;
  children: React.ReactNode;
}

export function DroppableArea({ id, children }: DroppableAreaProps) {
  const { isOver, setNodeRef } = useDroppable({
    id: id,
  });

  const style: React.CSSProperties = {
    transition: 'background-color 0.2s ease',
    backgroundColor: isOver ? 'rgba(255, 255, 255, 0.05)' : 'transparent',
    minHeight: '100px', // Ensure area is large enough to be dropped on
  };

  return (
    <div ref={setNodeRef} style={style} className="rounded-lg p-4">
      {children}
    </div>
  );
} 