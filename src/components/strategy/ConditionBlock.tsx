import React from 'react';
import { DndContext, closestCenter, KeyboardSensor, PointerSensor, useSensor, useSensors, DragEndEvent } from '@dnd-kit/core';
import { arrayMove, SortableContext, sortableKeyboardCoordinates, verticalListSortingStrategy } from '@dnd-kit/sortable';
import { useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { Plus } from 'lucide-react';
import { Condition } from './types';
import { ConditionRow } from './ConditionRow';

interface SortableConditionRowProps {
  condition: Condition;
  onUpdate: (id: string, newCondition: Partial<Condition>) => void;
  onDelete: (id: string) => void;
  index: number;
}

function SortableConditionRow({ condition, onUpdate, onDelete, index }: SortableConditionRowProps) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({ id: condition.id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  };

  return (
    <div ref={setNodeRef} style={style} {...attributes}>
      <ConditionRow
        condition={condition}
        onUpdate={onUpdate}
        onDelete={onDelete}
        isDragging={isDragging}
        index={index}
        dragHandleProps={listeners}
      />
    </div>
  );
}

interface ConditionBlockProps {
  title: string;
  borderColor: string;
  conditions: Condition[];
  setConditions: (updater: React.SetStateAction<Condition[]>) => void;
}

export function ConditionBlock({ title, borderColor, conditions, setConditions }: ConditionBlockProps) {
  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates })
  );

  function handleAddCondition() {
    const newCondition: Condition = { id: Date.now().toString(), indicator: 'EMA (20)', operator: '>', value: 0 };
    setConditions(prev => [...prev, newCondition]);
  }

  function handleUpdateCondition(id: string, newCondition: Partial<Condition>) {
    setConditions(prev => prev.map(c => c.id === id ? { ...c, ...newCondition } : c));
  }

  function handleDeleteCondition(id: string) {
    setConditions(prev => prev.filter(c => c.id !== id));
  }

  function handleDragEnd(event: DragEndEvent) {
    const { active, over } = event;
    if (over && active.id !== over.id) {
      setConditions((items) => {
        const oldIndex = items.findIndex(item => item.id === active.id);
        const newIndex = items.findIndex(item => item.id === over.id);
        return arrayMove(items, oldIndex, newIndex);
      });
    }
  }

  return (
    <div className={`bg-slate-800/50 rounded-lg p-5 border-t-4 ${borderColor}`}>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-xl font-bold text-white">{title}</h3>
        <button onClick={handleAddCondition} className="flex items-center space-x-2 bg-slate-700 hover:bg-slate-600 text-white font-semibold px-4 py-2 rounded-lg text-sm">
          <Plus size={16} />
          <span>Add</span>
        </button>
      </div>

      <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
        <SortableContext items={conditions} strategy={verticalListSortingStrategy}>
          <div className="space-y-2">
            {conditions.map((condition, index) => (
              <SortableConditionRow
                key={condition.id}
                condition={condition}
                onUpdate={handleUpdateCondition}
                onDelete={handleDeleteCondition}
                index={index + 1}
              />
            ))}
          </div>
        </SortableContext>
      </DndContext>
    </div>
  );
} 