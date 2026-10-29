export const sections = ['', 'world', 'technology', 'science', 'business', 'sport', 'environment'];
export function safeArticle(article) {
  if (!article || typeof article !== 'object' || !['title', 'description', 'url', 'publishedAt', 'category'].every(key => typeof article[key] === 'string')) return false;
  try { const url = new URL(article.url); return url.protocol === 'https:' && url.hostname === 'www.theguardian.com' && !url.username && !url.password; } catch { return false; }
}
export function getFilters(params) {
  return { q: (params.get('q') || '').slice(0, 150), section: sections.includes(params.get('section')) ? params.get('section') : '',
    period: ['day', 'week', 'month'].includes(params.get('period')) ? params.get('period') : '',
    sort: params.get('sort') === 'relevance' ? 'relevance' : 'newest',
    page: /^\d+$/.test(params.get('page') || '') ? Math.min(50, Math.max(1, Number(params.get('page')))) : 1 };
}

export function toggleBookmark(saved, article) {
  if (saved.some(item => item.url === article.url)) return saved.filter(item => item.url !== article.url);
  if (saved.length >= 100) return null;
  return [{ ...article, description: '' }, ...saved];
}
