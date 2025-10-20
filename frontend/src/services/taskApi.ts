// Task management API service for T4 backend integration
import { apiSlice } from './api';
import type {
  Task,
  TaskCreate,
  TaskUpdate,
  TaskFilter,
  TaskListResponse,
  TaskStats,
  PaginationParams,
} from '@/types';

export const taskApi = apiSlice.injectEndpoints({
  endpoints: (builder) => ({
    // Get paginated list of tasks
    getTasks: builder.query<TaskListResponse, PaginationParams & TaskFilter>({
      query: (params) => ({
        url: '/api/tasks',
        params,
      }),
      providesTags: (result) =>
        result?.tasks
          ? [
              ...result.tasks.map(({ id }) => ({ type: 'Task' as const, id })),
              { type: 'Task', id: 'LIST' },
            ]
          : [{ type: 'Task', id: 'LIST' }],
    }),

    // Get individual task by ID
    getTaskById: builder.query<Task, string>({
      query: (id) => `/api/tasks/${id}`,
      providesTags: (_result, _error, id) => [{ type: 'Task', id }],
    }),

    // Create new task
    createTask: builder.mutation<Task, TaskCreate>({
      query: (taskData) => ({
        url: '/api/tasks',
        method: 'POST',
        body: taskData,
      }),
      invalidatesTags: [
        { type: 'Task', id: 'LIST' },
        { type: 'Task', id: 'STATS' },
      ],
    }),

    // Update existing task
    updateTask: builder.mutation<Task, { id: string; data: TaskUpdate }>({
      query: ({ id, data }) => ({
        url: `/api/tasks/${id}`,
        method: 'PUT',
        body: data,
      }),
      invalidatesTags: (_result, _error, { id }) => [
        { type: 'Task', id },
        { type: 'Task', id: 'LIST' },
        { type: 'Task', id: 'STATS' },
      ],
    }),

    // Delete task
    deleteTask: builder.mutation<void, string>({
      query: (id) => ({
        url: `/api/tasks/${id}`,
        method: 'DELETE',
      }),
      invalidatesTags: (_result, _error, id) => [
        { type: 'Task', id },
        { type: 'Task', id: 'LIST' },
        { type: 'Task', id: 'STATS' },
      ],
    }),

    // Get task statistics
    getTaskStats: builder.query<TaskStats, void>({
      query: () => '/api/tasks/stats',
      providesTags: [{ type: 'Task', id: 'STATS' }],
    }),

    // Batch update tasks
    batchUpdateTasks: builder.mutation<
      { success: boolean; updated_count: number; message: string },
      { task_ids: string[]; updates: Partial<TaskUpdate> }
    >({
      query: (data) => ({
        url: '/api/tasks/batch',
        method: 'PUT',
        body: data,
      }),
      invalidatesTags: [
        { type: 'Task', id: 'LIST' },
        { type: 'Task', id: 'STATS' },
      ],
    }),

    // Mark task as completed
    completeTask: builder.mutation<Task, string>({
      query: (id) => ({
        url: `/api/tasks/${id}/complete`,
        method: 'PUT',
      }),
      invalidatesTags: (_result, _error, id) => [
        { type: 'Task', id },
        { type: 'Task', id: 'LIST' },
        { type: 'Task', id: 'STATS' },
      ],
    }),

    // Move task to different status (for drag-and-drop)
    moveTask: builder.mutation<Task, { id: string; status: 'todo' | 'in-progress' | 'review' | 'done' }>({
      query: ({ id, status }) => ({
        url: `/api/tasks/${id}/status?status=${status}`,
        method: 'PUT',
      }),
      // Optimistic update for immediate UI feedback
      onQueryStarted({ id, status }, { dispatch, queryFulfilled }) {
        const patchResult = dispatch(
          taskApi.util.updateQueryData('getTasks', {}, (draft) => {
            const task = draft.tasks.find(t => t.id === id);
            if (task) {
              task.status = status;
            }
          })
        );
        queryFulfilled.catch(patchResult.undo);
      },
      invalidatesTags: (_result, _error, { id }) => [
        { type: 'Task', id },
        { type: 'Task', id: 'LIST' },
        { type: 'Task', id: 'STATS' },
      ],
    }),

    // Create task from email
    createTaskFromEmail: builder.mutation<
      Task,
      {
        email_id: string;
        title: string;
        description?: string;
        priority?: 'high' | 'medium' | 'low';
        due_date?: string;
      }
    >({
      query: (data) => ({
        url: '/api/tasks/from-email',
        method: 'POST',
        body: data,
      }),
      invalidatesTags: [
        { type: 'Task', id: 'LIST' },
        { type: 'Task', id: 'STATS' },
      ],
    }),
  }),
});

export const {
  useGetTasksQuery,
  useGetTaskByIdQuery,
  useCreateTaskMutation,
  useUpdateTaskMutation,
  useDeleteTaskMutation,
  useGetTaskStatsQuery,
  useBatchUpdateTasksMutation,
  useCompleteTaskMutation,
  useMoveTaskMutation,
  useCreateTaskFromEmailMutation,
} = taskApi;
