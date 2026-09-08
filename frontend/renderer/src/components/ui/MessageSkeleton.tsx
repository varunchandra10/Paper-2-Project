import React from 'react';

/**
 * MessageSkeleton — 3 pulsing skeleton message rows shown during conversation switch
 * while fetchMessages is in-flight.
 */
export const MessageSkeleton: React.FC = () => (
  <div className="flex flex-col gap-3 w-full p-4 animate-pulse select-none" data-testid="message-skeleton">
    {[1, 2, 3].map((i) => (
      <div
        key={i}
        className="h-16 rounded-xl border app-border"
        style={{ background: 'var(--bg-elevated, rgba(255, 255, 255, 0.04))' }}
      />
    ))}
  </div>
);

export default MessageSkeleton;
