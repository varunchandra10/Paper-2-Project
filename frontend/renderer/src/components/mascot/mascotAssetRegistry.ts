// --- Asset Imports for Mr. Nerdy ---
import mrNerdyStanding from '../../assets/mr_nerdy/mr_nerdy_standing.png';
import mrNerdySleeping from '../../assets/mr_nerdy/mr_nerdy_sleeping.png';
import mrNerdyExcited from '../../assets/mr_nerdy/mr_nerdy_excited.png';
import mrNerdyHunching from '../../assets/mr_nerdy/mr_nerdy_huncing.png';
import mrNerdyThinking from '../../assets/mr_nerdy/mr_nerdy_thinking.png';
import mrNerdyWaving from '../../assets/mr_nerdy/mr_nerdy_waving.png';
import mrNerdyAngry from '../../assets/mr_nerdy/mr_nerdy_angry.png';
import mrNerdyPeeking from '../../assets/mr_nerdy/mr_nerdy_peeking.png';
import mrNerdySipping from '../../assets/mr_nerdy/mr_nerdy_having_sipping.png';
import mrNerdyCatching from '../../assets/mr_nerdy/mr_nerdy_document_catching.png';

// --- Asset Imports for Ms. Nerdy ---
import msNerdyStanding from '../../assets/ms_nerdy/ms_nerdy_standing.png';
import msNerdySleeping from '../../assets/ms_nerdy/ms_nerdy_sleeping.png';
import msNerdyExcited from '../../assets/ms_nerdy/ms_nerdy_excited.png';
import msNerdyHunching from '../../assets/ms_nerdy/ms_nerdy_hunching.png';
import msNerdyThinking from '../../assets/ms_nerdy/ms_nerdy_thinking.png';
import msNerdyWaving from '../../assets/ms_nerdy/ms_nerdy_hand_waving.png';
import msNerdyAngry from '../../assets/ms_nerdy/ms_nerdy_angry.png';
import msNerdyPeeking from '../../assets/ms_nerdy/ms_nerdy_peeking.png';
import msNerdySipping from '../../assets/ms_nerdy/ms_nerdy_sipping_coffee.png';
import msNerdyCatching from '../../assets/ms_nerdy/ms_nerdy_document_catching.png';

// --- Asset Imports for Mr. Nerd ---
import mrNerdStanding from '../../assets/mr_nerd/mr_nerd_standing.png';
import mrNerdSleeping from '../../assets/mr_nerd/mr_nerd_sleeping.png';
import mrNerdExcited from '../../assets/mr_nerd/mr_nerd_excited.png';
import mrNerdHunching from '../../assets/mr_nerd/mr_nerd_hunching.png';
import mrNerdThinking from '../../assets/mr_nerd/mr_nerd_thinking.png';
import mrNerdWaving from '../../assets/mr_nerd/mr_nerd_waving.png';
import mrNerdAngry from '../../assets/mr_nerd/mr_nerd_angry.png';
import mrNerdPeeking from '../../assets/mr_nerd/mr_nerd_peeking.png';
import mrNerdSipping from '../../assets/mr_nerd/mr_nerd_coffee_sipping.png';
import mrNerdCatching from '../../assets/mr_nerd/mr_nerd_document_catching.png';

// --- Asset Imports for Ms. Nerd ---
import msNerdStanding from '../../assets/ms_nerd/ms_nerd_standing.png';
import msNerdSleeping from '../../assets/ms_nerd/ms_nerd_sleeping.png';
import msNerdExcited from '../../assets/ms_nerd/ms_nerd_excited.png';
import msNerdHunching from '../../assets/ms_nerd/ms_nerd_hunching.png';
import msNerdThinking from '../../assets/ms_nerd/ms_nerd_thinking.png';
import msNerdWaving from '../../assets/ms_nerd/ms_nerd_hii.png';
import msNerdAngry from '../../assets/ms_nerd/ms_nerd_angry.png';
import msNerdPeeking from '../../assets/ms_nerd/ms_nerd_peeking.png';
import msNerdSipping from '../../assets/ms_nerd/ms_nerd_coffee_sipping.png';
import msNerdCatching from '../../assets/ms_nerd/ms_nerd_document_catching.png';

