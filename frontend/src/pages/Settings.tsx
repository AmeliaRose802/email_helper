// Settings page component
import React, { useState, useEffect } from 'react';
import { 
  useGetSettingsQuery, 
  useUpdateSettingsMutation, 
  useResetSettingsMutation,
  type UserSettings
} from '@/services/settingsApi';

interface SettingsData {
  username: string;
  jobContext: string;
  newsletterInterests: string;
  azureOpenAIEndpoint: string;
  azureOpenAIKey: string;
  azureOpenAIDeployment: string;
  customPrompts: {
    [key: string]: string;
  };
  adoAreaPath: string;
  adoPat: string;
}

const defaultSettings: SettingsData = {
  username: '',
  jobContext: '',
  newsletterInterests: '',
  azureOpenAIEndpoint: '',
  azureOpenAIKey: '',
  azureOpenAIDeployment: '',
  customPrompts: {},
  adoAreaPath: '',
  adoPat: '',
};

const CATEGORIES = [
  { id: 'required_personal_action', label: 'Required Personal Action', emoji: '🔴' },
  { id: 'team_action', label: 'Team Action', emoji: '👥' },
  { id: 'optional_action', label: 'Optional Action', emoji: '📋' },
  { id: 'job_listing', label: 'Job Listing', emoji: '💼' },
  { id: 'optional_event', label: 'Optional Event', emoji: '📅' },
  { id: 'work_relevant', label: 'Work Relevant', emoji: '💼' },
  { id: 'fyi', label: 'FYI', emoji: 'ℹ️' },
  { id: 'newsletter', label: 'Newsletter', emoji: '📰' },
  { id: 'spam_to_delete', label: 'Spam', emoji: '🗑️' },
];

