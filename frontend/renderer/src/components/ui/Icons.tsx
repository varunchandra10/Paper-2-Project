/**
 * Icons.tsx — Central Icon Registry for Synthexis
 * ─────────────────────────────────────────────────
 * ONE icon per purpose. No duplicates across packages.
 * All components import from here — never from react-icons/* directly.
 *
 * Usage:
 *   import { IconPdf, IconClose, IconTrash } from '../ui/Icons';
 *
 * Theme-aware color helpers (apply as className):
 *   IconColor.main    → text-[var(--text-main)]
 *   IconColor.muted   → text-[var(--text-muted)]
 *   IconColor.accent  → text-[var(--accent)]
 */

// ─── Theme-Aware Icon Color Constants ────────────────────────────────────────
export const IconColor = {
  main:   'text-[var(--text-main)]',
  muted:  'text-[var(--text-muted)]',
  accent: 'text-[var(--accent)]',
  error:  'text-red-400',
  warn:   'text-amber-400',
  ok:     'text-emerald-400',
} as const;

// ─── File Type Icons ──────────────────────────────────────────────────────────
// PDF  → FaFilePdf   (fa6)
// Word → FaFileWord  (fa6)
// Doc  → IoIosDocument (io)
// Generic file → IoIosDocument (io)
export { FaFilePdf    as IconPdf  } from 'react-icons/fa6';
export { FaFileWord   as IconWord } from 'react-icons/fa6';
export { IoIosDocument as IconDoc } from 'react-icons/io';

// ─── Action Icons ─────────────────────────────────────────────────────────────
// Close / X  → IoClose  (io5)
// Check      → FaCheck  (fa6)
// Trash      → FaTrashCan (fa6)
// Search     → FaSearch (fa)
// Terminal   → FaTerminal (fa6)
export { IoClose      as IconClose    } from 'react-icons/io5';
export { FaCheck      as IconCheck    } from 'react-icons/fa6';
export { FaTrashCan   as IconTrash    } from 'react-icons/fa6';
export { FaSearch     as IconSearch   } from 'react-icons/fa';
export { FaTerminal   as IconTerminal } from 'react-icons/fa6';

// ─── Navigation Icons ─────────────────────────────────────────────────────────
export {
  FiChevronLeft  as IconBack,
  FiChevronRight as IconForward,
  FiChevronUp    as IconUp,
  FiArrowRight   as IconArrowRight,
  FiArrowUp      as IconArrowUp,
} from 'react-icons/fi';

// ─── Window Control Icons ─────────────────────────────────────────────────────
export {
  FiMaximize as IconMaximize,
  FiMinimize as IconMinimize,
} from 'react-icons/fi';

// ─── UI / General Icons ───────────────────────────────────────────────────────
export {
  FiPlus          as IconPlus,
  FiFile          as IconFile,
  FiFileText      as IconFileText,
  FiMessageSquare as IconMessageSquare,
  FiClock         as IconClock,
  FiUploadCloud   as IconUploadCloud,
  FiLoader        as IconLoader,
  FiCopy          as IconCopy,
  FiCpu           as IconCpu,
  FiActivity      as IconActivity,
  FiBookOpen      as IconBookOpen,
} from 'react-icons/fi';

// ─── User / Profile Icons ─────────────────────────────────────────────────────
export {
  FiUser,
  FiMail         as IconMail,
  FiPhone        as IconPhone,
  FiCalendar     as IconCalendar,
  FiFolder       as IconFolder,
  FiCheckCircle  as IconCheckCircle,
  FiSave         as IconSave,
  FiSmile        as IconSmile,
  FiInfo         as IconInfo,
  FiLink         as IconLink,
  FiAlertCircle  as IconAlertCircle,
  FiUser         as IconUser,
} from 'react-icons/fi';

// ─── Theme Toggle Icons ───────────────────────────────────────────────────────
export { FiSun  as IconSun  } from 'react-icons/fi';
export { FiMoon as IconMoon } from 'react-icons/fi';
export { BsSnow  as IconSnow  } from 'react-icons/bs';
export { BsStars as IconStars } from 'react-icons/bs';

// ─── File Type Specific (BS — used in PdfAttachmentCard variants) ─────────────
export { BsFiletypeDocx as IconFileDocx } from 'react-icons/bs';
export { BsFiletypeTxt  as IconFileTxt  } from 'react-icons/bs';
export { BsBoxArrowUpRight as IconExternalLink } from 'react-icons/bs';

// ─── Log Level / Status Icons ─────────────────────────────────────────────────
export {
  FaCircleInfo          as IconInfo2,
  FaCircleXmark         as IconError,
  FaTriangleExclamation as IconWarning,
  FaTriangleExclamation as IconWarn,
} from 'react-icons/fa6';

// ─── Model / AI Icons ─────────────────────────────────────────────────────────
export {
  FaRobot as IconRobot,
  FaBrain as IconBrain,
  FaCode  as IconCode,
} from 'react-icons/fa6';

// ─── Misc ─────────────────────────────────────────────────────────────────────
export { FaRegFilePdf   as IconPdfOutline } from 'react-icons/fa6';
export { FaRegFolderOpen as IconFolderOpen } from 'react-icons/fa6';
export { FaTasks as IconTasks } from 'react-icons/fa';