export type AvatarId = 'mr-nerdy' | 'ms-nerdy' | 'mr-nerd' | 'ms-nerd';

export type MascotPose = 
  | 'standing' 
  | 'sleeping' 
  | 'excited' 
  | 'hunching' 
  | 'thinking' 
  | 'waving' 
  | 'angry' 
  | 'peeking' 
  | 'sipping_coffee' 
  | 'document_catching';

export interface MascotInfo {
  id: AvatarId;
  name: string;
  role: string;
  description: string;
  standingImage: string;
  poses: Record<MascotPose, string>;
}

export const MASCOT_REGISTRY: Record<AvatarId, MascotInfo> = {
  'mr-nerdy': {
    id: 'mr-nerdy',
    name: 'Mr. Nerdy',
    role: 'Companion',
    description: 'Interactive AI research mascot.',
    standingImage: mrNerdyStanding,
    poses: {
      standing: mrNerdyStanding,
      sleeping: mrNerdySleeping,
      excited: mrNerdyExcited,
      hunching: mrNerdyHunching,
      thinking: mrNerdyThinking,
      waving: mrNerdyWaving,
      angry: mrNerdyAngry,
      peeking: mrNerdyPeeking,
      sipping_coffee: mrNerdySipping,
      document_catching: mrNerdyCatching,
    }
  },
  'ms-nerdy': {
    id: 'ms-nerdy',
    name: 'Ms. Nerdy',
    role: 'Companion',
    description: 'Interactive AI research mascot.',
    standingImage: msNerdyStanding,
    poses: {
      standing: msNerdyStanding,
      sleeping: msNerdySleeping,
      excited: msNerdyExcited,
      hunching: msNerdyHunching,
      thinking: msNerdyThinking,
      waving: msNerdyWaving,
      angry: msNerdyAngry,
      peeking: msNerdyPeeking,
      sipping_coffee: msNerdySipping,
      document_catching: msNerdyCatching,
    }
  },
  'mr-nerd': {
    id: 'mr-nerd',
    name: 'Mr. Nerd',
    role: 'Companion',
    description: 'Interactive AI research mascot.',
    standingImage: mrNerdStanding,
    poses: {
      standing: mrNerdStanding,
      sleeping: mrNerdSleeping,
      excited: mrNerdExcited,
      hunching: mrNerdHunching,
      thinking: mrNerdThinking,
      waving: mrNerdWaving,
      angry: mrNerdAngry,
      peeking: mrNerdPeeking,
      sipping_coffee: mrNerdSipping,
      document_catching: mrNerdCatching,
    }
  },
  'ms-nerd': {
    id: 'ms-nerd',
    name: 'Ms. Nerd',
    role: 'Companion',
    description: 'Interactive AI research mascot.',
    standingImage: msNerdStanding,
    poses: {
      standing: msNerdStanding,
      sleeping: msNerdSleeping,
      excited: msNerdExcited,
      hunching: msNerdHunching,
      thinking: msNerdThinking,
      waving: msNerdWaving,
      angry: msNerdAngry,
      peeking: msNerdPeeking,
      sipping_coffee: msNerdSipping,
      document_catching: msNerdCatching,
    }
  }
};

export const getMascotAsset = (avatarId?: string | null, pose: MascotPose = 'standing'): string => {
  const validAvatarId = (avatarId && avatarId in MASCOT_REGISTRY) ? (avatarId as AvatarId) : 'mr-nerdy';
  const mascot = MASCOT_REGISTRY[validAvatarId];
  return mascot.poses[pose] || mascot.standingImage;
};