const Settings: React.FC = () => {
  const [settings, setSettings] = useState<SettingsData>(defaultSettings);
  const [activeTab, setActiveTab] = useState<'profile' | 'ai' | 'prompts'>('profile');
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle');
  const [showPassword, setShowPassword] = useState(false);

  // Fetch settings from API
  const { data: apiSettings, isLoading } = useGetSettingsQuery();
  const [updateSettings] = useUpdateSettingsMutation();
  const [resetSettingsMutation] = useResetSettingsMutation();

  // Load settings from API response
  useEffect(() => {
    if (apiSettings) {
      setSettings({
        username: apiSettings.username || '',
        jobContext: apiSettings.job_context || '',
        newsletterInterests: apiSettings.newsletter_interests || '',
        azureOpenAIEndpoint: apiSettings.azure_openai_endpoint || '',
        azureOpenAIKey: '', // Don't expose stored keys
        azureOpenAIDeployment: apiSettings.azure_openai_deployment || '',
        customPrompts: apiSettings.custom_prompts || {},
        adoAreaPath: apiSettings.ado_area_path || '',
        adoPat: '', // Don't expose stored PATs
      });
    }
  }, [apiSettings]);

  const handleSave = async () => {
    try {
      setSaveStatus('saving');
      
      // Convert frontend format to API format
      const apiData: UserSettings = {
        username: settings.username || undefined,
        job_context: settings.jobContext || undefined,
        newsletter_interests: settings.newsletterInterests || undefined,
        azure_openai_endpoint: settings.azureOpenAIEndpoint || undefined,
        azure_openai_deployment: settings.azureOpenAIDeployment || undefined,
        custom_prompts: settings.customPrompts,
        ado_area_path: settings.adoAreaPath || undefined,
        ado_pat: settings.adoPat || undefined,
      };
      
      await updateSettings(apiData).unwrap();
      setSaveStatus('saved');
      setTimeout(() => setSaveStatus('idle'), 2000);
    } catch (error) {
      console.error('Failed to save settings:', error);
      setSaveStatus('error');
      setTimeout(() => setSaveStatus('idle'), 2000);
    }
  };

  const handleReset = async () => {
    if (window.confirm('Are you sure you want to reset all settings to default?')) {
      try {
        setSaveStatus('saving');
        await resetSettingsMutation().unwrap();
        setSettings(defaultSettings);
        setSaveStatus('saved');
        setTimeout(() => setSaveStatus('idle'), 2000);
      } catch (error) {
        console.error('Failed to reset settings:', error);
        setSaveStatus('error');
        setTimeout(() => setSaveStatus('idle'), 2000);
      }
    }
  };

  if (isLoading) {
    return (
      <div style={{ padding: '40px', textAlign: 'center' }}>
        <h2>Loading settings...</h2>
      </div>
    );
  }

  return (
    <div className="settings-container">
      <header className="settings-header">
        <h1>⚙️ Settings</h1>
        <p className="settings-subtitle">Configure your Email Helper preferences</p>
      </header>

      {/* Tab Navigation */}
      <div className="settings-tabs">
        <button
          className={`settings-tab ${activeTab === 'profile' ? 'active' : ''}`}
          onClick={() => setActiveTab('profile')}
        >
          👤 User Profile
        </button>
        <button
          className={`settings-tab ${activeTab === 'ai' ? 'active' : ''}`}
          onClick={() => setActiveTab('ai')}
        >
          🤖 AI Configuration
        </button>
        <button
          className={`settings-tab ${activeTab === 'prompts' ? 'active' : ''}`}
          onClick={() => setActiveTab('prompts')}
        >
          📝 Custom Prompts
        </button>
      </div>

      {/* Tab Content */}
      <div className="settings-content">
        {activeTab === 'profile' && (
          <div className="settings-section">
            <h2>User Profile</h2>
            <p className="section-description">
              Your profile information is used to personalize email summaries and classification.
            </p>

            <div className="form-group">
              <label htmlFor="username">Username</label>
              <input
                id="username"
                type="text"
                className="form-input"
                placeholder="Enter your name"
                value={settings.username}
                onChange={(e) => setSettings({ ...settings, username: e.target.value })}
              />
              <small className="form-hint">This will be used in AI prompts for personalization.</small>
            </div>

            <div className="form-group">
              <label htmlFor="jobContext">Job Role Context</label>
              <textarea
                id="jobContext"
                className="form-textarea"
                placeholder="Describe your job role, responsibilities, and technical focus areas..."
                rows={8}
                value={settings.jobContext}
                onChange={(e) => setSettings({ ...settings, jobContext: e.target.value })}
              />
              <small className="form-hint">
                Include your role title, main responsibilities, technologies you work with, and team focus.
                This helps the AI filter summaries for relevance.
              </small>
            </div>

            <div className="form-group">
              <label htmlFor="newsletterInterests">Newsletter Interests & Topics</label>
              <textarea
                id="newsletterInterests"
                className="form-textarea"
                placeholder="Topics I care about:&#10;- DevOps and CI/CD pipelines&#10;- Azure and cloud infrastructure&#10;- Security best practices&#10;- React and frontend development&#10;- Artificial intelligence and machine learning&#10;&#10;Skip content about:&#10;- HR policies and benefits&#10;- Marketing campaigns&#10;- General company news"
                rows={10}
                value={settings.newsletterInterests}
                onChange={(e) => setSettings({ ...settings, newsletterInterests: e.target.value })}
              />
              <small className="form-hint">
                Define what topics interest you in newsletters. The AI will filter newsletter content to show only what's relevant to your interests.
                List specific technologies, projects, or domains you care about.
              </small>
            </div>
          </div>
        )}

        {activeTab === 'ai' && (
          <div className="settings-section">
            <h2>AI Configuration</h2>
            <p className="section-description">
              Configure your Azure OpenAI connection. These settings override the default backend configuration.
            </p>

            <div className="form-group">
              <label htmlFor="azureEndpoint">Azure OpenAI Endpoint</label>
              <input
                id="azureEndpoint"
                type="text"
                className="form-input"
                placeholder="https://your-resource.openai.azure.com/"
                value={settings.azureOpenAIEndpoint}
                onChange={(e) => setSettings({ ...settings, azureOpenAIEndpoint: e.target.value })}
              />
              <small className="form-hint">
                Your Azure OpenAI service endpoint URL (e.g., https://myservice.openai.azure.com/)
              </small>
            </div>

            <div className="form-group">
              <label htmlFor="azureKey">API Key</label>
              <div className="password-input-wrapper">
                <input
                  id="azureKey"
                  type={showPassword ? 'text' : 'password'}
                  className="form-input"
                  placeholder="Enter your Azure OpenAI API key"
                  value={settings.azureOpenAIKey}
                  onChange={(e) => setSettings({ ...settings, azureOpenAIKey: e.target.value })}
                />
                <button
                  type="button"
                  className="password-toggle"
                  onClick={() => setShowPassword(!showPassword)}
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                >
                  {showPassword ? '👁️' : '👁️‍🗨️'}
                </button>
              </div>
              <small className="form-hint">
                Your Azure OpenAI API key. This is stored locally in your browser.
              </small>
            </div>

            <div className="form-group">
              <label htmlFor="azureDeployment">Deployment Name</label>
              <input
                id="azureDeployment"
                type="text"
                className="form-input"
                placeholder="gpt-4"
                value={settings.azureOpenAIDeployment}
                onChange={(e) => setSettings({ ...settings, azureOpenAIDeployment: e.target.value })}
              />
              <small className="form-hint">
                The name of your deployed model (e.g., gpt-4, gpt-35-turbo)
              </small>
            </div>

            <div className="warning-box">
              <strong>⚠️ Security Notice</strong>
              <p>
                API keys are stored securely on the backend. Only enter these credentials if you want to
                override the default Azure OpenAI configuration.
              </p>
            </div>

            <hr style={{ margin: '32px 0', border: 'none', borderTop: '1px solid #e0e0e0' }} />

            <h3 style={{ marginTop: '24px', marginBottom: '16px' }}>Azure DevOps Integration</h3>
            <p className="section-description">
              Configure Azure DevOps for automatic task creation and assignment.
            </p>

            <div className="form-group">
              <label htmlFor="adoAreaPath">Area Path</label>
              <input
                id="adoAreaPath"
                type="text"
                className="form-input"
                placeholder="ProjectName\\Team\\Area"
                value={settings.adoAreaPath}
                onChange={(e) => setSettings({ ...settings, adoAreaPath: e.target.value })}
              />
              <small className="form-hint">
                The area path where tasks should be created (e.g., MyProject\\Engineering\\Backend)
              </small>
            </div>

            <div className="form-group">
              <label htmlFor="adoPat">Personal Access Token (PAT)</label>
              <div className="password-input-wrapper">
                <input
                  id="adoPat"
                  type={showPassword ? 'text' : 'password'}
                  className="form-input"
                  placeholder="Enter your Azure DevOps PAT"
                  value={settings.adoPat}
                  onChange={(e) => setSettings({ ...settings, adoPat: e.target.value })}
                />
                <button
                  type="button"
                  className="password-toggle"
                  onClick={() => setShowPassword(!showPassword)}
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                >
                  {showPassword ? '👁️' : '👁️‍🗨️'}
                </button>
              </div>
              <small className="form-hint">
                Personal Access Token with work item write permissions. Stored securely on the backend.
              </small>
            </div>
          </div>
        )}

        {activeTab === 'prompts' && (
          <div className="settings-section">
            <h2>Custom Prompts</h2>
            <p className="section-description">
              Customize AI prompts for each email category. Leave blank to use default prompts.
            </p>

            {CATEGORIES.map((category) => (
              <div key={category.id} className="form-group">
                <label htmlFor={`prompt-${category.id}`}>
                  {category.emoji} {category.label}
                </label>
                <textarea
                  id={`prompt-${category.id}`}
                  className="form-textarea"
                  placeholder={`Enter custom prompt for ${category.label} emails...`}
                  rows={4}
                  value={settings.customPrompts[category.id] || ''}
                  onChange={(e) =>
                    setSettings({
                      ...settings,
                      customPrompts: {
                        ...settings.customPrompts,
                        [category.id]: e.target.value,
                      },
                    })
                  }
                />
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Action Buttons */}
      <div className="settings-actions">
        <button className="synthwave-button" onClick={handleSave} disabled={saveStatus === 'saving'}>
          {saveStatus === 'saving' ? '💾 Saving...' : saveStatus === 'saved' ? '✅ Saved!' : '💾 Save Settings'}
        </button>
        <button className="synthwave-button-secondary" onClick={handleReset}>
          🔄 Reset to Defaults
        </button>
        {saveStatus === 'error' && <span className="error-text">❌ Failed to save settings</span>}
      </div>
    </div>
  );
};

export default Settings;
