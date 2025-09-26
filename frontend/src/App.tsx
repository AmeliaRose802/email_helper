// Main App component for Email Helper
import React from 'react';
import { Provider } from 'react-redux';
import { store } from '@/store/store';
import AppRouter from '@/router/AppRouter';
import '@/styles/index.css';

const App: React.FC = () => {
  return (
    <Provider store={store}>
      <AppRouter />
    </Provider>
  );
};

export default App;
