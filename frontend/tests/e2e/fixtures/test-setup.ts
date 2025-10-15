import { test as base, expect, Page, BrowserContext } from '@playwright/test';

/**
 * Mock email data for testing
 */
export interface MockEmail {
  id: string;
  subject: string;
  sender: string;
  recipient: string;
  body: string;
  received_time: string;
  is_read: boolean;
  categories: string[];
  conversation_id: string;
  category?: string;
}

/**
 * Mock task data for testing
 */
export interface MockTask {
  id: string;
  title: string;
  description: string;
  status: 'pending' | 'in_progress' | 'completed' | 'cancelled';
  priority: 'low' | 'medium' | 'high';
  due_date?: string;
  created_at: string;
  email_id?: string;
}

/**
 * Test fixtures with common setup and utilities
 */
interface TestFixtures {
  // Authenticated page with token
  authenticatedPage: Page;
  
  // Mock email data
  mockEmails: MockEmail[];
  
  // Mock task data
  mockTasks: MockTask[];
  
  // API mocking utilities
  mockEmailAPI: (page: Page, emails: MockEmail[]) => Promise<void>;
  mockTaskAPI: (page: Page, tasks: MockTask[]) => Promise<void>;
  mockAIAPI: (page: Page) => Promise<void>;
  
  // Navigation helpers
  navigateToEmails: (page: Page) => Promise<void>;
  navigateToTasks: (page: Page) => Promise<void>;
  navigateToProcessing: (page: Page) => Promise<void>;
}

/**
 * Generate mock email data
 */
export function generateMockEmails(count: number = 10): MockEmail[] {
  const categories = ['required_personal_action', 'optional_fyi', 'team_discussion', 'task_delegation'];
  const emails: MockEmail[] = [];
  
  for (let i = 1; i <= count; i++) {
    emails.push({
      id: `email-${i}`,
      subject: `Test Email ${i}: ${i % 2 === 0 ? 'Action Required' : 'FYI Update'}`,
      sender: `sender${i}@example.com`,
      recipient: 'user@example.com',
      body: `This is the body of test email ${i}. ${i % 2 === 0 ? 'Please take action.' : 'For your information only.'}`,
      received_time: new Date(Date.now() - i * 3600000).toISOString(),
      is_read: i > 5,
      categories: i % 3 === 0 ? ['Important'] : [],
      conversation_id: `conv-${Math.floor(i / 3)}`,
      category: categories[i % categories.length],
    });
  }
  
  return emails;
}

/**
 * Generate mock task data
 */
export function generateMockTasks(count: number = 5): MockTask[] {
  const tasks: MockTask[] = [];
  const statuses: MockTask['status'][] = ['pending', 'in_progress', 'completed', 'cancelled'];
  const priorities: MockTask['priority'][] = ['low', 'medium', 'high'];
  
  for (let i = 1; i <= count; i++) {
    tasks.push({
      id: `task-${i}`,
      title: `Task ${i}: ${i % 2 === 0 ? 'Complete Report' : 'Review Document'}`,
      description: `This is the description for task ${i}`,
      status: statuses[i % statuses.length],
      priority: priorities[i % priorities.length],
      due_date: new Date(Date.now() + i * 86400000).toISOString(),
      created_at: new Date(Date.now() - i * 3600000).toISOString(),
      email_id: i <= 5 ? `email-${i}` : undefined,
    });
  }
  
  return tasks;
}

/**
 * Mock Email API responses
 */
