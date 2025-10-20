// Main App component for Email Helper
import React from 'react';
import { Provider } from 'react-redux';
import { store } from '@/store/store';
import AppRouter from '@/router/AppRouter';

const App: React.FC = () => {
  
  try {
    return (
      <Provider store={store}>
        <AppRouter />
      </Provider>
    );
  } catch (error) {
    console.error('❌ Error in App component:', error);
    return (
      <div className="error-container">
        <h1 className="error-container__title">Error Loading App</h1>
        <p>{error instanceof Error ? error.message : String(error)}</p>
      </div>
    );
  }
};

export default App;
