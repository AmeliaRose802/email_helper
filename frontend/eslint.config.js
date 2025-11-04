import js from '@eslint/js'
import globals from 'globals'
import reactHooks from 'eslint-plugin-react-hooks'
import reactRefresh from 'eslint-plugin-react-refresh'
import tseslint from 'typescript-eslint'
import { defineConfig, globalIgnores } from 'eslint/config'

export default defineConfig([
  globalIgnores(['dist']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      js.configs.recommended,
      tseslint.configs.recommended,
      reactHooks.configs['recommended-latest'],
      reactRefresh.configs.vite,
    ],
    languageOptions: {
      ecmaVersion: 2020,
      globals: globals.browser,
    },
    rules: {
      // Forbid inline styles in React components
      // All styling must be in CSS files (frontend/src/styles/unified.css)
      // Exception: truly dynamic values that cannot be expressed in CSS
      'no-restricted-syntax': [
        'warn',
        {
          selector: 'JSXAttribute[name.name="style"]',
          message: 'Inline styles are forbidden. Use CSS classes from unified.css instead. Only use inline styles for truly dynamic values that cannot be expressed in CSS (e.g., calculated widths based on runtime data).',
        },
      ],
    },
  },
])
