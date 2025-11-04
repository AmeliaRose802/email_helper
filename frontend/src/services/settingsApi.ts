// Settings API service using RTK Query
import { apiSlice } from './api';

export interface UserSettings {
  username?: string;
  job_context?: string;
  newsletter_interests?: string;
  azure_openai_endpoint?: string;
  azure_openai_deployment?: string;
  custom_prompts?: Record<string, string>;
  ado_area_path?: string;
  ado_pat?: string;
}

export interface SettingsResponse {
  success: boolean;
  message: string;
  settings?: UserSettings;
}

// Extend the API slice with settings endpoints
export const settingsApi = apiSlice.injectEndpoints({
  endpoints: (builder) => ({
    getSettings: builder.query<UserSettings, void>({
      query: () => '/api/settings',
      providesTags: ['Settings'],
    }),
    updateSettings: builder.mutation<SettingsResponse, UserSettings>({
      query: (settings) => ({
        url: '/api/settings',
        method: 'PUT',
        body: settings,
      }),
      invalidatesTags: ['Settings'],
    }),
    resetSettings: builder.mutation<SettingsResponse, void>({
      query: () => ({
        url: '/api/settings',
        method: 'DELETE',
      }),
      invalidatesTags: ['Settings'],
    }),
  }),
});

export const {
  useGetSettingsQuery,
  useUpdateSettingsMutation,
  useResetSettingsMutation,
} = settingsApi;