async function mockEmailAPI(page: Page, emails: MockEmail[]): Promise<void> {
  await page.route('**/api/emails*', async (route) => {
    const url = new URL(route.request().url());
    
    // GET /api/emails - List emails with pagination
    if (route.request().method() === 'GET' && url.pathname === '/api/emails') {
      const page = parseInt(url.searchParams.get('page') || '1');
      const perPage = parseInt(url.searchParams.get('per_page') || '20');
      const start = (page - 1) * perPage;
      const end = start + perPage;
      
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          emails: emails.slice(start, end),
          total: emails.length,
          page,
          per_page: perPage,
          total_pages: Math.ceil(emails.length / perPage),
        }),
      });
    }
    // GET /api/emails/:id - Get single email
    else if (route.request().method() === 'GET' && url.pathname.match(/\/api\/emails\/email-\d+$/)) {
      const id = url.pathname.split('/').pop();
      const email = emails.find((e) => e.id === id);
      
      if (email) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(email),
        });
      } else {
        await route.fulfill({ status: 404, body: 'Email not found' });
      }
    }
    // PATCH /api/emails/:id - Update email
    else if (route.request().method() === 'PATCH') {
      const id = url.pathname.split('/').pop();
      const email = emails.find((e) => e.id === id);
      
      if (email) {
        const updates = await route.request().postDataJSON();
        Object.assign(email, updates);
        
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(email),
        });
      } else {
        await route.fulfill({ status: 404, body: 'Email not found' });
      }
    }
    // POST /api/emails/batch - Batch operations
    else if (route.request().method() === 'POST' && url.pathname.includes('/batch')) {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ success: true, updated: 0 }),
      });
    }
    else {
      await route.continue();
    }
  });
  
  // Mock email stats
  await page.route('**/api/emails/stats*', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        total: emails.length,
        unread: emails.filter((e) => !e.is_read).length,
        by_category: {
          required_personal_action: emails.filter((e) => e.category === 'required_personal_action').length,
          optional_fyi: emails.filter((e) => e.category === 'optional_fyi').length,
          team_discussion: emails.filter((e) => e.category === 'team_discussion').length,
          task_delegation: emails.filter((e) => e.category === 'task_delegation').length,
        },
      }),
    });
  });
}

/**
 * Mock Task API responses
 */
async function mockTaskAPI(page: Page, tasks: MockTask[]): Promise<void> {
  await page.route('**/api/tasks*', async (route) => {
    const url = new URL(route.request().url());
    
    // GET /api/tasks - List tasks
    if (route.request().method() === 'GET' && url.pathname === '/api/tasks') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          tasks,
          total: tasks.length,
          page: 1,
          per_page: 50,
          total_pages: 1,
        }),
      });
    }
    // POST /api/tasks - Create task
    else if (route.request().method() === 'POST' && url.pathname === '/api/tasks') {
      const taskData = await route.request().postDataJSON();
      const newTask: MockTask = {
        id: `task-${Date.now()}`,
        created_at: new Date().toISOString(),
        status: 'pending',
        priority: 'medium',
        ...taskData,
      };
      tasks.push(newTask);
      
      await route.fulfill({
        status: 201,
        contentType: 'application/json',
        body: JSON.stringify(newTask),
      });
    }
    // PATCH /api/tasks/:id - Update task
    else if (route.request().method() === 'PATCH') {
      const id = url.pathname.split('/').pop();
      const task = tasks.find((t) => t.id === id);
      
      if (task) {
        const updates = await route.request().postDataJSON();
        Object.assign(task, updates);
        
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(task),
        });
      } else {
        await route.fulfill({ status: 404, body: 'Task not found' });
      }
    }
    // DELETE /api/tasks/:id - Delete task
    else if (route.request().method() === 'DELETE') {
      const id = url.pathname.split('/').pop();
      const index = tasks.findIndex((t) => t.id === id);
      
      if (index !== -1) {
        tasks.splice(index, 1);
        await route.fulfill({ status: 204 });
      } else {
        await route.fulfill({ status: 404, body: 'Task not found' });
      }
    }
    else {
      await route.continue();
    }
  });
  
  // Mock task stats
  await page.route('**/api/tasks/stats*', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        total: tasks.length,
        by_status: {
          pending: tasks.filter((t) => t.status === 'pending').length,
          in_progress: tasks.filter((t) => t.status === 'in_progress').length,
          completed: tasks.filter((t) => t.status === 'completed').length,
          cancelled: tasks.filter((t) => t.status === 'cancelled').length,
        },
        by_priority: {
          low: tasks.filter((t) => t.priority === 'low').length,
          medium: tasks.filter((t) => t.priority === 'medium').length,
          high: tasks.filter((t) => t.priority === 'high').length,
        },
      }),
    });
  });
}

