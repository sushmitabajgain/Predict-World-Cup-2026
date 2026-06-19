import React from 'react';

export default function GroupSelector({ groups, activeGroup, onChange }) {
  return (
    <div className="group-selector" aria-label="Groups">
      <button className={!activeGroup ? 'active' : ''} onClick={() => onChange('')} type="button">
        All
      </button>
      {groups.map((group) => (
        <button
          className={group === activeGroup ? 'active' : ''}
          key={group}
          onClick={() => onChange(group)}
          type="button"
        >
          {group.replace('Group ', '')}
        </button>
      ))}
    </div>
  );
}
