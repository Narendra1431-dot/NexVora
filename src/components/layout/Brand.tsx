import './Brand.css';

/**
 * Enhanced Brand component with premium styling
 * Uses design system tokens for consistent appearance
 */
export function Brand({ symbolOnly = false, compact = false }: { symbolOnly?: boolean; compact?: boolean }) {
  return <span 
    className={`nexvora-brand${symbolOnly ? ' nexvora-brand--symbol' : ''}${compact ? ' nexvora-brand--compact' : ''} brand-premium`} 
    role="img" 
    aria-label="NexVora – Skills Today, Opportunities Tomorrow"
  >
    <svg className="nexvora-brand__symbol" viewBox="575 105 590 480" aria-hidden="true">
      <image href="/branding/nexvora-reference.png" width="1672" height="941"/>
    </svg>
    {!symbolOnly && <svg className="nexvora-brand__wordmark" viewBox="410 585 875 170" aria-hidden="true">
      <image href="/branding/nexvora-reference.png" width="1672" height="941"/>
    </svg>}
  </span>;
}
