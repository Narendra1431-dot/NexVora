# NexVora HTML splash integration

Adapted the supplied C:/workspace/frontend/index.html, style.css and script.js splash structure into src/components/layout/LoginSplash.tsx and its scoped CSS. The prototype login form, mock authentication and global CSS resets are deliberately excluded: the existing application Login remains mounted as children and owns authentication.

The supplied frontend/nexvora-logo.png was an SVG placeholder with a PNG extension. The actual final PNG attachment (ChatGPT Image Oct 3, 2026, 12_12_56 AM.png) is copied unchanged to public/branding/nexvora-logo.png. SHA-256: 3B2B10E85D4DD275472557835716AF269509F5BF74100CDF353122EDEE8FC5BA.

Timeline after image load: energy point/rings/particles, construction at 1s, original logo fade at 1.9s, original wordmark reveal at 2.8s, original tagline reveal at 3.3s, light sweep at 3.85s, complete unchanged image held from 4.5s, simultaneous exit/login transition from 5.0 to 5.6s. Wordmark/tagline masks reveal the original pixels, not duplicate typeset text. All effects are scoped and finite.

The final 600ms fades/scales the splash to 1.02 and fades/translates Login from 10px to zero. The splash then unmounts, restores scrolling and releases inert/accessibility hiding. The existing plcip_token session skips it; nexvora_splash_shown prevents replay. Reduced motion displays the final logo for 1s and fades over 600ms without transforms/construction. Image failure or a 4s loading watchdog releases Login. Old MP4 asset removed from public and generated build; obsolete video CSS removed.

Verified 2026-10-03: 1920x1080, 1366x768, 768x1024, 390x844, 844x390 via browser viewport tests. Full viewport overlay, complete natural-aspect logo, 4px starting dot, simultaneous transition and final unmount confirmed. Browser error logs empty. Production build and TypeScript pass; 6 splash/auth/navigation tests pass, optional live-data case skipped. Original asset hashes match. Existing unrelated build chunk-size advisory remains.
