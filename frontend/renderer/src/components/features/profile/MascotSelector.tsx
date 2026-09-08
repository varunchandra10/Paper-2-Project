import React from 'react';
import { 
  type AvatarId, 
  MASCOT_REGISTRY, 
  MascotWaistUpCard 
} from '../../mascot/MascotCompanion';

export const MASCOT_LIST: AvatarId[] = ['mr-nerdy', 'ms-nerdy', 'mr-nerd', 'ms-nerd'];

interface MascotSelectorProps {
  formAvatar: string;
  setFormAvatar: (id: string) => void;
}

export const MascotSelector: React.FC<MascotSelectorProps> = ({
  formAvatar,
  setFormAvatar
}) => {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 h-full items-stretch">
      {MASCOT_LIST.map((avatarId) => {
        const info = MASCOT_REGISTRY[avatarId];
        if (!info) return null;
        const isSelected = formAvatar === avatarId;

        return (
          <MascotWaistUpCard
            key={avatarId}
            avatarId={avatarId}
            isSelected={isSelected}
            onClick={() => setFormAvatar(avatarId)}
          />
        );
      })}
    </div>
  );
};
