export async function loadTermDataset(term) {
  const url = `./data/term${term}_dataset.json`;
  
  try {
    const response = await fetch(url);
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    const data = await response.json();
    return data;
  } catch (error) {
    console.error(`Failed to load dataset for term ${term}:`, error);
    throw error;
  }
}

export async function loadMEPScores(term) {
  try {
    const response = await fetch(`/api/scores/${term}`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const data = await response.json();
    if (!data.success) {
      throw new Error(data.error || 'Failed to load MEP Score data');
    }
    return data.data;
  } catch (error) {
    console.error('Error loading MEP Score data:', error);
    return null;
  }
}

export async function recalculateMEPRankingScores(term) {
  try {
    const response = await fetch(`/api/scores/${term}/recalculate`, {
      method: 'POST'
    });
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const data = await response.json();
    if (!data.success) {
      throw new Error(data.error || 'Failed to recalculate MEP Score');
    }
    return data.data;
  } catch (error) {
    console.error('Error recalculating MEP Score:', error);
    return null;
  }
}

export async function getScoringConfig() {
  try {
    const response = await fetch('/api/scoring-config');
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const data = await response.json();
    if (!data.success) {
      throw new Error(data.error || 'Failed to load scoring config');
    }
    return data.config;
  } catch (error) {
    console.error('Error loading scoring config:', error);
    return null;
  }
}

// Group name to logo file mapping
const GROUP_LOGO_MAPPING = {
  'EPP': 'EPP.png',
  'S&D': 'snd.png',
  'ECR': 'ecr-group.png',
  'European Conservatives and Reformists Group': 'ecr-group.png',
  'Renew': 'renew.png',
  'RE': 'renew.png',
  'Greens/EFA': 'greens.png',
  'GUE/NGL': 'theleft.png',
  'Left': 'theleft.png',
  'The Left group in the European Parliament - GUE/NGL': 'theleft.png',
  'ID': 'NI.png', // Using NI as fallback for ID
  'PfE': 'patriots.png',
  'Patriots for Europe Group': 'patriots.png',
  'ESN': 'ESN.png',
  'Europe of Sovereign Nations': 'ESN.png',
  'Europe of Sovereign Nations Group': 'ESN.png',
  'NI': 'NI.png',
  'Non-attached Members': 'NI.png'
};

// Group name abbreviation mapping (for fallback text)
const GROUP_ABBREVIATION_MAPPING = {
  "Group of the European People's Party (Christian Democrats)": "EPP",
  "Group of the Progressive Alliance of Socialists and Democrats in the European Parliament": "S&D",
  'Renew Europe Group': 'Renew',
  'Group of the Greens/European Free Alliance': 'Greens/EFA',
  'European Conservatives and Reformists Group': 'ECR',
  'The Left group in the European Parliament - GUE/NGL': 'Left',
  'Identity and Democracy Group': 'ID',
  'Non-attached Members': 'NI',
  'Group of the Alliance of Liberals and Democrats for Europe': 'ALDE',
  'Europe of Freedom and Direct Democracy Group': 'EFDD',
  'Europe of Nations and Freedom Group': 'ENF',
  'Patriots for Europe Group': 'PfE',
  'Europe of Sovereign Nations': 'ESN',
  'Europe of Sovereign Nations Group': 'ESN',
  'Unknown': 'NI'
};

/**
 * Get the logo filename for a political group
 * @param {string} groupName - Full group name or abbreviation
 * @returns {string|null} Logo filename or null if not found
 */
export function getGroupLogo(groupName) {
  if (!groupName) return null;
  
  // Try direct mapping first
  if (GROUP_LOGO_MAPPING[groupName]) {
    return GROUP_LOGO_MAPPING[groupName];
  }
  
  // Try abbreviation mapping
  const abbreviation = GROUP_ABBREVIATION_MAPPING[groupName];
  if (abbreviation && GROUP_LOGO_MAPPING[abbreviation]) {
    return GROUP_LOGO_MAPPING[abbreviation];
  }
  
  return null;
}

/**
 * Get the abbreviation for a political group
 * @param {string} groupName - Full group name
 * @returns {string} Group abbreviation
 */
export function getGroupAbbreviation(groupName) {
  return GROUP_ABBREVIATION_MAPPING[groupName] || groupName;
}

/**
 * Create an HTML element displaying the group logo with fallback text
 * @param {string} groupName - Full group name
 * @param {object} options - Configuration options
 * @param {string} options.size - Logo size class ('small', 'medium', 'large')
 * @param {boolean} options.showText - Whether to show text alongside logo
 * @param {string} options.className - Additional CSS classes
 * @returns {string} HTML string for the group logo/text
 */
export function createGroupDisplay(groupName, options = {}) {
  const { size = 'medium', showText = false, className = '' } = options;
  
  const logoFile = getGroupLogo(groupName);
  const abbreviation = getGroupAbbreviation(groupName);
  
  if (logoFile) {
    const sizeClass = {
      'small': 'h-4 w-auto',
      'medium': 'h-6 w-auto',
      'large': 'h-8 w-auto'
    }[size];
    
    // Use flex gap instead of margin-left for consistent spacing
    const deviceInfo = getMobileDeviceInfo();
    const isMobileOptimized = deviceInfo.isMobile;
    const textClasses = isMobileOptimized ? 'text-current text-sm' : 'text-current';
    const textSpan = showText ? `<span class="${textClasses}">${abbreviation}</span>` : '';
    
    // URL-encode the logo filename to handle spaces and special characters
    const encodedLogoFile = encodeURIComponent(logoFile);
    
    return `
      <div class="group-display inline-flex items-center ${className}" title="${groupName}">
        <img src="./logos/${encodedLogoFile}" alt="${abbreviation}" class="group-logo ${sizeClass}" onerror="this.style.display='none'; this.nextElementSibling.style.display='inline';">
        ${textSpan}
      </div>
    `;
  } else {
    // Fallback to text only
    return `<span class="group-text ${className}" title="${groupName}">${abbreviation}</span>`;
  }
}

// Country name to ISO code mapping for all EU countries
const COUNTRY_CODE_MAPPING = {
  'Austria': 'AT',
  'Belgium': 'BE', 
  'Bulgaria': 'BG',
  'Croatia': 'HR',
  'Cyprus': 'CY',
  'Czech Republic': 'CZ',
  'Czechia': 'CZ',
  'Denmark': 'DK',
  'Estonia': 'EE',
  'Finland': 'FI',
  'France': 'FR',
  'Germany': 'DE',
  'Greece': 'GR',
  'Hungary': 'HU',
  'Ireland': 'IE',
  'Italy': 'IT',
  'Latvia': 'LV',
  'Lithuania': 'LT',
  'Luxembourg': 'LU',
  'Malta': 'MT',
  'Netherlands': 'NL',
  'Poland': 'PL',
  'Portugal': 'PT',
  'Romania': 'RO',
  'Slovakia': 'SK',
  'Slovenia': 'SI',
  'Spain': 'ES',
  'Sweden': 'SE'
};

/**
 * Get ISO country code from country name
 * @param {string} countryName - Full country name
 * @returns {string} ISO country code (2 letters)
 */
export function getCountryCode(countryName) {
  const countryCodes = {
    'Austria': 'AT',
    'Belgium': 'BE',
    'Bulgaria': 'BG',
    'Croatia': 'HR',
    'Cyprus': 'CY',
    'Czech Republic': 'CZ',
    'Czechia': 'CZ',
    'Denmark': 'DK',
    'Estonia': 'EE',
    'Finland': 'FI',
    'France': 'FR',
    'Germany': 'DE',
    'Greece': 'GR',
    'Hungary': 'HU',
    'Ireland': 'IE',
    'Italy': 'IT',
    'Latvia': 'LV',
    'Lithuania': 'LT',
    'Luxembourg': 'LU',
    'Malta': 'MT',
    'Netherlands': 'NL',
    'Poland': 'PL',
    'Portugal': 'PT',
    'Romania': 'RO',
    'Slovakia': 'SK',
    'Slovenia': 'SI',
    'Spain': 'ES',
    'Sweden': 'SE'
  };
  
  // Normalize the country name to handle case sensitivity and whitespace
  const normalizedName = countryName?.trim();
  const countryCode = countryCodes[normalizedName];
  
  // If we can't find the country code, return a fallback instead of the full name
  if (countryCode) {
    return countryCode;
  }
  
  // For unknown countries, return a generic code or the first 2 letters uppercase
  return normalizedName?.substring(0, 2).toUpperCase() || 'XX';
}

/**
 * Convert country code to flag emoji
 * @param {string} iso2 - 2-letter ISO country code
 * @returns {string} Flag emoji string
 */
export function countryToFlag(iso2) {
  if (!iso2) return '';
  return iso2.toUpperCase().replace(/./g, char => 
    String.fromCodePoint(char.charCodeAt(0) + 127397)
  );
}

/**
 * Detect mobile device characteristics for optimization
 * @returns {object} Mobile device information
 */
function getMobileDeviceInfo() {
  const userAgent = navigator.userAgent;
  const isMobile = /Mobi|Android|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(userAgent);
  const isAndroid = /Android/i.test(userAgent);
  const isIOS = /iPhone|iPad|iPod/i.test(userAgent);
  const isChromeMobile = /Chrome/.test(userAgent) && isMobile && !/Edge|Edg/.test(userAgent);
  const isLowEndDevice = navigator.deviceMemory && navigator.deviceMemory <= 2;
  const isSlowConnection = navigator.connection && (navigator.connection.effectiveType === 'slow-2g' || navigator.connection.effectiveType === '2g');
  
  return {
    isMobile,
    isAndroid,
    isIOS,
    isChromeMobile,
    isLowEndDevice,
    isSlowConnection,
    touchScreen: 'ontouchstart' in window,
    devicePixelRatio: window.devicePixelRatio || 1
  };
}

/**
 * Detect if browser supports flag emoji rendering
 * Uses canvas-based detection to check if flag emojis render as images or fallback text
 * Enhanced with Chrome mobile-specific detection and performance optimizations
 * @returns {boolean} True if flag emojis are supported
 */
export function detectFlagEmojiSupport() {
  // Cache the result to avoid repeated DOM manipulation
  if (detectFlagEmojiSupport._cached !== undefined) {
    return detectFlagEmojiSupport._cached;
  }
  
  try {
    const deviceInfo = getMobileDeviceInfo();
    
    // Mobile-specific early detection optimizations
    if (deviceInfo.isMobile) {
      // Chrome mobile on Android has specific emoji rendering challenges
      if (deviceInfo.isChromeMobile && deviceInfo.isAndroid) {
        // Android Chrome versions vary significantly in emoji support
        const chromeVersion = navigator.userAgent.match(/Chrome\/(\d+)/);
        if (chromeVersion && parseInt(chromeVersion[1]) < 90) {
          // Older Chrome versions on Android have poor flag emoji support
          detectFlagEmojiSupport._cached = false;
          return false;
        }
      }
      
      // iOS devices generally have good emoji support
      if (deviceInfo.isIOS) {
        detectFlagEmojiSupport._cached = true;
        return true;
      }
      
      // Skip expensive canvas detection on low-end devices or slow connections
      if (deviceInfo.isLowEndDevice || deviceInfo.isSlowConnection) {
        detectFlagEmojiSupport._cached = false;
        return false;
      }
    }
    
    // Canvas size optimization for mobile devices
    const canvasSize = deviceInfo.isMobile ? 12 : 16;
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d', { willReadFrequently: true });
    canvas.width = canvasSize;
    canvas.height = canvasSize;
    
    // Mobile-optimized font stack for better performance
    ctx.textBaseline = 'top';
    if (deviceInfo.isChromeMobile) {
      // Chrome mobile optimized font stack with Noto Color Emoji priority
      ctx.font = `${canvasSize}px "Noto Color Emoji", "Apple Color Emoji", "Segoe UI Emoji", "Twemoji Mozilla", sans-serif`;
    } else {
      // Standard font stack for other browsers
      ctx.font = `${canvasSize}px "Apple Color Emoji", "Segoe UI Emoji", "Noto Color Emoji", "Twemoji Mozilla", sans-serif`;
    }
    
    // Test with US flag emoji for better color detection 🇺🇸 
    const usFlag = countryToFlag('US');
    
    // Clear canvas and set white background for better contrast detection
    ctx.fillStyle = 'white';
    ctx.fillRect(0, 0, canvasSize, canvasSize);
    
    // Draw flag emoji with black color to ensure visibility
    ctx.fillStyle = 'black';
    ctx.fillText(usFlag, 0, 0);
    const flagData = ctx.getImageData(0, 0, canvasSize, canvasSize).data;
    
    // Clear canvas and draw fallback text for comparison
    ctx.fillStyle = 'white';
    ctx.fillRect(0, 0, canvasSize, canvasSize);
    ctx.fillStyle = 'black';
    ctx.fillText('US', 0, 0);
    const textData = ctx.getImageData(0, 0, canvasSize, canvasSize).data;
    
    // Enhanced color detection - look for any colored pixels in flag rendering
    let flagHasColor = false;
    let textHasColor = false;
    
    // Mobile-optimized pixel analysis with reduced iterations for performance
    const stepSize = deviceInfo.isMobile ? 8 : 4; // Skip more pixels on mobile for performance
    
    // Check for non-grayscale pixels (indicates emoji rendering)
    for (let i = 0; i < flagData.length; i += stepSize) {
      const r = flagData[i];
      const g = flagData[i + 1]; 
      const b = flagData[i + 2];
      const a = flagData[i + 3];
      
      // If pixel is not transparent and has color variation, it's likely an emoji
      if (a > 0 && (r !== g || g !== b)) {
        flagHasColor = true;
        break;
      }
    }
    
    // Check text rendering for comparison
    for (let i = 0; i < textData.length; i += stepSize) {
      const r = textData[i];
      const g = textData[i + 1];
      const b = textData[i + 2];
      const a = textData[i + 3];
      
      if (a > 0 && (r !== g || g !== b)) {
        textHasColor = true;
        break;
      }
    }
    
    // Browser and platform specific checks
    const isChrome = /Chrome/.test(navigator.userAgent) && !/Edge|Edg/.test(navigator.userAgent);
    const isWindows = /Windows/.test(navigator.userAgent);
    
    // Chrome mobile-specific enhanced detection
    if (deviceInfo.isChromeMobile) {
      // More lenient detection for Chrome mobile since it has better emoji support than desktop
      let differentPixels = 0;
      for (let i = 0; i < Math.min(flagData.length, textData.length); i += 4) {
        if (Math.abs(flagData[i] - textData[i]) > 5) { // Lower threshold for mobile
          differentPixels++;
        }
      }
      
      const differenceRatio = differentPixels / (flagData.length / 4);
      const flagSupported = flagHasColor && (differenceRatio > 0.05); // Lower threshold for mobile
      
      detectFlagEmojiSupport._cached = flagSupported;
      return flagSupported;
    }
    
    // Chrome on Windows desktop is particularly problematic with flags
    if (isChrome && isWindows && !deviceInfo.isMobile) {
      // More rigorous test - check if rendering produces significantly different output
      let differentPixels = 0;
      for (let i = 0; i < Math.min(flagData.length, textData.length); i++) {
        if (Math.abs(flagData[i] - textData[i]) > 10) {
          differentPixels++;
        }
      }
      
      // If less than 10% of pixels are different, likely no emoji support
      const differenceRatio = differentPixels / (flagData.length);
      const flagSupported = flagHasColor && (differenceRatio > 0.1);
      
      detectFlagEmojiSupport._cached = flagSupported;
      return flagSupported;
    }
    
    // For other browsers, use color detection
    const flagSupported = flagHasColor && !textHasColor;
    
    detectFlagEmojiSupport._cached = flagSupported;
    return flagSupported;
  } catch (error) {
    // Fallback: assume no support if detection fails
    detectFlagEmojiSupport._cached = false;
    return false;
  }
}

/**
 * Initialize flag emoji polyfill for browsers that need it
 * Enhanced with Chrome mobile-specific optimizations and mobile performance improvements
 * Implements bandwidth-aware loading and mobile viewport optimizations
 * Only loads the font if flag emoji support is not detected
 */
export function initFlagEmojiPolyfill() {
  // Check if polyfill is already loaded
  if (document.getElementById('flag-emoji-polyfill')) {
    return;
  }
  
  // Only load polyfill if flag emojis are not supported
  if (detectFlagEmojiSupport()) {
    return;
  }
  
  const deviceInfo = getMobileDeviceInfo();
  const isChrome = /Chrome/.test(navigator.userAgent) && !/Edge|Edg/.test(navigator.userAgent);
  const isWindows = /Windows/.test(navigator.userAgent);
  const isFirefox = /Firefox/.test(navigator.userAgent);
  
  // Mobile performance optimization - skip polyfill on very low-end devices or slow connections
  if (deviceInfo.isMobile && (deviceInfo.isLowEndDevice || deviceInfo.isSlowConnection)) {
    return;
  }
  
  // Create and inject CSS for flag emoji fallback
  const style = document.createElement('style');
  style.id = 'flag-emoji-polyfill';
  
  // Mobile-optimized font loading strategy
  let fontSrc = 'https://cdn.jsdelivr.net/npm/country-flag-emoji-polyfill@0.1/dist/TwemojiCountryFlags.woff2';
  let fontDisplay = deviceInfo.isMobile ? 'optional' : 'swap'; // Use optional on mobile to prevent layout shifts
  
  // Base CSS with mobile-optimized font loading
  let cssContent = `
    /* Flag Emoji Polyfill - Enhanced for mobile and cross-browser compatibility */
    @font-face {
      font-family: "Twemoji Country Flags";
      src: url("${fontSrc}") format("woff2");
      unicode-range: U+1F1E6-1F1FF;
      font-display: ${fontDisplay};
      font-weight: normal;
      font-style: normal;
    }
  `;
  
  // Chrome mobile-specific optimizations
  if (deviceInfo.isChromeMobile) {
    cssContent += `
    /* Chrome Mobile-specific flag emoji enhancements */
    .flag-emoji-enhanced {
      font-family: "Twemoji Country Flags", "Noto Color Emoji", "Apple Color Emoji", "Segoe UI Emoji", monospace, sans-serif;
      font-variant-emoji: emoji;
      text-rendering: optimizeSpeed; /* Chrome mobile performs better with optimizeSpeed */
      -webkit-font-feature-settings: "liga" on, "kern" on;
      font-feature-settings: "liga" on, "kern" on;
      font-synthesis: none;
      -webkit-font-smoothing: antialiased;
      -webkit-text-size-adjust: 100%; /* Prevent mobile zoom on small text */
      /* Mobile-optimized hardware acceleration */
      will-change: auto;
      transform: translateZ(0);
      /* Touch-friendly sizing */
      min-height: ${deviceInfo.touchScreen ? '24px' : '16px'};
      /* High DPI optimization */
      ${deviceInfo.devicePixelRatio > 2 ? 'image-rendering: -webkit-optimize-contrast;' : ''}
    }
    
    /* Android Chrome specific fixes */
    ${deviceInfo.isAndroid ? `
    .flag-emoji-enhanced {
      /* Android Chrome needs explicit sizing for consistent rendering */
      display: inline-block;
      vertical-align: middle;
      line-height: 1;
      /* Ensure font loads on Android Chrome */
      font-family: "Twemoji Country Flags", "Noto Color Emoji", monospace !important;
      /* Prevent text selection issues on Android */
      -webkit-user-select: none;
      user-select: none;
    }
    ` : ''}
    
    /* Touch device optimizations */
    ${deviceInfo.touchScreen ? `
    .flag-emoji-enhanced {
      /* Larger touch targets for accessibility */
      padding: 2px;
      /* Prevent touch highlights */
      -webkit-tap-highlight-color: transparent;
      /* Smooth scrolling performance */
      backface-visibility: hidden;
    }
    ` : ''}
    `;
  } else if (isChrome && !deviceInfo.isMobile) {
    // Desktop Chrome optimizations (keep existing)
    cssContent += `
    /* Chrome Desktop-specific flag emoji enhancements */
    .flag-emoji-enhanced {
      font-family: "Twemoji Country Flags", "Apple Color Emoji", "Noto Color Emoji", "Segoe UI Emoji", "Twemoji Mozilla", monospace, sans-serif;
      font-variant-emoji: emoji;
      text-rendering: optimizeSpeed;
      -webkit-font-feature-settings: "liga" on, "clig" on, "kern" on;
      font-feature-settings: "liga" on, "clig" on, "kern" on;
      font-synthesis: none;
      -webkit-font-smoothing: antialiased;
      -moz-osx-font-smoothing: grayscale;
      will-change: auto;
      transform: translateZ(0);
    }
    
    /* Chrome Windows specific fixes */
    ${isWindows ? `
    .flag-emoji-enhanced {
      display: inline-block;
      vertical-align: baseline;
      line-height: 1.2;
      font-family: "Twemoji Country Flags", monospace !important;
    }
    ` : ''}
    `;
  } else if (isFirefox) {
    // Firefox-specific optimizations (keep existing)
    cssContent += `
    /* Firefox-specific flag emoji enhancements */
    .flag-emoji-enhanced {
      font-family: "Twemoji Country Flags", "Apple Color Emoji", "Segoe UI Emoji", "Noto Color Emoji", "Twitter Color Emoji", sans-serif;
      font-variant-emoji: emoji;
      text-rendering: optimizeLegibility;
    }
    
    @-moz-document url-prefix() {
      .flag-emoji-enhanced {
        font-feature-settings: "liga" on, "clig" on;
      }
    }
    `;
  } else {
    // Generic browser fallback
    cssContent += `
    /* Generic browser flag emoji support */
    .flag-emoji-enhanced {
      font-family: "Twemoji Country Flags", "Apple Color Emoji", "Segoe UI Emoji", "Noto Color Emoji", "Twitter Color Emoji", sans-serif;
      font-variant-emoji: emoji;
      text-rendering: optimizeLegibility;
    }
    `;
  }
  
  // Mobile-optimized performance enhancements
  cssContent += `
    /* Mobile-optimized performance enhancements */
    .flag-emoji-enhanced {
      /* Bandwidth-friendly font loading */
      font-display: ${fontDisplay};
      /* Optimize for emoji content */
      font-variant-numeric: normal;
      font-variant-ligatures: common-ligatures;
      /* Mobile scroll performance */
      ${deviceInfo.isMobile ? 'will-change: auto; contain: layout style;' : ''}
    }
    
    /* Mobile viewport-aware sizing */
    .country-flag.flag-emoji-enhanced {
      /* Prevent layout shifts during font load */
      width: ${deviceInfo.isMobile ? '1.5em' : '1.25em'};
      height: ${deviceInfo.isMobile ? '1.2em' : '1em'};
      display: inline-block;
      vertical-align: ${deviceInfo.isMobile ? 'middle' : '-0.1em'};
      text-align: center;
      /* Mobile touch optimization */
      ${deviceInfo.touchScreen ? 'min-width: 20px; min-height: 16px;' : ''}
    }
    
    /* High DPI mobile optimization */
    ${deviceInfo.devicePixelRatio > 2 ? `
    @media (-webkit-min-device-pixel-ratio: 2), (min-resolution: 192dpi) {
      .flag-emoji-enhanced {
        /* Crisp rendering on high DPI displays */
        image-rendering: -webkit-optimize-contrast;
        image-rendering: crisp-edges;
      }
    }
    ` : ''}
    
    /* Loading state optimizations */
    @supports (font-display: ${fontDisplay}) {
      .flag-emoji-enhanced {
        font-display: ${fontDisplay};
      }
    }
    
    /* Chrome mobile-specific badge fallback styling */
    ${deviceInfo.isChromeMobile ? `
    .chrome-mobile-badge-fallback {
      background: linear-gradient(135deg, #4285f4 0%, #34a853 100%);
      color: white;
      font-weight: bold;
      border-radius: 3px;
      padding: 1px 3px;
      font-size: 0.75em;
      text-shadow: 0 1px 2px rgba(0,0,0,0.3);
      box-shadow: 0 1px 3px rgba(0,0,0,0.2);
    }
    ` : ''}
  `;
  
  style.textContent = cssContent;
  document.head.appendChild(style);
  
  // Enhanced logging with mobile device info
  const browserInfo = deviceInfo.isChromeMobile ? 'Chrome Mobile' : 
                     isChrome ? 'Chrome Desktop' : 
                     isFirefox ? 'Firefox' : 'Unknown';
  const platformInfo = deviceInfo.isAndroid ? 'Android' : 
                      deviceInfo.isIOS ? 'iOS' : 
                      isWindows ? 'Windows' : 'Other OS';
  const deviceInfo_str = deviceInfo.isMobile ? 
    `Mobile (${deviceInfo.isLowEndDevice ? 'Low-end' : 'Standard'} device, ${deviceInfo.isSlowConnection ? 'slow' : 'fast'} connection)` : 
    'Desktop';
    
  
  // Mobile-optimized preload strategy
  if (isChrome && !deviceInfo.isSlowConnection) {
    // Only preload on fast connections to save bandwidth
    const preloadLink = document.createElement('link');
    preloadLink.rel = 'preload';
    preloadLink.href = fontSrc;
    preloadLink.as = 'font';
    preloadLink.type = 'font/woff2';
    preloadLink.crossOrigin = 'anonymous';
    
    // Add importance hint for mobile
    if (deviceInfo.isMobile) {
      preloadLink.setAttribute('importance', 'low');
    }
    
    // Add error handling for font loading
    preloadLink.onerror = () => {
      console.warn('Primary Twemoji font failed to load, flags will fall back to country code badges');
    };
    
    document.head.appendChild(preloadLink);
  }
}

/**
 * Create country display HTML with robust cross-browser flag emoji support
 * Enhanced with Chrome mobile-specific optimizations and mobile performance improvements
 * Implements smart fallback system: flag emoji -> mobile badge -> standard badge -> text
 * Includes mobile viewport optimizations and touch-friendly interfaces
 * 
 * @param {string} countryName - Full country name
 * @param {object} options - Display options
 * @param {string} options.size - Display size ('small', 'medium', 'large')
 * @param {boolean} options.showText - Show country name text
 * @param {boolean} options.showCode - Show country code text
 * @param {string} options.className - Additional CSS classes
 * @param {boolean} options.forceBadge - Force badge display instead of emoji
 * @param {boolean} options.enableFallback - Enable automatic fallback detection (default: true)
 * @param {boolean} options.optimizeForMobile - Enable mobile-specific optimizations (default: auto-detect)
 * @returns {string} HTML string for country display
 */
export function createCountryDisplay(countryName, options = {}) {
  try {
    const { 
      size = 'medium', 
      showText = false, 
      showCode = false, 
      className = '', 
      forceBadge = false,
      enableFallback = true,
      optimizeForMobile = null // Auto-detect if null
    } = options;
    
    // Input validation and error handling
    if (!countryName || typeof countryName !== 'string') {
      console.warn('createCountryDisplay: Invalid country name provided:', countryName);
      return `<span class="country-display-error ${className}">Unknown</span>`;
    }
    
    const countryCode = getCountryCode(countryName);
    if (!countryCode) {
      console.warn('createCountryDisplay: Could not resolve country code for:', countryName);
      return `<span class="country-display-error ${className}">${countryName}</span>`;
    }
    
    const flag = countryToFlag(countryCode);
    const deviceInfo = getMobileDeviceInfo();
    const isMobileOptimized = optimizeForMobile !== null ? optimizeForMobile : deviceInfo.isMobile;
    
    // Initialize polyfill with error handling
    try {
      initFlagEmojiPolyfill();
    } catch (polyfillError) {
      console.warn('createCountryDisplay: Polyfill initialization failed:', polyfillError);
    }
    
    // Browser detection for optimizations
    const isChrome = /Chrome/.test(navigator.userAgent) && !/Edge|Edg/.test(navigator.userAgent);
    const isWindows = /Windows/.test(navigator.userAgent);
    const isFirefox = /Firefox/.test(navigator.userAgent);
    
    // Simplified approach: Try flag emojis first, fall back to badges only if forced or on very limited devices
    const isVeryLowEnd = deviceInfo.isMobile && deviceInfo.isLowEndDevice && deviceInfo.isSlowConnection;
    const shouldUseBadge = forceBadge || isVeryLowEnd;
    
    // Mobile-optimized size configurations
    const mobileAdjustment = isMobileOptimized ? 1.2 : 1; // 20% larger on mobile for touch accessibility
    
    // Badge configurations with mobile optimization
    const badgeClasses = {
      small: isMobileOptimized ? 'w-7 h-5 text-xs' : 'w-6 h-4 text-xs',
      medium: isMobileOptimized ? 'w-8 h-6 text-sm' : 'w-7 h-5 text-xs', 
      large: isMobileOptimized ? 'w-10 h-7 text-base' : 'w-8 h-6 text-sm'
    }[size] || (isMobileOptimized ? 'w-8 h-6 text-sm' : 'w-7 h-5 text-xs');
    
    // Emoji size configurations with mobile and high-DPI optimization
    const baseEmojiSizes = {
      small: 0.875,   // 14px base
      medium: 1,      // 16px base
      large: 1.25     // 20px base
    }[size] || 1;
    
    const emojiSize = baseEmojiSizes * mobileAdjustment * (deviceInfo.devicePixelRatio > 2 ? 1.1 : 1);
    const emojiSizeStr = `${emojiSize}rem`;
    
    // Prepare optional text elements with XSS protection and mobile optimization
    const codeTextNeeded = showText || showCode;
    const textToShow = showText ? countryName : countryCode;
    const safeTextToShow = textToShow.replace(/[<>&"']/g, (match) => {
      const escapeMap = { '<': '&lt;', '>': '&gt;', '&': '&amp;', '"': '&quot;', "'": '&#39;' };
      return escapeMap[match];
    });
    
    // Use flex gap instead of margin-left for consistent spacing
    const textClasses = isMobileOptimized ? 'text-gray-700 text-sm' : 'text-gray-700';
    const codeSpan = codeTextNeeded ? `<span class="${textClasses}">${safeTextToShow}</span>` : '';
    
    if (shouldUseBadge) {
      // Fallback: Use styled country code badges with mobile optimizations
      let badgeExtraClasses = isChrome ? 'chrome-optimized-badge' : '';
      let badgeStyle = '';
      
      // Chrome mobile-specific badge styling
      if (deviceInfo.isChromeMobile) {
        badgeExtraClasses += ' chrome-mobile-badge-fallback';
        // Add touch-friendly styling
        badgeStyle = 'min-height: 24px; cursor: default;';
      }
      
      // Touch device optimization
      if (deviceInfo.touchScreen) {
        badgeExtraClasses += ' touch-optimized';
        badgeStyle += ' -webkit-tap-highlight-color: transparent;';
      }
      
      const badgeBaseClasses = isMobileOptimized ? 
        'bg-blue-600 text-white font-bold rounded-md shadow-md transition-colors hover:bg-blue-700 active:bg-blue-800' :
        'bg-blue-600 text-white font-bold rounded shadow-sm transition-colors hover:bg-blue-700';
      
      return `
        <div class="country-display inline-flex items-center ${className}" 
             title="${countryName}" 
             data-country="${countryCode}" 
             data-fallback="badge"
             data-mobile-optimized="${isMobileOptimized}">
          <span class="inline-flex items-center justify-center ${badgeClasses} ${badgeExtraClasses} ${badgeBaseClasses}"
                style="${badgeStyle}"
                role="img"
                aria-label="${countryName}">${countryCode}</span>
          ${codeSpan}
        </div>
      `.trim();
    } else {
      // Primary: Use flag emoji with mobile-specific optimizations
      let flagClasses = 'country-flag flag-emoji-enhanced';
      let flagStyles = `font-family: "Twemoji Country Flags", "Apple Color Emoji", "Segoe UI Emoji", "Noto Color Emoji", sans-serif; font-size: ${emojiSizeStr}; line-height: 1; display: inline-block;`;
      
      // Chrome mobile-specific enhancements
      if (deviceInfo.isChromeMobile) {
        flagClasses += ' chrome-mobile-flag-emoji';
        flagStyles += ' text-rendering: optimizeSpeed; -webkit-font-smoothing: antialiased;';
        flagStyles += ' -webkit-text-size-adjust: 100%;'; // Prevent mobile zoom
        
        // Android-specific adjustments
        if (deviceInfo.isAndroid) {
          flagStyles += ' vertical-align: middle;';
          flagClasses += ' android-flag-emoji';
        }
        
        // Touch device optimizations
        if (deviceInfo.touchScreen) {
          flagStyles += ' -webkit-tap-highlight-color: transparent; user-select: none;';
          flagClasses += ' touch-optimized';
        }
        
        // High DPI optimizations
        if (deviceInfo.devicePixelRatio > 2) {
          flagStyles += ' image-rendering: -webkit-optimize-contrast;';
        }
      } else if (isChrome && !deviceInfo.isMobile) {
        // Desktop Chrome optimizations
        flagClasses += ' chrome-flag-emoji';
        flagStyles += ' text-rendering: optimizeSpeed; -webkit-font-smoothing: antialiased;';
        
        // Windows Chrome specific adjustments
        if (isWindows) {
          flagStyles += ' vertical-align: baseline; width: 1.25em; height: 1em;';
        }
      }
      
      // Firefox-specific enhancements (unchanged)
      if (isFirefox) {
        flagClasses += ' firefox-flag-emoji';
        flagStyles += ' text-rendering: optimizeLegibility;';
      }
      
      // Mobile viewport optimizations
      if (isMobileOptimized) {
        flagStyles += ' width: auto; height: auto; max-width: none; max-height: none;';
        
        // Ensure minimum touch target size for accessibility
        if (deviceInfo.touchScreen) {
          flagStyles += ' min-width: 20px; min-height: 16px; padding: 2px;';
        }
      }
      
      return `
        <div class="country-display inline-flex items-center ${className}" 
             title="${countryName}" 
             data-country="${countryCode}" 
             data-fallback="emoji"
             data-mobile-optimized="${isMobileOptimized}">
          <span class="${flagClasses}" 
                style="${flagStyles}" 
                role="img" 
                aria-label="${countryName} flag"
                data-emoji="${flag}">${flag}</span>
          ${codeSpan}
        </div>
      `.trim();
    }
  } catch (error) {
    console.error('createCountryDisplay: Unexpected error:', error);
    // Ultimate fallback - just return the country code as text
    return `<span class="country-display-error ${options.className || ''}" title="Error displaying ${countryName}">${getCountryCode(countryName) || countryName}</span>`;
  }
}

/**
 * Validate flag emoji rendering after DOM insertion
 * Enhanced with Chrome mobile-specific validation and performance optimization
 * @param {Element} element - DOM element containing flag emoji
 * @returns {boolean} True if flag appears to be rendering correctly
 */
export function validateFlagEmojiRendering(element) {
  try {
    const flagSpan = element.querySelector('.flag-emoji-enhanced');
    if (!flagSpan) return false;
    
    const deviceInfo = getMobileDeviceInfo();
    
    // Mobile-optimized dimension validation
    const rect = flagSpan.getBoundingClientRect();
    const minDimension = deviceInfo.isMobile ? 8 : 10; // More lenient on mobile
    
    if (rect.width < minDimension || rect.height < minDimension) {
      console.warn('Flag emoji appears to have invalid dimensions:', rect);
      return false;
    }
    
    // Chrome mobile-specific validation
    if (deviceInfo.isChromeMobile) {
      // Check if element is visible and properly rendered on mobile
      const computedStyle = window.getComputedStyle(flagSpan);
      const fontFamily = computedStyle.fontFamily;
      
      // More lenient font family check for Chrome mobile
      if (!fontFamily.includes('Twemoji Country Flags') && 
          !fontFamily.includes('Noto Color Emoji') && 
          !fontFamily.includes('Apple Color Emoji')) {
        console.warn('Flag emoji polyfill font may not have loaded properly on Chrome mobile:', fontFamily);
        return false;
      }
      
      // Check if emoji is actually visible (not display: none or opacity: 0)
      if (computedStyle.display === 'none' || computedStyle.opacity === '0' || computedStyle.visibility === 'hidden') {
        console.warn('Flag emoji element is not visible on Chrome mobile');
        return false;
      }
      
      return true;
    }
    
    // Desktop Chrome-specific checks
    const isChrome = /Chrome/.test(navigator.userAgent) && !/Edge|Edg/.test(navigator.userAgent);
    if (isChrome && !deviceInfo.isMobile) {
      // Check computed font family to ensure polyfill font loaded
      const computedStyle = window.getComputedStyle(flagSpan);
      const fontFamily = computedStyle.fontFamily;
      
      if (!fontFamily.includes('Twemoji Country Flags') && !fontFamily.includes('Apple Color Emoji')) {
        console.warn('Flag emoji polyfill font may not have loaded properly:', fontFamily);
        return false;
      }
    }
    
    return true;
  } catch (error) {
    console.warn('Flag emoji validation failed:', error);
    return false;
  }
}

/**
 * Initialize mobile-specific flag emoji optimizations
 * Applies Chrome mobile-specific fixes and performance enhancements
 * Should be called after DOM is ready
 */
export function initMobileFlagOptimizations() {
  const deviceInfo = getMobileDeviceInfo();
  
  if (!deviceInfo.isMobile) {
    return; // Skip on desktop
  }
  
  
  // Apply mobile-specific CSS classes to flag displays
  const flagElements = document.querySelectorAll('.country-display');
  
  flagElements.forEach(element => {
    if (deviceInfo.isChromeMobile) {
      element.classList.add('chrome-mobile-optimized');
    }
    
    if (deviceInfo.touchScreen) {
      element.classList.add('touch-device');
    }
    
    if (deviceInfo.isLowEndDevice) {
      element.classList.add('low-end-device');
    }
  });
  
  // Chrome mobile-specific performance optimizations
  if (deviceInfo.isChromeMobile) {
    // Add viewport meta tag optimization for better emoji rendering
    let viewportMeta = document.querySelector('meta[name=\"viewport\"]');
    if (viewportMeta) {
      const content = viewportMeta.getAttribute('content');
      if (!content.includes('user-scalable=no')) {
        // Prevent zoom issues with emoji on Chrome mobile
        viewportMeta.setAttribute('content', content + ', user-scalable=no');
      }
    }
    
    // Preload Noto Color Emoji if not already loaded for Chrome mobile
    if (!document.querySelector('link[href*=\"noto-emoji\"]') && !deviceInfo.isSlowConnection) {
      const preloadLink = document.createElement('link');
      preloadLink.rel = 'preconnect';
      preloadLink.href = 'https://fonts.gstatic.com';
      preloadLink.crossOrigin = 'anonymous';
      document.head.appendChild(preloadLink);
    }
    
  }
}