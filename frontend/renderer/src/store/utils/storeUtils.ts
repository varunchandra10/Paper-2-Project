export { API_BASE, getApiBase, isElectronEnvironment } from '../../config/api';

export function getPaperId(filename: string): string {
  const baseName = filename.replace(/\.[^/.]+$/, ""); // Strip extension
  const cleanTitle = baseName.toLowerCase().replace(/[^a-z0-9\s]/g, '').trim();
  const slug = cleanTitle.replace(/\s+/g, '_').substring(0, 30).replace(/^_+|_+$/g, '');
  return `paper_${slug}`;
}
