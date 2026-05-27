/** @type {import('tailwindcss').Config} */
module.exports = {
    darkMode: ["class"],
    content: [
    "./src/**/*.{js,jsx,ts,tsx}",
    "./public/index.html"
  ],
  theme: {
  	extend: {
  		borderRadius: {
  			lg: 'var(--radius)',
  			md: 'calc(var(--radius) - 2px)',
  			sm: 'calc(var(--radius) - 4px)'
  		},
  		colors: {
  			background: 'hsl(var(--background))',
  			foreground: 'hsl(var(--foreground))',
  			card: {
  				DEFAULT: 'hsl(var(--card))',
  				foreground: 'hsl(var(--card-foreground))'
  			},
  			popover: {
  				DEFAULT: 'hsl(var(--popover))',
  				foreground: 'hsl(var(--popover-foreground))'
  			},
  			primary: {
  				DEFAULT: 'hsl(var(--primary))',
  				foreground: 'hsl(var(--primary-foreground))'
  			},
  			secondary: {
  				DEFAULT: 'hsl(var(--secondary))',
  				foreground: 'hsl(var(--secondary-foreground))'
  			},
  			muted: {
  				DEFAULT: 'hsl(var(--muted))',
  				foreground: 'hsl(var(--muted-foreground))'
  			},
  			accent: {
  				DEFAULT: 'hsl(var(--accent))',
  				foreground: 'hsl(var(--accent-foreground))'
  			},
  			destructive: {
  				DEFAULT: 'hsl(var(--destructive))',
  				foreground: 'hsl(var(--destructive-foreground))'
  			},
  			border: 'hsl(var(--border))',
  			input: 'hsl(var(--input))',
  			ring: 'hsl(var(--ring))',
  			chart: {
  				'1': 'hsl(var(--chart-1))',
  				'2': 'hsl(var(--chart-2))',
  				'3': 'hsl(var(--chart-3))',
  				'4': 'hsl(var(--chart-4))',
  				'5': 'hsl(var(--chart-5))'
  			}
  		},
  		keyframes: {
  			'accordion-down': {
  				from: { height: '0' },
  				to: { height: 'var(--radix-accordion-content-height)' }
  			},
  			'accordion-up': {
  				from: { height: 'var(--radix-accordion-content-height)' },
  				to: { height: '0' }
  			},
  			// ── Battlefield condition card animations ──────────────────────
  			'card-enter': {
  				'0%':   { opacity: '0', transform: 'translateY(16px) scale(0.95)' },
  				'60%':  { opacity: '1', transform: 'translateY(-3px) scale(1.02)' },
  				'100%': { opacity: '1', transform: 'translateY(0) scale(1)' }
  			},
  			'card-float': {
  				'0%, 100%': { transform: 'translateY(0px)' },
  				'50%':      { transform: 'translateY(-4px)' }
  			},
  			'shimmer': {
  				'0%':   { backgroundPosition: '-400px 0' },
  				'100%': { backgroundPosition: '400px 0' }
  			},
  			'glow-common': {
  				'0%, 100%': { boxShadow: '0 0 6px 1px rgba(148,163,184,0.15)' },
  				'50%':      { boxShadow: '0 0 14px 3px rgba(148,163,184,0.30)' }
  			},
  			'glow-uncommon': {
  				'0%, 100%': { boxShadow: '0 0 6px 1px rgba(52,211,153,0.20)' },
  				'50%':      { boxShadow: '0 0 18px 4px rgba(52,211,153,0.45)' }
  			},
  			'glow-rare': {
  				'0%, 100%': { boxShadow: '0 0 8px 2px rgba(96,165,250,0.25)' },
  				'50%':      { boxShadow: '0 0 22px 5px rgba(96,165,250,0.55)' }
  			},
  			'glow-epic': {
  				'0%, 100%': { boxShadow: '0 0 10px 3px rgba(167,139,250,0.30)' },
  				'50%':      { boxShadow: '0 0 28px 7px rgba(167,139,250,0.65)' }
  			},
  			'border-flow': {
  				'0%, 100%': { backgroundPosition: '0% 50%' },
  				'50%':      { backgroundPosition: '100% 50%' }
  			},
  			'dice-tumble': {
  				'0%':   { transform: 'rotate(0deg) scale(1)' },
  				'20%':  { transform: 'rotate(72deg) scale(1.15)' },
  				'40%':  { transform: 'rotate(144deg) scale(0.9)' },
  				'60%':  { transform: 'rotate(216deg) scale(1.1)' },
  				'80%':  { transform: 'rotate(288deg) scale(0.95)' },
  				'100%': { transform: 'rotate(360deg) scale(1)' }
  			},
  			'result-slide': {
  				'0%':   { opacity: '0', transform: 'translateY(12px)' },
  				'100%': { opacity: '1', transform: 'translateY(0)' }
  			},
  			'outcome-flash-bonus': {
  				'0%':   { boxShadow: '0 0 0 0 rgba(251,191,36,0)' },
  				'30%':  { boxShadow: '0 0 0 8px rgba(251,191,36,0.4)' },
  				'100%': { boxShadow: '0 0 0 0 rgba(251,191,36,0)' }
  			},
  			'outcome-flash-penalty': {
  				'0%':   { boxShadow: '0 0 0 0 rgba(239,68,68,0)' },
  				'30%':  { boxShadow: '0 0 0 8px rgba(239,68,68,0.4)' },
  				'100%': { boxShadow: '0 0 0 0 rgba(239,68,68,0)' }
  			},
  			'art-reveal': {
  				'0%':   { opacity: '0', filter: 'blur(8px) saturate(0)' },
  				'60%':  { opacity: '0.8', filter: 'blur(2px) saturate(0.6)' },
  				'100%': { opacity: '1', filter: 'blur(0) saturate(1)' }
  			}
  		},
  		animation: {
  			'accordion-down':      'accordion-down 0.2s ease-out',
  			'accordion-up':        'accordion-up 0.2s ease-out',
  			'card-enter':          'card-enter 0.45s cubic-bezier(0.34,1.56,0.64,1) both',
  			'card-float':          'card-float 3s ease-in-out infinite',
  			'shimmer':             'shimmer 1.5s linear infinite',
  			'glow-common':         'glow-common 2.5s ease-in-out infinite',
  			'glow-uncommon':       'glow-uncommon 2.2s ease-in-out infinite',
  			'glow-rare':           'glow-rare 2s ease-in-out infinite',
  			'glow-epic':           'glow-epic 1.8s ease-in-out infinite',
  			'dice-tumble':         'dice-tumble 0.35s ease-in-out',
  			'result-slide':        'result-slide 0.3s ease-out both',
  			'outcome-flash-bonus': 'outcome-flash-bonus 0.6s ease-out',
  			'outcome-flash-penalty':'outcome-flash-penalty 0.6s ease-out',
  			'art-reveal':          'art-reveal 0.8s ease-out both'
  		}
  	}
  },
  plugins: [require("tailwindcss-animate")],
};