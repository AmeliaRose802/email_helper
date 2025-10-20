// Main entry point for Email Helper React app
import { createRoot } from 'react-dom/client';
import App from './App';
import './styles/unified.css';

// CRITICAL: Catch all errors to prevent JavaScript from breaking
window.addEventListener('error', (event) => {
  console.error('========== GLOBAL ERROR CAUGHT ==========');
  console.error('Message:', event.message);
  console.error('Filename:', event.filename);
  console.error('Line:', event.lineno, 'Col:', event.colno);
  console.error('Error object:', event.error);
  event.preventDefault(); // Prevent the error from breaking everything
  return true;
});

window.addEventListener('unhandledrejection', (event) => {
  console.error('========== UNHANDLED PROMISE REJECTION ==========');
  console.error('Reason:', event.reason);
  event.preventDefault();
});

const rootElement = document.getElementById('root');
if (!rootElement) {
  console.error('❌ Root element not found!');
  throw new Error('Root element not found');
}

try {
  const root = createRoot(rootElement);
  
  // Temporarily disable StrictMode to check if it's causing issues
  root.render(<App />);
  
  // Signal to Electron that React is fully ready
  setTimeout(() => {
    window.dispatchEvent(new Event('react-ready'));
  }, 100);
} catch (error) {
  console.error('❌ Error rendering app:', error);
  rootElement.innerHTML = `
    <div style="padding: 40px; text-align: center; font-family: Arial;">
      <h1 style="color: red;">❌ React Failed to Load</h1>
      <p>Error: ${error instanceof Error ? error.message : String(error)}</p>
      <pre style="text-align: left; background: #f0f0f0; padding: 20px; border-radius: 8px;">
${error instanceof Error ? error.stack : ''}
      </pre>
    </div>
  `;
}