/**
 * Mock AI API responses
 */
async function mockAIAPI(page: Page): Promise<void> {
  // Mock classification
  await page.route('**/api/ai/classify*', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        category: 'required_personal_action',
        confidence: 0.95,
        reasoning: 'Email requires immediate action',
        alternatives: ['task_delegation', 'team_discussion'],
      }),
    });
  });
  
  // Mock action item extraction
  await page.route('**/api/ai/extract-actions*', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        action_items: [
          {
            action: 'Complete project report',
            deadline: '2024-12-31',
            priority: 'high',
          },
          {
            action: 'Schedule team meeting',
            deadline: '2024-12-25',
            priority: 'medium',
          },
        ],
      }),
    });
  });
  
  // Mock summary generation
  await page.route('**/api/ai/summarize*', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        summary: 'This email contains important action items that require immediate attention.',
        key_points: ['Project deadline approaching', 'Team meeting needed', 'Report submission required'],
      }),
    });
  });
  
  // Mock batch processing
  await page.route('**/api/processing/process-batch*', async (route) => {
    const data = await route.request().postDataJSON();
    const emailIds = data.email_ids || [];
    
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        processed: emailIds.length,
        failed: 0,
        results: emailIds.map((id: string) => ({
          email_id: id,
          category: 'required_personal_action',
          success: true,
        })),
      }),
    });
  });
}

/**
 * Navigation helper - go to emails page
 */
async function navigateToEmails(page: Page): Promise<void> {
  await page.goto('/emails');
  await page.waitForLoadState('networkidle');
}

/**
 * Navigation helper - go to tasks page
 */
async function navigateToTasks(page: Page): Promise<void> {
  await page.goto('/tasks');
  await page.waitForLoadState('networkidle');
}

/**
 * Navigation helper - go to processing page
 */
async function navigateToProcessing(page: Page): Promise<void> {
  await page.goto('/processing');
  await page.waitForLoadState('networkidle');
}

/**
 * Create authenticated page (skip login if not required)
 */
async function createAuthenticatedPage(page: Page): Promise<Page> {
  // Mock health check
  await page.route('**/health*', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        status: 'healthy',
        service: 'email-helper-backend',
        version: '1.0.0',
        provider: 'com',
      }),
    });
  });
  
  // For tests, we can skip authentication by mocking the auth check
  // In real scenarios, you'd set up proper auth tokens
  await page.route('**/auth/me*', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        id: 'test-user-1',
        email: 'test@example.com',
        name: 'Test User',
      }),
    });
  });
  
  return page;
}

/**
 * Extended test fixture with utilities
 */
export const test = base.extend<TestFixtures>({
  authenticatedPage: async ({ page }, use) => {
    const authPage = await createAuthenticatedPage(page);
    await use(authPage);
  },
  
  mockEmails: async ({}, use) => {
    await use(generateMockEmails(15));
  },
  
  mockTasks: async ({}, use) => {
    await use(generateMockTasks(8));
  },
  
  mockEmailAPI: async ({}, use) => {
    await use(mockEmailAPI);
  },
  
  mockTaskAPI: async ({}, use) => {
    await use(mockTaskAPI);
  },
  
  mockAIAPI: async ({}, use) => {
    await use(mockAIAPI);
  },
  
  navigateToEmails: async ({}, use) => {
    await use(navigateToEmails);
  },
  
  navigateToTasks: async ({}, use) => {
    await use(navigateToTasks);
  },
  
  navigateToProcessing: async ({}, use) => {
    await use(navigateToProcessing);
  },
});

export { expect };
