/**
 * Shared Formatting Utilities
 *
 * Provides standardized file size, date, and paper ID slug formatting
 * eliminating duplicate formatting logic across sidebars and document lists.
 */

/**
 * Formats byte counts into human-readable strings (e.g. "1.5 MB", "450 KB")
 */
export const formatFileSize = (size?: string | number): string => {
  if (!size) return '0 B';
  if (typeof size === 'string' && isNaN(Number(size))) return size;
  const bytes = Number(size);
  if (bytes <= 0) return '0 B';
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
};

/**
 * Formats timestamps or ISO date strings into clean display labels (e.g. "Aug 27")
 */
export const formatDate = (dateString?: string | number): string => {
  if (!dateString) return 'Recent';
  try {
    const timestamp = typeof dateString === 'number' && dateString < 1e12 ? dateString * 1000 : dateString;
    const date = new Date(timestamp);
    if (isNaN(date.getTime())) return String(dateString);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  } catch {
    return String(dateString);
  }
};

/**
 * Derives a canonical paper identifier slug from a filename
 * e.g. "Attention Is All You Need.pdf" -> "paper_attention_is_all_you_need"
 */
export const getPaperId = (filename: string): string => {
  if (!filename) return 'paper_document';
  const baseName = filename.replace(/\.[^/.]+$/, ""); // Strip extension
  const cleanTitle = baseName.toLowerCase().replace(/[^a-z0-9\s]/g, '').trim();
  const slug = cleanTitle.replace(/\s+/g, '_').substring(0, 30).replace(/^_+|_+$/g, '');
  return slug ? `paper_${slug}` : 'paper_document';
};
