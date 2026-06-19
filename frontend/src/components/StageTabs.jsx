import React from 'react';

export default function StageTabs({ stages, activeStage, onChange }) {
  return (
    <div className="stage-tabs" role="tablist" aria-label="Tournament stages">
      {stages.map((stage) => (
        <button
          className={stage === activeStage ? 'active' : ''}
          key={stage}
          onClick={() => onChange(stage)}
          type="button"
        >
          {stage}
        </button>
      ))}
    </div>
  );
}
