// Test setup file for Vitest
import '@testing-library/jest-dom';
import Modal from 'react-modal';

// Mock react-modal for tests
if (typeof document !== 'undefined') {
  // Create a root element for tests
  const rootDiv = document.createElement('div');
  rootDiv.id = 'root';
  document.body.appendChild(rootDiv);
  
  // Set Modal app element
  Modal.setAppElement('#root');
}
